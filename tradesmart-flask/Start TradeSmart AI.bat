@echo off
REM One-click launcher for TradeSmart AI (Flask + Jinja2 frontend).
REM Double-click this file. First run: sets up a virtual environment and
REM installs dependencies automatically (takes a few minutes, needs
REM internet). Every run after that just starts the app in a few seconds.
REM Leave the black window open while you use the app - closing it stops it.

cd /d "%~dp0"

if not exist venv\Scripts\activate.bat (
    echo.
    echo [TradeSmart AI] First run - setting up a Python virtual environment...
    echo This only happens once and needs an internet connection.
    echo.
    py -3.12 -m venv venv 2>nul
    if not exist venv\Scripts\activate.bat (
        python -m venv venv
    )
    if not exist venv\Scripts\activate.bat (
        echo.
        echo [TradeSmart AI] Could not create a virtual environment.
        echo Make sure Python 3.12 is installed and on your PATH, then try again.
        echo.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo.
    echo [TradeSmart AI] Installing dependencies - this can take a few minutes...
    echo.
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo.
    echo [TradeSmart AI] Setup complete.
    echo.
) else (
    call venv\Scripts\activate.bat
)

if not exist ".env" (
    echo.
    echo [TradeSmart AI] No .env file found here.
    echo Copy .env.example to .env and fill in your SQL Server details
    echo - see README.md. Or just continue: set DB_ENABLED=false in a new
    echo .env to try the app without a database connection.
    echo.
    pause
    exit /b 1
)

echo.
echo [TradeSmart AI] Starting... your browser will open automatically.
echo Leave this window open while you use the app. Close it to stop.
echo.

python app.py

pause
