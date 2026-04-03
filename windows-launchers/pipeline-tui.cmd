@echo off
setlocal enabledelayedexpansion

rem Pipeline TUI Launcher - Windows-side entrypoint
rem
rem Copy this file to a Windows-local folder before double-clicking.

set "WSL_DISTRO=Ubuntu"
set "WSL_PROJECT=/home/xpdlqj/code/projectH"

where wsl.exe >nul 2>nul
if errorlevel 1 (
    echo [ERROR] WSL not found. Install: https://aka.ms/wsl
    pause
    exit /b 1
)

wsl.exe -d %WSL_DISTRO% -- test -d "%WSL_PROJECT%" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Project not found: %WSL_PROJECT%
    echo Update WSL_PROJECT in this file.
    pause
    exit /b 1
)

echo Pipeline TUI  [%WSL_DISTRO%] %WSL_PROJECT%

wsl.exe -d %WSL_DISTRO% --cd "%WSL_PROJECT%" --exec python3 pipeline-launcher.py "%WSL_PROJECT%" --line-mode
if not "%ERRORLEVEL%"=="0" pause
exit /b %ERRORLEVEL%
