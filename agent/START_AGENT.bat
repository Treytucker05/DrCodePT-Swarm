@echo off
cd /d "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\agent"

echo =================================================================
echo == DrCodePT-Swarm Agent Console
echo =================================================================

echo.
echo --- CURRENT PLANNER SYSTEM PROMPT (For Cloud Codex ) ---
type planner_system_prompt.txt
echo -----------------------------------------------------------------
echo.
pause

python main.py
pause
