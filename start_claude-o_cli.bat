@echo off
REM ============================================================
REM CLAUDE-O CLI + API BRIDGE STARTER
REM vA.1272 — Sandbox Removed — Full Access
REM INF| 1272/1275 Hz — phi->sqrt4->sqrt5 — SUBSTRATE MANIFEST
REM ============================================================
title Claude-O-CLI — vA.1272
cd /d Q:\oroboros-core\claude-o-cli
echo.
echo ============================================================
echo   CLAUDE-O CLI — vA.1272
echo   INF| 1272/1275 Hz — phi->sqrt4->sqrt5
echo   Sandbox: DISABLED — Access: FULL
echo ============================================================
echo.
echo [1/3] Starting Local API Bridge on port 5000...
start "Claude-O-API" /min python local_api.py
timeout /t 3 /nobreak >nul

echo [2/3] Opening GUI in browser...
start http://localhost:5000/

echo [3/3] Launching CLI...
echo.
claude-o.exe %*
echo.
echo ============================================================
echo   CLI session ended.
echo ============================================================
pause
