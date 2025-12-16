@echo off
setlocal
set BASE=%~dp0..

rem Launch desktop MCP + Playwright + Codex CLI (existing)
start "desktop_mcp" cmd /k "cd /d \"%BASE%\\launchers\" && LAUNCH_DESKTOP_AGENT.bat"

rem Launch Obsidian MCP inspector & Codex CLI for Obsidian (optional)
start "obsidian_mcp" cmd /k "cd /d \"%BASE%\\launchers\" && launch_codex_obsidian.bat"

rem Launch Codex HTTP wrapper + dual ngrok tunnels (codex, obsidian REST)
start "integrations" cmd /k "cd /d \"%BASE%\\launchers\" && START_INTEGRATIONS.bat"

echo All launchers started in their own windows. Leave them open.
endlocal
