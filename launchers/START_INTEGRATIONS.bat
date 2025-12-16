@echo off
setlocal

rem Launch Codex HTTP wrapper (FastAPI) and ngrok tunnels for both Codex and Obsidian REST API.
rem This keeps windows open so you can see the public URLs ngrok prints.

set BASE=%~dp0
set CODEX_PORT=5051
set OBSIDIAN_PORT=27123
set NGROK_EXE=C:\nvm4w\nodejs\node_modules\ngrok\bin\ngrok.exe
set NGROK_CFG=%LOCALAPPDATA%\\ngrok\\ngrok.yml

echo [INFO] Starting Codex HTTP wrapper on port %CODEX_PORT% ...
start "codex_http" cmd /k "cd /d \"%BASE%\" && python -m uvicorn codex_http_server:app --host 0.0.0.0 --port %CODEX_PORT%"

echo [INFO] Starting ngrok with both tunnels (codex, obsidian) via config %NGROK_CFG% ...
start "ngrok_all" cmd /k "\"%NGROK_EXE%\" start --all --config \"%NGROK_CFG%\""

echo.
echo [NEXT] Wait for ngrok windows to show forwarding URLs, then:
echo   - Codex public URL  : https://<codex-subdomain>.ngrok-free.app/codex/run
echo   - Obsidian public URL: https://<obsidian-subdomain>.ngrok-free.app/ (use /vault/... endpoints)
echo.
echo When done, press any key to exit this launcher (it will NOT close the spawned windows).
pause >nul
endlocal
