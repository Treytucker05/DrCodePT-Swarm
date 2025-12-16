@echo off
REM Start Dr. CodePT RAG Client
setlocal enabledelayedexpansion
cd /d "%~dp0PROGRAMS\drcodept-rag"
if exist venv\Scripts\activate.bat (
  call venv\Scripts\activate.bat
)
python drcodept.py
pause
