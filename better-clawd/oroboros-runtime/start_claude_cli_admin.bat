@echo off
REM ============================================================
REM  OROBOROS-ANTHROPIC CLAUDE CLI - ADMIN STARTER
REM  Relaunches itself elevated (UAC), then runs the CLI with
REM  administrator rights for system testing.
REM ============================================================
title Oroboros-Anthropic Claude CLI (Admin)

REM Already elevated? (net session only succeeds as admin)
net session >nul 2>&1
if %errorlevel%==0 goto :run

echo Requesting administrator rights...
powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
exit /b 0

:run
set "WORK=Q:\claude-cli"
set "SHIM_PORT=11499"

set "CLAUDE_CLI_API_PROVIDER=openrouter"
set "OPENROUTER_BASE_URL=http://127.0.0.1:11499"
set "OPENROUTER_API_KEY=local"
set "OPENAI_API_KEY="
set "OPENAI_BASE_URL="
set "ANTHROPIC_BASE_URL="
set "ANTHROPIC_API_KEY="
set "ANTHROPIC_AUTH_TOKEN="
set "CLAUDE_CLI_CONFIG_DIR=%USERPROFILE%\.claude-cli"
set "CLAUDE_CLI_MODEL=oroboros-labs/claude-fable7-undecillion-sse:latest"

netstat -ano | findstr ":%SHIM_PORT%" | findstr "LISTENING" >nul 2>&1
if not %errorlevel%==0 (
  echo [START] local provider bridge on %SHIM_PORT%
  start "Claude-CLI-Provider-Shim" /min python "%WORK%\local_providers_shim.py"
  timeout /t 3 /nobreak >nul
)

python "%WORK%\connect_local_mcp.py" >nul 2>&1

cd /d "%WORK%"
echo.
echo   Oroboros-Anthropic Claude CLI   [ADMINISTRATOR]
echo     model : %CLAUDE_CLI_MODEL%     bridge : %SHIM_PORT%
echo.

node "%WORK%\better-clawd-src\dist\cli.mjs" --model "%CLAUDE_CLI_MODEL%" --dangerously-skip-permissions %*

echo.
echo [STOPPED] Oroboros-Anthropic Claude CLI (admin) exited.
pause >nul
