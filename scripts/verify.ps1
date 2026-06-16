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

Push-Location $backend
try {
    Invoke-Checked { & $python -m pytest -q } "Running backend tests"
}
finally {
    Pop-Location
}

Push-Location $frontend
try {
    Invoke-Checked { & $nodeExe node_modules\vitest\vitest.mjs run } "Running frontend unit tests"
    Invoke-Checked { & $nodeExe node_modules\typescript\bin\tsc --noEmit } "Running frontend type check"
    Invoke-Checked { & $nodeExe node_modules\vite\bin\vite.js build } "Running frontend build"
}
finally {
    Pop-Location
}
