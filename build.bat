@echo off
echo PDF Toolkit Build Script
echo ------------------------

if not exist venv (
    echo venv directory not found. Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Is Python installed and on PATH?
        pause
        exit /b
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Building main.py...
pyinstaller --onefile --name PDFTool main.py

echo Build completed!
echo Executable is located in the dist\ folder.
pause
