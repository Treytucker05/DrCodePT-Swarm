@echo off
REM Start the 01 Light server and local client

REM Change to this script's directory (DrCodePT-Swarm root)
cd /d "%~dp0"

REM Go to the 01 software directory
cd "01\software"

REM Use UTF-8 code page to avoid spinner / Unicode issues
chcp 65001 >NUL

REM Run 01 in light mode with the local Python client and local profile
REM If 'poetry' is not on PATH, this will fall back to the full poetry.exe path.
where poetry >NUL 2>&1
if %ERRORLEVEL%==0 (
    poetry run 01 --server light --client light-python --profile local
) else (
    "C:\Users\treyt\AppData\Roaming\Python\Python313\Scripts\poetry.exe" run 01 --server light --client light-python --profile local
)

REM Keep the window open after exit so you can see any errors
pause
