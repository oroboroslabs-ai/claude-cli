@echo off
REM Claude CLI (Oroboros) — NOT Anthropic Claude Code
REM Glass UI + terminal chat: claude-cli  |  UI only: claude-cli --ui-only
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
python -m claude_o_cli.claude_o_cli %*
