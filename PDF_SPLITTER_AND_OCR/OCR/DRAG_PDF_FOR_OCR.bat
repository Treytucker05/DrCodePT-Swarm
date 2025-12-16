@echo off
setlocal enabledelayedexpansion

REM OCR Textbook PDF - Drag and Drop
REM Converts scanned/image-based PDFs to searchable text

if "%~1"=="" (
    echo.
    echo ========================================
    echo   PDF OCR Tool
    echo ========================================
    echo.
    echo Usage: Drag a PDF file onto this batch file
    echo This will convert image-based PDFs to searchable text PDFs
    echo.
    pause
    exit /b 1
)

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%ocr_textbook.py" "%~1"

pause
exit /b 0
