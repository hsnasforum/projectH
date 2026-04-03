@echo off
setlocal enabledelayedexpansion

rem ============================================================
rem  Pipeline TUI Launcher — Windows-side entrypoint (curses)
rem ============================================================
rem
rem  이 파일을 Windows 로컬 폴더에 복사해서 더블클릭으로 실행하세요.
rem  GUI 대신 터미널 기반 curses UI가 열립니다.
rem ============================================================

set "WSL_DISTRO=Ubuntu"
set "WSL_PROJECT=/home/xpdlqj/code/projectH"

where wsl.exe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] WSL이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

wsl.exe -d %WSL_DISTRO% -- test -d "%WSL_PROJECT%" 2>nul
if errorlevel 1 (
    echo [ERROR] 프로젝트 경로를 찾을 수 없습니다: %WSL_PROJECT%
    pause
    exit /b 1
)

echo  Pipeline TUI Launcher
echo  Distro:  %WSL_DISTRO%
echo  Project: %WSL_PROJECT%
echo.

wsl.exe -d %WSL_DISTRO% --cd "%WSL_PROJECT%" -- python3 pipeline-launcher.py "%WSL_PROJECT%" --line-mode
if not "%ERRORLEVEL%"=="0" pause
exit /b %ERRORLEVEL%
