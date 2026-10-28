@echo off
title K4LI EXE PROTECT — Pull + Build
cd /d "%~dp0"

echo.
echo  ██╗  ██╗ ██╗  ██╗    ██████╗ ██╗   ██╗██╗██╗     ██████╗
echo  ██║ ██╔╝ ██║  ██║    ██╔══██╗██║   ██║██║██║     ██╔══██╗
echo  █████╔╝  ███████║    ██████╔╝██║   ██║██║██║     ██║  ██║
echo  ██╔═██╗  ╚════██║    ██╔══██╗██║   ██║██║██║     ██║  ██║
echo  ██║  ██╗      ██║    ██████╔╝╚██████╔╝██║███████╗██████╔╝
echo  ╚═╝  ╚═╝      ╚═╝    ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═════╝
echo.
echo  [PULL+BUILD]  K4LI EXE PROTECT — Update and Build
echo  --------------------------------------------------------
echo.

:: ── Git pull ──────────────────────────────────────────────────────────────────
echo  [STEP 1] Pulling latest changes from GitHub...
git pull
if %errorlevel% neq 0 (
    echo  [ERROR]  git pull failed. Check internet or repo access.
    pause
    exit /b 1
)
echo  [OK]     Repository updated.
echo.

:: ── Run build ─────────────────────────────────────────────────────────────────
echo  [STEP 2] Starting build...
echo.
call build.bat
