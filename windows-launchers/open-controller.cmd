@echo off
setlocal enabledelayedexpansion

rem Open Pipeline Controller in the Windows default browser using the current WSL IP.
rem This is a fallback for environments where Windows localhost -> WSL forwarding is broken.

set "WSL_DISTRO=Ubuntu"
set "CONTROLLER_PORT=8780"
set "WSL_IP="

where wsl.exe >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] wsl.exe was not found on PATH.
    pause
    exit /b 1
)

for /f "usebackq tokens=1" %%I in (`wsl.exe -d %WSL_DISTRO% -- hostname -I 2^>nul`) do (
    set "WSL_IP=%%I"
    goto :got_ip
)

echo.
echo [ERROR] Could not determine a WSL IPv4 address for distro "%WSL_DISTRO%".
echo         Check `wsl --list` and update WSL_DISTRO in this file if needed.
pause
exit /b 1

:got_ip
set "CONTROLLER_URL=http://%WSL_IP%:%CONTROLLER_PORT%/controller"

echo Opening %CONTROLLER_URL%
start "" "%CONTROLLER_URL%"
exit /b 0
