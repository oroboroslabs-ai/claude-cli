# =============================================================
#  Oroboros-Anthropic Claude CLI — installer
#  Local-first agent CLI. Runs your models on Ollama. No cloud key.
# =============================================================
param(
  [string]$InstallDir = "Q:\claude-cli",
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
Write-Host "Oroboros-Anthropic Claude CLI installer" -ForegroundColor Cyan
Write-Host "Target: $InstallDir"

# 1) Node check
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw "Node.js is required but was not found on PATH."
}

# 2) Copy runtime
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path (Join-Path $here '*') -Destination $InstallDir -Recurse -Force

# 3) Build the CLI (unless a prebuilt dist is bundled)
$dist = Join-Path $InstallDir "better-clawd-src\dist\cli.mjs"
if (-not $SkipBuild) {
  if (-not (Test-Path $dist)) {
    if (Get-Command bun -ErrorAction SilentlyContinue) {
      Push-Location (Join-Path $InstallDir "better-clawd-src")
      bun install; bun run build
      Pop-Location
    } else {
      Write-Host "bun not found and no prebuilt dist — install bun or ship dist/cli.mjs." -ForegroundColor Yellow
    }
  }
}

# 4) Put claude-cli on PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$InstallDir*") {
  [Environment]::SetEnvironmentVariable("Path", "$InstallDir;$userPath", "User")
  Write-Host "Added $InstallDir to your PATH." -ForegroundColor Green
}

# 5) Wire local MCP adaptively
if (Test-Path (Join-Path $InstallDir "connect_local_mcp.py")) {
  try { python (Join-Path $InstallDir "connect_local_mcp.py") } catch {}
}

Write-Host ""
Write-Host "Installed. Run:  claude-cli   (or J:\start_claude_cli.bat)" -ForegroundColor Green
Write-Host "Guide: C:\Users\incoguser\Downloads\CLAUDE-CLI-GUIDE\CLAUDE-CLI-GUIDE.md"
