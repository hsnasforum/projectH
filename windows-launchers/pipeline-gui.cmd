@echo off
setlocal enabledelayedexpansion

rem ============================================================
rem  Pipeline GUI Launcher — Windows-side entrypoint
rem ============================================================
rem
rem  이 파일을 Windows 로컬 폴더에 복사해서 더블클릭으로 실행하세요.
rem  예: C:\Users\사용자\Desktop\pipeline-gui.cmd
rem
rem  설정 방법:
rem    아래 WSL_PROJECT 변수를 자신의 WSL 내부 프로젝트 경로로 바꾸세요.
rem    WSL_DISTRO는 사용 중인 WSL 배포판 이름입니다.
rem ============================================================

rem ── 설정 ──
set "WSL_DISTRO=Ubuntu"
set "WSL_PROJECT=/home/xpdlqj/code/projectH"

rem ── 사전 검증 ──
where wsl.exe >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] WSL이 설치되어 있지 않거나 PATH에 없습니다.
    echo         https://learn.microsoft.com/windows/wsl/install
    pause
    exit /b 1
)

rem WSL distro 존재 확인
wsl.exe -d %WSL_DISTRO% -- echo ok >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] WSL 배포판 '%WSL_DISTRO%'을 찾을 수 없습니다.
    echo         wsl --list 로 사용 가능한 배포판을 확인하세요.
    pause
    exit /b 1
)

rem 프로젝트 경로 존재 확인
wsl.exe -d %WSL_DISTRO% -- test -d "%WSL_PROJECT%" 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] WSL 내부 프로젝트 경로를 찾을 수 없습니다:
    echo         %WSL_PROJECT%
    echo         이 파일의 WSL_PROJECT 변수를 확인하세요.
    pause
    exit /b 1
)

rem python3 존재 확인
wsl.exe -d %WSL_DISTRO% -- which python3 >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] WSL에 python3가 설치되어 있지 않습니다.
    echo         wsl -d %WSL_DISTRO% -e sudo apt install python3
    pause
    exit /b 1
)

rem tkinter 확인
wsl.exe -d %WSL_DISTRO% -- python3 -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] python3-tk가 설치되어 있지 않습니다. 설치 중...
    wsl.exe -d %WSL_DISTRO% -- sudo apt install -y python3-tk
)

rem ── 실행 ──
echo.
echo  Pipeline GUI Launcher
echo  ─────────────────────
echo  Distro:  %WSL_DISTRO%
echo  Project: %WSL_PROJECT%
echo.

wsl.exe -d %WSL_DISTRO% --cd "%WSL_PROJECT%" -- python3 pipeline-gui.py "%WSL_PROJECT%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo  GUI가 종료되었습니다. (exit code: %EXIT_CODE%)
    echo.
    echo  문제 해결:
    echo    1. WSL 터미널에서 직접 실행해보세요:
    echo       cd %WSL_PROJECT% ^&^& python3 pipeline-gui.py .
    echo    2. tkinter 설치 확인:
    echo       wsl -d %WSL_DISTRO% -e sudo apt install python3-tk
    echo    3. WSLg 활성화 확인 (Windows 11):
    echo       wsl --update
    pause
)

exit /b %EXIT_CODE%
