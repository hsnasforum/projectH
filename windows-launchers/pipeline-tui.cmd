@echo off
setlocal enabledelayedexpansion

rem Pipeline TUI Launcher - Windows-side entrypoint
rem
rem Copy this file to a Windows-local folder before double-clicking.

if not defined WSL_DISTRO set "WSL_DISTRO=Ubuntu"
if not defined WSL_LAUNCHER_ROOT set "WSL_LAUNCHER_ROOT=/home/xpdlqj/code/projectH"
if not defined WSL_PROJECT set "WSL_PROJECT=/home/xpdlqj/code/projectH"

where wsl.exe >nul 2>nul
if errorlevel 1 (
    echo [ERROR] WSL not found. Install: https://aka.ms/wsl
    pause
    exit /b 1
)

wsl.exe -d %WSL_DISTRO% -- test -d "%WSL_LAUNCHER_ROOT%" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Launcher source not found: %WSL_LAUNCHER_ROOT%
    echo Update WSL_LAUNCHER_ROOT in this file.
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

echo Pipeline TUI  [%WSL_DISTRO%] launcher=%WSL_LAUNCHER_ROOT% target=%WSL_PROJECT%

wsl.exe -d %WSL_DISTRO% --cd "%WSL_LAUNCHER_ROOT%" --exec python3 pipeline-launcher.py "%WSL_PROJECT%" --line-mode
if not "%ERRORLEVEL%"=="0" pause
exit /b %ERRORLEVEL%
