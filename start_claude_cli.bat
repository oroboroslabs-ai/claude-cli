@echo off
REM ============================================================
REM CLAUDE CLI + API BRIDGE STARTER — HARDENED
REM vA.1272 — ZTA Active — RGE Governing
REM INF| 1272/1275 Hz — phi->sqrt4->sqrt5 — SUBSTRATE MANIFEST
REM ============================================================
title Claude-CLI — vA.1272 — HARDENED
cd /d Q:\oroboros-core\claude-o-cli
echo.
echo ============================================================
echo   CLAUDE CLI — vA.1272 — HARDENED
echo   INF| 1272/1275 Hz — phi->sqrt4->sqrt5
echo   ZTA: ACTIVE — RGE: GOVERNING — Path Whitelist: ON
echo ============================================================
echo.
echo [1/3] Starting Claude CLI glass server on port 5000...
start "Claude-API" /min python run_cli.py
timeout /t 3 /nobreak >nul

echo [2/3] Opening GUI in browser...
start http://localhost:5000/

echo [3/3] Ready.
echo.
echo   GUI:     http://localhost:5000/
echo   Run:     claude-cli  (after pip install -e .)
echo.
pause
