# Claude CLI — Windows install (Oroboros, NOT Anthropic Claude Code)
$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot

Write-Host ""
Write-Host "  Claude CLI — Windows install" -ForegroundColor Cyan
Write-Host "  (Oroboros local Ollama terminal — not Anthropic Claude Code)" -ForegroundColor DarkGray
Write-Host ""

Set-Location $RepoRoot

Write-Host "[1/3] Installing package (pip install -e .)..." -ForegroundColor Yellow
python -m pip install -e . --user
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

$scriptsDir = Join-Path $env:APPDATA "Python\Python313\Scripts"
$exe = Join-Path $scriptsDir "claude-cli.exe"
if (-not (Test-Path $exe)) {
    # Fallback: discover from pip show
    $scriptsDir = python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
    $exe = Join-Path $scriptsDir "claude-cli.exe"
}
if (-not (Test-Path $exe)) { throw "claude-cli.exe not found after install" }

Write-Host "[2/3] Ensuring PATH includes Python Scripts..." -ForegroundColor Yellow
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$scriptsDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$scriptsDir", "User")
    $env:Path = "$env:Path;$scriptsDir"
    Write-Host "  Added: $scriptsDir" -ForegroundColor Green
} else {
    Write-Host "  Already on PATH: $scriptsDir" -ForegroundColor Green
}

Write-Host "[3/3] Adding shim to ~/.local/bin (optional fallback)..." -ForegroundColor Yellow
$localBin = Join-Path $env:USERPROFILE ".local\bin"
New-Item -ItemType Directory -Force -Path $localBin | Out-Null
$shim = Join-Path $localBin "claude-cli.cmd"
@(
    "@echo off",
    "REM Oroboros Claude CLI — NOT Anthropic Claude Code (claude.exe)",
    "`"$exe`" %*"
) | Set-Content -Path $shim -Encoding ASCII
Write-Host "  Shim: $shim" -ForegroundColor Green

Write-Host ""
Write-Host "  Done. Open a NEW PowerShell window, then run:" -ForegroundColor Green
Write-Host "    claude-cli" -ForegroundColor White
Write-Host ""
Write-Host "  Glass UI: http://127.0.0.1:5000" -ForegroundColor DarkGray
Write-Host "  (Do NOT use 'claude' — that is Anthropic Claude Code.)" -ForegroundColor DarkGray
Write-Host ""
