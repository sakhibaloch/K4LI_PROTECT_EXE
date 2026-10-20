@echo off
title K4LI EXE PROTECT — Build
cd /d "%~dp0"

echo.
echo  ██╗  ██╗ ██╗  ██╗    ██████╗ ██╗   ██╗██╗██╗     ██████╗
echo  ██║ ██╔╝ ██║  ██║    ██╔══██╗██║   ██║██║██║     ██╔══██╗
echo  █████╔╝  ███████║    ██████╔╝██║   ██║██║██║     ██║  ██║
echo  ██╔═██╗  ╚════██║    ██╔══██╗██║   ██║██║██║     ██║  ██║
echo  ██║  ██╗      ██║    ██████╔╝╚██████╔╝██║███████╗██████╔╝
echo  ╚═╝  ╚═╝      ╚═╝    ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═════╝
echo.
echo  [BUILD]  K4LI EXE PROTECT — PyInstaller Release Build
echo  --------------------------------------------------------
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR]  Python is not installed or not in PATH.
    echo           Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo  [OK]     %%v

:: ── Install / upgrade PyInstaller ────────────────────────────────────────────
echo.
echo  [STEP 1] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo  [INFO]   PyInstaller not found — installing...
    pip install pyinstaller --quiet
    if %errorlevel% neq 0 (
        echo  [ERROR]  pip install failed. Check your internet connection.
        pause
        exit /b 1
    )
    echo  [OK]     PyInstaller installed.
) else (
    echo  [OK]     PyInstaller already installed.
)

:: ── Clean previous build ──────────────────────────────────────────────────────
echo.
echo  [STEP 2] Cleaning previous build...
if exist "dist"  rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo  [OK]     Clean done.

:: ── Check icon ────────────────────────────────────────────────────────────────
echo.
echo  [STEP 3] Checking logo.ico...
if exist "logo.ico" (
    echo  [OK]     logo.ico found — will be embedded in EXE.
    set ICON_FLAG=--icon "logo.ico"
    set DATA_FLAG=--add-data "logo.ico;." --add-data "sign.ps1;."
) else (
    echo  [WARN]   logo.ico not found — building without icon.
    set ICON_FLAG=
    set DATA_FLAG=--add-data "sign.ps1;."
)

:: ── Build ─────────────────────────────────────────────────────────────────────
echo.
echo  [STEP 4] Building single EXE (this may take 30-90 seconds)...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "K4LI_EXE_PROTECT" ^
    %ICON_FLAG% ^
    %DATA_FLAG% ^
    --clean ^
    k4li_protect.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR]  Build failed. Check the output above.
    pause
    exit /b 1
)

:: ── Move EXE to root folder ───────────────────────────────────────────────────
echo.
echo  [STEP 5] Copying release EXE to project folder...
if exist "dist\K4LI_EXE_PROTECT.exe" (
    copy /y "dist\K4LI_EXE_PROTECT.exe" "K4LI_EXE_PROTECT.exe" >nul
    echo  [OK]     K4LI_EXE_PROTECT.exe ready in current folder.
) else (
    echo  [WARN]   EXE not found in dist\ — check PyInstaller output.
)

:: ── Self-signed code signing (via sign.ps1 — no Windows SDK needed) ──────────
echo.
echo  [STEP 6] Code signing  (self-signed cert - K4LI Software)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sign.ps1" -ExePath "%~dp0K4LI_EXE_PROTECT.exe"

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  --------------------------------------------------------
echo  [DONE]   Build complete!
echo           EXE : %~dp0K4LI_EXE_PROTECT.exe
echo  --------------------------------------------------------
echo.
pause
