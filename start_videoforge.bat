@echo off
setlocal

:: Set the title of the window
title VideoForge Pro Launcher

echo =========================================
echo       Starting VideoForge Pro...
echo =========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.10 or newer from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Check if virtual environment exists, create if it doesn't
if not exist "venv" (
    echo [INFO] First time setup: Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created successfully.
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Check and install dependencies
echo [INFO] Checking dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Launch the application
echo [INFO] Launching the application...
python main.py

:: Deactivate virtual environment when the app closes (optional, as the window usually closes)
deactivate

endlocal
