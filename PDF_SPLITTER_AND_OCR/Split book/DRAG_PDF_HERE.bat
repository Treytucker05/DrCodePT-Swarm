@echo off
setlocal enabledelayedexpansion

REM Batch wrapper for split_book.py to enable reliable drag-and-drop on Windows
REM Drag a PDF file onto this .bat file to split it into chapters or run OCR

if "%~1"=="" (
    echo.
    echo ========================================
    echo   PDF Splitter - Drag and Drop
    echo ========================================
    echo.
    echo Usage: Drag a PDF file onto this batch file
    echo.
    pause
    exit /b 1
)

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

echo.
echo Choose mode: [S]plit chapters  |  [O]CR searchable (no split)
set /p MODE=Enter S or O (default S): 
if /i "%MODE%"=="O" (
    set MODE_FLAG=--mode ocr
) else (
    set MODE_FLAG=--mode split
)

REM Call the Python script with the dragged file and selected mode
python "%SCRIPT_DIR%split_book.py" %MODE_FLAG% "%~1"

pause
exit /b 0
