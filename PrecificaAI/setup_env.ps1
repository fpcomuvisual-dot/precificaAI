$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PIP_CACHE_DIR = Join-Path $scriptPath ".cache\pip"
$env:HF_HOME = Join-Path $scriptPath ".cache\huggingface"
$env:TORCH_HOME = Join-Path $scriptPath ".cache\torch"
$env:TEMP = Join-Path $scriptPath ".temp"
$env:TMP = Join-Path $scriptPath ".temp"

if (!(Test-Path $env:PIP_CACHE_DIR)) { New-Item -ItemType Directory -Force -Path $env:PIP_CACHE_DIR | Out-Null }
if (!(Test-Path $env:HF_HOME)) { New-Item -ItemType Directory -Force -Path $env:HF_HOME | Out-Null }
if (!(Test-Path $env:TORCH_HOME)) { New-Item -ItemType Directory -Force -Path $env:TORCH_HOME | Out-Null }
if (!(Test-Path $env:TEMP)) { New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null }

Write-Host "✅ Ambiente blindado configurado em $scriptPath"
Write-Host "   PIP_CACHE_DIR: $env:PIP_CACHE_DIR"
Write-Host "   HF_HOME:       $env:HF_HOME"
Write-Host "   TORCH_HOME:    $env:TORCH_HOME"
