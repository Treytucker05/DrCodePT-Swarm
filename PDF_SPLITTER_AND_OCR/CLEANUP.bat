@echo off
setlocal enabledelayedexpansion

REM Cleanup script - removes unnecessary files and folders

cd /d "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PDF_SPLITTER_AND_OCR"

echo Cleaning up unnecessary files...

REM Remove folders
if exist "chapters" (
    rmdir /s /q "chapters"
    echo ✓ Deleted: chapters
)

if exist "Split book\output" (
    rmdir /s /q "Split book\output"
    echo ✓ Deleted: Split book\output
)

if exist "Split book\__pycache__" (
    rmdir /s /q "Split book\__pycache__"
    echo ✓ Deleted: Split book\__pycache__
)

if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo ✓ Deleted: __pycache__
)

REM Remove temporary scripts
if exist "DIAGNOSE_ATLAS.bat" del /f /q "DIAGNOSE_ATLAS.bat" && echo ✓ Deleted: DIAGNOSE_ATLAS.bat
if exist "DIAGNOSE_PDF.bat" del /f /q "DIAGNOSE_PDF.bat" && echo ✓ Deleted: DIAGNOSE_PDF.bat
if exist "diagnose_pdf.py" del /f /q "diagnose_pdf.py" && echo ✓ Deleted: diagnose_pdf.py
if exist "EXTRACT_ATLAS.bat" del /f /q "EXTRACT_ATLAS.bat" && echo ✓ Deleted: EXTRACT_ATLAS.bat
if exist "EXTRACT_ATLAS_SECTIONS.py" del /f /q "EXTRACT_ATLAS_SECTIONS.py" && echo ✓ Deleted: EXTRACT_ATLAS_SECTIONS.py
if exist "MERGE_CHAPTERS.bat" del /f /q "MERGE_CHAPTERS.bat" && echo ✓ Deleted: MERGE_CHAPTERS.bat
if exist "MERGE_CHAPTERS.py" del /f /q "MERGE_CHAPTERS.py" && echo ✓ Deleted: MERGE_CHAPTERS.py
if exist "requirements.txt" del /f /q "requirements.txt" && echo ✓ Deleted: requirements.txt

echo.
echo ✓ Cleanup complete!
echo.
echo Your folder structure is now:
echo   OCR\
echo     - ocr_textbook.py
echo     - DRAG_PDF_FOR_OCR.bat
echo   Split book\
echo     - split_book.py
echo     - DRAG_PDF_HERE.bat
echo.
pause
