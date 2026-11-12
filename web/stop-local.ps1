$ErrorActionPreference = 'Stop'
$workRoot = Join-Path $PSScriptRoot 'work'
foreach ($name in @('website', 'backend')) {
    $recordPath = Join-Path $workRoot ($name + '.process.json')
    if (-not (Test-Path -LiteralPath $recordPath)) { continue }
    $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
    $ownedProcess = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
    if ($ownedProcess -and $ownedProcess.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.started) {
        & taskkill.exe /PID $record.pid /T /F | Out-Null
    }
}
Write-Host '已停止本启动器创建的网页和语音服务。'
