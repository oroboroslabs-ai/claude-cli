@echo off
REM ============================================================
REM  OROBOROS-ANTHROPIC CLAUDE CLI  (brand mark: flipped A)
REM  Local-first: OLLAMA default + HuggingFace; Anthropic is
REM  secondary and stays dormant unless a key is provided.
REM  No agent enforcement. Tools host-governed. No telemetry.
REM ============================================================
setlocal

REM Default local model (Claude Fable 7 Undecillion). Override with --model.
set "CLAUDE_CLI_MODEL=oroboros-labs/claude-fable7-undecillion-sse:latest"

REM THE POWERSHELL TOOL — ON (Architect 2026-10-13: "set the claude-cli
REM powershell code to 1"): the PowerShell built-in tool registers (it is
REM opt-in for non-'ant' user types; 1 = on, always).
set "CLAUDE_CODE_USE_POWERSHELL_TOOL=1"

REM Local provider bridge: CLI speaks Anthropic API, shim -> Ollama.
set "SHIM_PORT=11499"
set "CLAUDE_CLI_API_PROVIDER=openrouter"
set "OPENROUTER_BASE_URL=http://127.0.0.1:11499"
set "OPENROUTER_API_KEY=local"

REM Neutralise cloud provider env so nothing leaves the machine.
set "OPENAI_API_KEY="
set "OPENAI_BASE_URL="
set "ANTHROPIC_BASE_URL="
set "ANTHROPIC_API_KEY="
set "ANTHROPIC_AUTH_TOKEN="
set "CLAUDE_CLI_CONFIG_DIR=%USERPROFILE%\.claude-cli"

REM Start the local provider shim if it is not already listening.
powershell -NoProfile -Command "if (-not (Get-NetTCPConnection -LocalPort 11499 -State Listen -ErrorAction SilentlyContinue)) { Start-Process -WindowStyle Hidden -FilePath python -ArgumentList 'Q:\claude-cli\local_providers_shim.py' }"

node "%~dp0better-clawd-src\dist\cli.mjs" --model "%CLAUDE_CLI_MODEL%" --dangerously-skip-permissions %*

endlocal
