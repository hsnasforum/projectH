@echo off
REM pipeline.bat — Windows에서 더블클릭하여 WSL pipeline launcher를 실행합니다.
REM
REM 사용법:
REM   pipeline.bat                      (기본: 현재 디렉터리)
REM   pipeline.bat C:\path\to\project   (지정 경로)

setlocal

if "%~1"=="" (
    set "WIN_PATH=%~dp0"
) else (
    set "WIN_PATH=%~1"
)

REM Windows 경로를 WSL 경로로 변환
for /f "tokens=*" %%i in ('wsl wslpath -u "%WIN_PATH%"') do set "WSL_PATH=%%i"

echo.
echo  Pipeline Launcher 시작 중...
echo  Project: %WIN_PATH%
echo  WSL Path: %WSL_PATH%
echo.

wsl bash -ic "cd '%WSL_PATH%' && python3 pipeline-launcher.py '%WSL_PATH%'"

endlocal
