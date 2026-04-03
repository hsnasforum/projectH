# Windows Launchers

WSL 내부의 pipeline을 Windows에서 더블클릭으로 실행하기 위한 launcher 템플릿입니다.

## 사용 방법

1. 이 폴더의 `.cmd` 파일을 **Windows 로컬 폴더**에 복사하세요.
   - 예: `C:\Users\사용자\Desktop\pipeline-gui.cmd`
   - WSL 공유 경로(`\\wsl.localhost\...`)에서 직접 실행하면 안 됩니다.

2. 복사한 파일을 열고, 상단의 설정 변수를 자신의 환경에 맞게 수정하세요:
   ```cmd
   set "WSL_DISTRO=Ubuntu"
   set "WSL_PROJECT=/home/xpdlqj/code/projectH"
   ```

3. 더블클릭으로 실행하세요.

## 파일 설명

| 파일 | 설명 |
|------|------|
| `pipeline-gui.cmd` | tkinter 기반 desktop GUI launcher (WSLg 필요) |
| `pipeline-tui.cmd` | curses 기반 터미널 TUI launcher |

## 요구사항

- Windows 11 + WSL2
- WSLg (GUI용) — `wsl --update`로 활성화
- WSL 내부: `python3`, `python3-tk` (GUI용), `tmux`

## 문제 해결

| 증상 | 해결 |
|------|------|
| "WSL이 설치되어 있지 않습니다" | [WSL 설치](https://learn.microsoft.com/windows/wsl/install) |
| "배포판을 찾을 수 없습니다" | `wsl --list`로 확인 후 `WSL_DISTRO` 수정 |
| "프로젝트 경로를 찾을 수 없습니다" | `WSL_PROJECT` 변수 확인 |
| GUI 창이 안 뜸 | `wsl --update` 후 재시작 (WSLg) |
| tkinter 없음 | `wsl -e sudo apt install python3-tk` |

## 왜 Windows 로컬에 복사해야 하나요?

`cmd.exe`는 UNC 경로(`\\wsl.localhost\...`)를 현재 디렉터리로 지원하지 않습니다.
WSL 공유 경로에서 `.bat`/`.cmd`를 직접 실행하면 현재 디렉터리가 `C:\Windows`로
떨어지고, 경로 변환이 실패합니다. Windows 로컬 파일시스템(C:\, D:\ 등)에서
실행하면 이 문제가 없습니다.
