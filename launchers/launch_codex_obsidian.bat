@echo off
setlocal EnableDelayedExpansion

rem === Config ===
set "VAULT=C:\Users\treyt\OneDrive\Desktop\LifeOS"
set "CONFIG=%USERPROFILE%\.codex\config.toml"
set "LOG=%~dp0launch_codex_obsidian.log"
set "PKG=@mauricio.wolff/mcp-obsidian@0.7.2"
set "INSPECTOR_CMD=npx @modelcontextprotocol/inspector npx ""%PKG%"" ""%VAULT%"""

echo [%date% %time%] launcher started>>"%LOG%"

rem Ensure config exists (copy example if missing)
if not exist "%CONFIG%" (
  powershell -NoLogo -Command "@'
windows_wsl_setup_acknowledged = true
model = \"gpt-5.1-codex-max\"
model_reasoning_effort = \"xhigh\"
sandbox_mode = \"danger-full-access\"
approval_policy = \"never\"
network_access = \"enabled\"

[mcpServers.obsidian]
command = \"npx\"
args = [\"%PKG%\", \"%VAULT%\"]
'@ | Set-Content -Encoding UTF8 \"%CONFIG%\""
  echo [%date% %time%] config created>>"%LOG%"
)

rem Pre-warm package
npx --yes "%PKG%" --version >nul 2>nul

rem Check ports 6277/6274; start inspector if not already listening
set "NEEDINSPECTOR="
for %%P in (6277 6274) do (
  netstat -ano | findstr /c:":%%P " | findstr LISTENING >nul
  if errorlevel 1 set NEEDINSPECTOR=1
)
if defined NEEDINSPECTOR (
  start "" /min cmd /c "%INSPECTOR_CMD%"
  echo [%date% %time%] inspector started>>"%LOG%"
)

rem Wait for ports up (30s)
powershell -NoLogo -Command ^
  "for($i=0;$i -lt 30;$i++){if((Test-NetConnection 127.0.0.1 -Port 6277).TcpTestSucceeded -and (Test-NetConnection 127.0.0.1 -Port 6274).TcpTestSucceeded){exit 0}; Start-Sleep 1}; exit 1"
if errorlevel 1 (
  echo [%date% %time%] warning: inspector ports not confirmed>>"%LOG%"
  echo Warning: inspector ports not confirmed up; continuing...
)

echo Launching Codex CLI (Obsidian MCP enabled) for vault: %VAULT%
echo.
codex --config "%CONFIG%" --search
set EXITCODE=%ERRORLEVEL%
echo [%date% %time%] codex exit %EXITCODE%>>"%LOG%"
echo.
echo Codex exited with code %EXITCODE%.
echo Press any key to close...
pause >nul

endlocal
