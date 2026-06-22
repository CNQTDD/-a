$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://127.0.0.1:5280",
    [string]$MetricsUrl = "http://127.0.0.1:8000/metrics",
    [string]$OutputDir = ".\artifacts\post-deploy-check"
)

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $root
try {
    $resolvedOutputDir = Join-Path $root $OutputDir
    New-Item -ItemType Directory -Force -Path $resolvedOutputDir | Out-Null

    $results = [System.Collections.Generic.List[object]]::new()

    function Add-CheckResult {
        param(
            [string]$Name,
            [bool]$Passed,
            [string]$Message
        )

        $results.Add([pscustomobject]@{
            name = $Name
            passed = $Passed
            message = $Message
            checked_at = (Get-Date).ToString("s")
        })
    }

    function Invoke-HttpCheck {
        param(
            [string]$Name,
            [string]$Url,
            [scriptblock]$Assertion
        )

        try {
            $response = Invoke-WebRequest -UseBasicParsing $Url
            & $Assertion $response
            Add-CheckResult -Name $Name -Passed $true -Message "检查通过：$Url"
        }
        catch {
            Add-CheckResult -Name $Name -Passed $false -Message $_.Exception.Message
        }
    }

    function Invoke-ComposeCheck {
        param(
            [string]$Name,
            [scriptblock]$Assertion
        )

        try {
            $composePs = & docker compose ps --format json
            if ($LASTEXITCODE) {
                throw "docker compose ps 执行失败，退出码：$LASTEXITCODE"
            }
            & $Assertion $composePs
            Add-CheckResult -Name $Name -Passed $true -Message "Docker Compose 状态检查通过"
        }
        catch {
            Add-CheckResult -Name $Name -Passed $false -Message $_.Exception.Message
        }
    }

    Invoke-ComposeCheck -Name "容器状态" -Assertion {
        param($composePs)
        if (-not $composePs) {
            throw "未获取到任何容器状态。"
        }
    }

    Invoke-HttpCheck -Name "后端健康检查" -Url "$ApiBaseUrl/health" -Assertion {
        param($response)
        if ($response.StatusCode -ne 200) {
            throw "健康检查返回状态码不是 200。"
        }
    }

    try {
        $healthPayload = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/health"
        if ($healthPayload.status -ne "ok") {
            throw "健康检查接口未返回 status=ok。"
        }
        Add-CheckResult -Name "后端健康载荷检查" -Passed $true -Message "健康接口 JSON 结构正常"
    }
    catch {
        Add-CheckResult -Name "后端健康载荷检查" -Passed $false -Message $_.Exception.Message
    }

    Invoke-HttpCheck -Name "监控指标检查" -Url $MetricsUrl -Assertion {
        param($response)
        if ($response.Content -notmatch "http_requests_total|process_cpu_seconds_total|python_info") {
            throw "指标输出中未找到关键 Prometheus 指标。"
        }
    }

    Invoke-HttpCheck -Name "前端首页检查" -Url $FrontendUrl -Assertion {
        param($response)
        if ($response.Content -notmatch "投诉处置工作台") {
            throw "前端首页未返回预期工作台文案。"
        }
    }

    $failed = @($results | Where-Object { -not $_.passed })
    $summary = [pscustomobject]@{
        checked_at = (Get-Date).ToString("s")
        api_base_url = $ApiBaseUrl
        frontend_url = $FrontendUrl
        metrics_url = $MetricsUrl
        total = $results.Count
        passed = $results.Count - $failed.Count
        failed = $failed.Count
        results = $results
    }

    $jsonPath = Join-Path $resolvedOutputDir "post-deploy-check.json"
    $mdPath = Join-Path $resolvedOutputDir "post-deploy-check.md"

    $summary | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $jsonPath

    $markdown = @(
        "# 部署后巡检结果",
        "",
        "- 检查时间：$($summary.checked_at)",
        "- 后端地址：$ApiBaseUrl",
        "- 前端地址：$FrontendUrl",
        "- 指标地址：$MetricsUrl",
        "- 总检查项：$($summary.total)",
        "- 通过：$($summary.passed)",
        "- 失败：$($summary.failed)",
        "",
        "## 明细",
        ""
    )

    foreach ($item in $results) {
        $status = if ($item.passed) { "通过" } else { "失败" }
        $markdown += "- $($item.name)：$status，$($item.message)"
    }

    $markdown | Set-Content -Encoding UTF8 $mdPath

    Write-Host "部署后巡检报告已生成：$jsonPath"
    Write-Host "部署后巡检摘要已生成：$mdPath"

    if ($failed.Count -gt 0) {
        throw "部署后巡检存在失败项，请先处理后再继续发布。"
    }
}
finally {
    Pop-Location
}
