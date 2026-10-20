@echo off
title K4LI EXE PROTECT
cd /d "%~dp0"
python k4li_protect.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python not found or script crashed.
    echo Make sure Python is installed and in PATH.
    pause
)
