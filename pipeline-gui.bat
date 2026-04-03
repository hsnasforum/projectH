@echo off
setlocal

rem Internal desktop GUI launcher entrypoint for projectH.
rem
rem 주의: 이 파일은 WSL 공유 경로(\\wsl.localhost\...)에서 직접 더블클릭하면
rem UNC 경로 경고가 뜹니다. Windows 바탕화면 등에서 실행하려면
rem windows-launchers/pipeline-gui.cmd 를 복사해서 사용하세요.

set "WIN_PATH=%~1"
if not defined WIN_PATH set "WIN_PATH=%~dp0"

where wsl.exe >nul 2>&1
if errorlevel 1 goto :no_wsl

set "WSL_PATH="
if /i "%WIN_PATH:~0,16%"=="\\wsl.localhost\" goto :unc_localhost
if /i "%WIN_PATH:~0,7%"=="\\wsl$\" goto :unc_share

for /f "usebackq delims=" %%I in (`wsl.exe wslpath -a -u "%WIN_PATH%" 2^>nul`) do set "WSL_PATH=%%I"
goto :path_ready

:unc_localhost
set "UNC_REST=%WIN_PATH:~16%"
goto :unc_to_linux

:unc_share
set "UNC_REST=%WIN_PATH:~7%"
goto :unc_to_linux

:unc_to_linux
for /f "tokens=1,* delims=\\" %%A in ("%UNC_REST%") do (
    set "UNC_DISTRO=%%A"
    set "UNC_TAIL=%%B"
)
if defined UNC_TAIL set "WSL_PATH=/%UNC_TAIL:\=/%"

:path_ready
if not defined WSL_PATH goto :bad_path

echo.
echo Pipeline GUI Launcher starting...
echo Project: %WIN_PATH%
echo WSL Path: %WSL_PATH%
echo.

wsl.exe --cd "%WSL_PATH%" --exec python3 pipeline-gui.py "%WSL_PATH%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo GUI exited with code %EXIT_CODE%.
    echo If tkinter is missing, run: wsl -e sudo apt install python3-tk
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
