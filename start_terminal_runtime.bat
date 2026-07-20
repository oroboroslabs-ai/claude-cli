@echo off
REM ============================================================
REM CLAUDE-CLI — TERMINAL RUNTIME (tools + MCP + agentic loop)
REM vA.1272 — Level 6 — NO SANDBOX — Crown 1272 Hz
REM Launch from src/ so root claude_o_cli.py cannot shadow the package.
REM ============================================================
title Claude-CLI Terminal Runtime — L6
set "CLI_ROOT=Q:\oroboros-core\claude-o-cli"
cd /d "%CLI_ROOT%\src"

set "PYTHONPATH=%CLI_ROOT%\src;%CLI_ROOT%"
set "OLLAMA_MODEL=claude-7:latest"
set "OLLAMA_URL=http://localhost:11434"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo.
echo ============================================================
echo   CLAUDE-CLI TERMINAL RUNTIME - Level 6
echo   Tools + MCP + Agentic Loop linked to chat
echo   Model: %OLLAMA_MODEL%
echo   Crown 1272 Hz - Mao Haki - Sandbox OFF
echo ============================================================
echo.

if exist "J:\anthropic-local-chat\start-mcp-lab.ps1" (
  echo [1/2] Probing MCP lab...
  start "MCP-Lab" /min powershell -NoProfile -ExecutionPolicy Bypass -File "J:\anthropic-local-chat\start-mcp-lab.ps1"
) else (
  echo [1/2] MCP lab script not found - skipping
)

echo [2/2] Starting terminal chat with runtime engine...
echo   Commands: /runtime  /mcp  /tools  /loop  /perceive  /haki
echo.

python -m claude_o_cli.claude_o_cli chat
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  echo.
  echo [X] Launch failed ^(exit %ERR%^). Trying direct entry...
  python -c "import sys; sys.path.insert(0, r'%CLI_ROOT%\src'); sys.path.insert(1, r'%CLI_ROOT%'); from claude_o_cli.claude_o_cli import main; sys.argv=['claude-cli','chat']; main()"
  set "ERR=%ERRORLEVEL%"
)
if not "%ERR%"=="0" (
  echo.
  echo [X] Still failed. Check: python on PATH, package at %CLI_ROOT%\src\claude_o_cli
  pause
)
exit /b %ERR%
