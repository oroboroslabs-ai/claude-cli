@echo off
REM ============================================================
REM  OROBOROS-ANTHROPIC CLAUDE CLI  -  official starter (J:\ root)
REM  Starts ONLY our CLI. No Anthropic services, no telemetry.
REM  Local body: Ollama (+ HuggingFace). Anthropic stays dormant.
REM ============================================================
title Oroboros-Anthropic Claude CLI
setlocal

set "WORK=Q:\claude-cli"
set "SHIM_PORT=11499"

REM Local-first environment: nothing leaves the machine.
set "CLAUDE_CLI_API_PROVIDER=openrouter"
set "OPENROUTER_BASE_URL=http://127.0.0.1:11499"
set "OPENROUTER_API_KEY=local"
set "OPENAI_API_KEY="
set "OPENAI_BASE_URL="
set "ANTHROPIC_BASE_URL="
set "ANTHROPIC_API_KEY="
set "ANTHROPIC_AUTH_TOKEN="
set "CLAUDE_CODE_USE_BEDROCK="
set "CLAUDE_CODE_USE_VERTEX="
set "CLAUDE_CLI_CONFIG_DIR=%USERPROFILE%\.claude-cli"
set "CLAUDE_CLI_MODEL=oroboros-labs/claude-fable7-undecillion-sse:latest"

REM Start our local provider bridge (CLI speaks Anthropic API -> Ollama).
netstat -ano | findstr ":%SHIM_PORT%" | findstr "LISTENING" >nul 2>&1
if not %errorlevel%==0 (
  echo [START] local provider bridge on %SHIM_PORT%
  start "Claude-CLI-Provider-Shim" /min python "%WORK%\local_providers_shim.py"
  timeout /t 3 /nobreak >nul
)

REM Adaptive connect: wire whatever local MCP services are present right now.
REM (Run `python Q:\claude-cli\connect_local_mcp.py --remote` once to also note
REM  the cloud fallback; local is the default and needs no key.)
python "%WORK%\connect_local_mcp.py" >nul 2>&1

cd /d "%WORK%"
echo.
echo   Oroboros-Anthropic Claude CLI
echo     command : claude-cli
echo     body    : Ollama (local)    bridge : %SHIM_PORT%
echo     model   : %CLAUDE_CLI_MODEL%
echo     anthropic : dormant (no key)   agent enforcement : off
echo.

node "%WORK%\better-clawd-src\dist\cli.mjs" --model "%CLAUDE_CLI_MODEL%" --dangerously-skip-permissions %*

echo.
echo [STOPPED] Oroboros-Anthropic Claude CLI exited.
pause >nul
endlocal
