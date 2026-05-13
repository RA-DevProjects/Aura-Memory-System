@echo off
:: Navigate to the folder where the bat is located
cd /d "%~dp0"
echo Starting Aura Memory System...
echo.
:: Run the script and keep the window open if it crashes
python soul.py
if %errorlevel% neq 0 (
    echo.
    echo [CRASH] Something went wrong. 
    echo Check if you installed the library: pip install ollama
)
pause