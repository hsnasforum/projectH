# Windows Launchers

Windows 바탕화면에서 더블클릭으로 pipeline GUI/TUI를 실행하기 위한 launcher입니다.

## 사용 방법

1. `.cmd` 파일을 **Windows 로컬 폴더**에 복사합니다.
   - 예: `C:\Users\사용자\Desktop\pipeline-gui.cmd`
2. 파일 상단의 두 변수를 자기 환경에 맞게 수정합니다:
   ```cmd
   set "WSL_DISTRO=Ubuntu"
   set "WSL_PROJECT=/home/xpdlqj/code/projectH"
   ```
3. 더블클릭으로 실행합니다.

## 파일

| 파일 | 설명 |
|------|------|
| `pipeline-gui.cmd` | tkinter desktop GUI (WSLg 필요) |
| `pipeline-tui.cmd` | curses 터미널 TUI |

## 요구사항

- Windows 11 + WSL2 + WSLg
- WSL 내부: `python3`, `python3-tk` (GUI용), `tmux`

## 기존 `.bat` 파일과의 차이

repo 루트의 `pipeline-gui.bat`, `pipeline.bat`은 WSL 공유 경로(`\\wsl.localhost\...`)에서
직접 실행될 때 UNC 경고가 뜹니다. 이 `.cmd` 파일은 Windows 로컬에서 실행되므로
UNC 문제가 없고, 사전 검증(WSL, distro, path, python3)도 포함되어 있습니다.

## 문제 해결

- **GUI 창이 안 뜸**: `wsl --update` + `sudo apt install python3-tk`
- **배포판 못 찾음**: `wsl --list`로 확인 후 `WSL_DISTRO` 수정
- **경로 못 찾음**: `WSL_PROJECT` 변수 확인
