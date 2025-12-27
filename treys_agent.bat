@echo off
cd /d C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm
pip install -r requirements.txt --break-system-packages --quiet
python agent/treys_agent.py %*
pause
