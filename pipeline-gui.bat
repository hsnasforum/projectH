@echo off
setlocal

rem pipeline-gui.bat — Windows에서 더블클릭하여 WSL pipeline GUI launcher를 실행합니다.
rem WSLg 필요 (Windows 11 WSL2)

set "WIN_PATH=%~1"
if not defined WIN_PATH set "WIN_PATH=%~dp0"

where wsl.exe >nul 2>&1
if errorlevel 1 goto :no_wsl

set "WSL_PATH="
for /f "usebackq delims=" %%I in (`wsl.exe wslpath -a -u "%WIN_PATH%" 2^>nul`) do set "WSL_PATH=%%I"
if not defined WSL_PATH goto :bad_path

echo.
echo Pipeline GUI Launcher starting...
echo Project: %WIN_PATH%
echo WSL Path: %WSL_PATH%
echo.

wsl.exe --cd "%WSL_PATH%" -- python3 pipeline-gui.py "%WSL_PATH%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo GUI exited with code %EXIT_CODE%.
    echo tkinter가 없다면: wsl -e sudo apt install python3-tk
    pause
)

exit /b %EXIT_CODE%

:no_wsl
echo.
echo WSL is not installed or not available on PATH.
pause
exit /b 1

:bad_path
echo.
echo Failed to convert the selected path to a WSL path.
echo Input: %WIN_PATH%
pause
exit /b 1
