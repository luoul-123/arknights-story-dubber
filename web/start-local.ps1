param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$webRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent $webRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$nodePath = (Get-Command node -ErrorAction Stop).Source
$workRoot = Join-Path $webRoot 'work'
New-Item -ItemType Directory -Path $workRoot -Force | Out-Null
if (-not (Test-Path -LiteralPath $pythonPath)) { throw '找不到项目 Python，请先安装项目依赖。' }
if (-not (Test-Path -LiteralPath (Join-Path $webRoot 'node_modules'))) { throw '请先在 web 目录运行 npm ci。' }
$configPath = Join-Path $webRoot '.dev.vars'
if (-not (Test-Path -LiteralPath $configPath)) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    $token = [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant()
    $config = "VOICE_BACKEND_URL=http://127.0.0.1:9881" + [Environment]::NewLine + "VOICE_BACKEND_TOKEN=$token" + [Environment]::NewLine + "STUDIO_ADMIN_USER_ID=local_seedy" + [Environment]::NewLine
    [IO.File]::WriteAllText($configPath, $config, (New-Object Text.UTF8Encoding $false))
}
function Test-Port($port) {
    $client = New-Object Net.Sockets.TcpClient
    try { $client.Connect('127.0.0.1', $port); return $true } catch { return $false } finally { $client.Dispose() }
}
if (-not (Test-Port 9881)) {
    $process = Start-Process -FilePath $pythonPath -ArgumentList @('backend/run_local.py') -WorkingDirectory $webRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $workRoot 'backend.stdout.log') -RedirectStandardError (Join-Path $workRoot 'backend.stderr.log')
    @{ pid=$process.Id; started=$process.StartTime.ToUniversalTime().Ticks.ToString() } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $workRoot 'backend.process.json')
}
if (-not (Test-Port 5173)) {
    $process = Start-Process -FilePath $nodePath -ArgumentList @('scripts/run-framework.mjs', 'dev', '--port', '5173') -WorkingDirectory $webRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $workRoot 'website.stdout.log') -RedirectStandardError (Join-Path $workRoot 'website.stderr.log')
    @{ pid=$process.Id; started=$process.StartTime.ToUniversalTime().Ticks.ToString() } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $workRoot 'website.process.json')
}
$ready = $false
for ($i=0; $i -lt 45; $i++) {
    try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:5173/api/voice/status' -UseBasicParsing -TimeoutSec 2; if ($response.StatusCode -eq 200) { $ready=$true; break } } catch {}
    Start-Sleep -Seconds 1
}
if (-not $ready) { throw '网页启动超时，请查看 web/work 中的日志。' }
Write-Host '泰拉之声网页版已启动：http://127.0.0.1:5173/'
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:5173/signin-with-chatgpt?return_to=/' }
