@echo off
setlocal enabledelayedexpansion

rem Pipeline GUI Launcher - Windows-side entrypoint
rem
rem Copy this file to a Windows-local folder before double-clicking.
rem Example: C:\Users\<you>\Desktop\pipeline-gui.cmd
rem
rem Edit these values for your environment.

if not defined WSL_DISTRO set "WSL_DISTRO=Ubuntu"
if not defined WSL_LAUNCHER_ROOT set "WSL_LAUNCHER_ROOT=/home/xpdlqj/code/projectH"
if not defined WSL_PROJECT set "WSL_PROJECT=/home/xpdlqj/code/projectH"

where wsl.exe >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] WSL is not installed or not available on PATH.
    echo         https://learn.microsoft.com/windows/wsl/install
    pause
    exit /b 1
)

wsl.exe -d %WSL_DISTRO% -- echo ok >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] WSL distro "%WSL_DISTRO%" was not found.
    echo         Run: wsl --list
    pause
    exit /b 1
)

wsl.exe -d %WSL_DISTRO% -- test -d "%WSL_LAUNCHER_ROOT%" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] WSL launcher source path was not found:
    echo         %WSL_LAUNCHER_ROOT%
    echo         Update WSL_LAUNCHER_ROOT in this file.
    pause
    exit /b 1
)

wsl.exe -d %WSL_DISTRO% -- test -d "%WSL_PROJECT%" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] WSL project path was not found:
    echo         %WSL_PROJECT%
    echo         Update WSL_PROJECT in this file.
    pause
    exit /b 1
)

wsl.exe -d %WSL_DISTRO% -- which python3 >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] python3 is not installed in WSL.
    echo         Run: wsl -d %WSL_DISTRO% -e sudo apt install python3
    pause
    exit /b 1
)

echo Pipeline GUI  [%WSL_DISTRO%] launcher=%WSL_LAUNCHER_ROOT% target=%WSL_PROJECT%

wsl.exe -d %WSL_DISTRO% --cd "%WSL_LAUNCHER_ROOT%" --exec python3 pipeline-gui.py "%WSL_PROJECT%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo GUI exited [code %EXIT_CODE%].
    echo If the window didn't appear, check tkinter and WSLg:
    echo   wsl -d %WSL_DISTRO% -e sudo apt install python3-tk
    echo   wsl --update
    pause
)

exit /b %EXIT_CODE%
