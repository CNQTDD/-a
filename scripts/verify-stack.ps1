$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $root ".venv-codex\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = Join-Path $root ".venv\Scripts\python.exe"
}
$nodeExe = "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if (-not (Test-Path $nodeExe)) {
    $nodeExe = (Get-Command node.exe).Source
}
$npmCmd = Join-Path (Split-Path $nodeExe) "npm.cmd"
if (-not (Test-Path $npmCmd)) {
    $npmCmd = "npm.cmd"
}

$env:DOCKER_CONFIG = Join-Path $env:TEMP "docker-config-codex"
New-Item -ItemType Directory -Force -Path $env:DOCKER_CONFIG | Out-Null

$artifactRoot = Join-Path $root "artifacts\stack-verification"
$logDir = Join-Path $artifactRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$previewProcess = $null

function Invoke-Checked {
    param(
        [scriptblock]$Command,
        [string]$Label
    )

    Write-Host $Label
    & $Command
    if ($LASTEXITCODE) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

$playwrightConfig = Join-Path $frontend "playwright.stack.config.ts"

Push-Location $root
try {
    Push-Location $frontend
    try {
        $previousViteBaseUrl = $env:VITE_API_BASE_URL
        $env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
        Invoke-Checked {
            & $nodeExe node_modules\vite\bin\vite.js build
        } "Building frontend dist"
    }
    finally {
        if ($null -eq $previousViteBaseUrl) {
            Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
        }
        else {
            $env:VITE_API_BASE_URL = $previousViteBaseUrl
        }
        Pop-Location
    }

    Invoke-Checked {
        & docker compose build api model-stub frontend
    } "Building compose images"

    Invoke-Checked {
        & docker compose --profile development up -d --wait --no-build --force-recreate api frontend model-stub mysql redis etcd minio milvus elasticsearch prometheus
    } "Starting compose stack"

    Invoke-Checked {
        & docker compose exec -T api alembic upgrade head
    } "Running migrations"

    Invoke-Checked {
        & docker compose exec -T api python scripts/seed_sample_knowledge.py `
            --database-url mysql+pymysql://suzhida:suzhida@mysql:3306/suzhida `
            --elasticsearch-url http://elasticsearch:9200 `
            --milvus-uri http://milvus:19530
    } "Seeding sample knowledge"

    Push-Location $backend
    try {
        $env:RUN_INFRA_TESTS = "1"
        Invoke-Checked { & $python -m pytest tests/contract -v } "Running infrastructure contracts"
        Invoke-Checked { & $python -m pytest tests/integration/test_end_to_end_complaint.py -v } "Running backend e2e"
    }
    finally {
        Remove-Item Env:RUN_INFRA_TESTS -ErrorAction SilentlyContinue
        Pop-Location
    }

    $previewProcess = Start-Process -WindowStyle Hidden -PassThru -FilePath $nodeExe -WorkingDirectory $frontend -ArgumentList @(
        "node_modules\vite\bin\vite.js",
        "preview",
        "--host",
        "127.0.0.1",
        "--port",
        "5299",
        "--strictPort"
    )
    $previewReady = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5299" | Out-Null
            $previewReady = $true
            break
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $previewReady) {
        throw "Frontend preview server did not become ready on http://127.0.0.1:5299"
    }

    Push-Location $frontend
    try {
        Invoke-Checked {
            & $nodeExe node_modules\playwright\cli.js test --config $playwrightConfig ./tests/e2e/degraded-flow.spec.ts
        } "Running frontend e2e"
    }
    finally {
        Pop-Location
    }

    Push-Location $backend
    try {
        $loadHostOutput = Join-Path $backend "artifacts\performance"
        New-Item -ItemType Directory -Force -Path $loadHostOutput | Out-Null
        $apiContainerId = (& docker compose ps -q api).Trim()
        if (-not $apiContainerId) {
            throw "API container is not available for the load test."
        }
        Invoke-Checked {
            & docker compose exec -T api python tests/performance/run_load.py --base-url http://127.0.0.1:8000 --concurrency 50 --requests 500 --output /tmp/performance
        } "Running load test"
        & docker cp "${apiContainerId}:/tmp/performance" $loadHostOutput
        if ($LASTEXITCODE) {
            throw "Copying load test artifacts failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($previewProcess -ne $null -and -not $previewProcess.HasExited) {
        Stop-Process -Id $previewProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Push-Location $root
    try {
        & docker compose logs --no-color | Set-Content -Encoding UTF8 (Join-Path $logDir "compose.log")
        & docker compose ps | Set-Content -Encoding UTF8 (Join-Path $logDir "ps.log")
    }
    finally {
        Pop-Location
    }

    Push-Location $root
    try {
        & docker compose down --remove-orphans
    }
    finally {
        Pop-Location
    }
}
