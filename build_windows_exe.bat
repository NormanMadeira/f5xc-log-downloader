@echo off
setlocal enabledelayedexpansion
title F5 XC Log Downloader - Build EXE (V1.0)
cd /d "%~dp0"

echo ============================================
echo  F5 XC Log Downloader - Windows EXE Builder
echo ============================================
echo.

rem --- Pick a Python launcher: prefer the "py" launcher, fall back to "python" ---
set "PYCMD="
py --version >nul 2>&1
if not errorlevel 1 set "PYCMD=py"
if not defined PYCMD (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYCMD=python"
)
if not defined PYCMD (
    echo [ERROR] Could not find Python. Install Python 3.9+ from python.org
    echo         and make sure "Add python.exe to PATH" is checked during setup.
    pause
    exit /b 1
)
echo Using Python launcher: %PYCMD%
%PYCMD% --version

echo.
echo Installing/updating dependencies (flask, requests, pyinstaller)...
%PYCMD% -m pip install --upgrade pip >nul
%PYCMD% -m pip install flask requests pyinstaller
if errorlevel 1 (
    echo [ERROR] pip install failed. Check your internet connection / proxy settings.
    pause
    exit /b 1
)

echo.
echo Building standalone EXE with PyInstaller...
%PYCMD% -m PyInstaller --clean --noconfirm --onefile --name F5XC-Log-Downloader f5xc_log_downloader.py
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed. See the output above for details.
    pause
    exit /b 1
)

echo.
echo Preparing a clean folder to share...
if not exist "release" mkdir "release"
copy /y "dist\F5XC-Log-Downloader.exe" "release\F5XC-Log-Downloader.exe" >nul
if exist "README_V5_1.txt" copy /y "README_V5_1.txt" "release\README.txt" >nul

echo.
echo ============================================
echo  BUILD COMPLETE
echo  EXE ready to share: %CD%\release\F5XC-Log-Downloader.exe
echo.
echo  Note: some antivirus/Windows Defender SmartScreen may flag a
echo  freshly built PyInstaller EXE as "unrecognized" on first run.
echo  This is a common false positive for onefile PyInstaller builds
echo  from a new/unsigned publisher, not a sign of malware. Recipients
echo  may need to click "More info" -> "Run anyway", or you can
echo  code-sign the EXE if you distribute it broadly.
echo ============================================
echo.
pause
