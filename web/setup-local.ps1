param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$webRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent $webRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$dataRoot = Join-Path $webRoot '.voice-data'
$voiceArchive = Join-Path $webRoot 'work\voice-of-terra-voices.zip'
$voiceUrl = 'https://github.com/luoul-123/arknights-story-dubber/releases/latest/download/voice-of-terra-voices.zip'

if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw '请先安装 Node.js 22.13 或更新版本：https://nodejs.org/' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw '找不到 npm，请重新安装 Node.js。' }
if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) { throw '完整配音需要 NVIDIA GPU 与驱动。请先在这台电脑安装显卡驱动。' }
if (-not (Test-Path -LiteralPath $pythonPath)) {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw '请先安装 Python 3.11 并勾选 py launcher：https://www.python.org/downloads/' }
    & py -3.11 -m venv (Join-Path $projectRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw '无法创建 Python 3.11 虚拟环境。' }
}
& $pythonPath -m pip install -r (Join-Path $projectRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python 依赖安装失败。' }
Push-Location $webRoot
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw '网页依赖安装失败。' }
} finally { Pop-Location }

if (-not (Test-Path -LiteralPath (Join-Path $dataRoot 'characters.json'))) {
    New-Item -ItemType Directory -Path (Split-Path $voiceArchive) -Force | Out-Null
    Write-Host '正在下载五套音色，约 1.2 GB。'
    & curl.exe --fail --location --retry 3 --output $voiceArchive $voiceUrl
    if ($LASTEXITCODE -ne 0) { throw '音色包尚未发布或下载失败，请到 GitHub Releases 检查。' }
    New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
    Expand-Archive -LiteralPath $voiceArchive -DestinationPath $dataRoot -Force
    & $pythonPath (Join-Path $webRoot 'backend\relocate_voice_data.py') $dataRoot
    if ($LASTEXITCODE -ne 0) { throw '音色包校验失败。' }
}

Write-Host '安装 GPU 语音引擎。首次下载需要数 GB，可能较久。'
& $pythonPath (Join-Path $webRoot 'backend\setup_engine.py')
if ($LASTEXITCODE -ne 0) { throw '语音引擎安装失败。' }
& (Join-Path $webRoot 'start-local.ps1') -NoBrowser:$NoBrowser
