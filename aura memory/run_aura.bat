@echo off

cd /d "%~dp0"
echo Starting Aura Memory System...
echo.

python soul.py
if %errorlevel% neq 0 (
    echo.
    echo [CRASH] Something went wrong. 
    echo Check if you installed the library: pip install ollama
)
pause
