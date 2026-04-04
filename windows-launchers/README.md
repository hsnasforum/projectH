# Windows Launchers

Windows에서 pipeline GUI를 실행하는 두 가지 방법을 제공합니다.

대상 repo는 `projectH` 자체일 필요가 없습니다.
`AGENTS.md`가 있는 임의의 WSL 내부 repo를 target으로 지정할 수 있습니다.
launcher는 target repo에 `.pipeline/`, `work/`, `verify/`가 없으면 자동 bootstrap합니다.

## 방법 1: `.cmd` launcher (권장 — 설치 불필요)

1. `.cmd` 파일을 **Windows 로컬 폴더**에 복사합니다.
   - 예: `C:\Users\사용자\Desktop\pipeline-gui.cmd`
2. 파일 상단의 두 변수를 자기 환경에 맞게 수정합니다:
   ```cmd
   set "WSL_DISTRO=Ubuntu"
   set "WSL_PROJECT=/home/xpdlqj/code/finance"
   ```
3. 더블클릭으로 실행합니다.

## 방법 2: `.exe` (GUI 내부에서 경로 설정)

1. `dist/pipeline-gui.exe`를 Windows 로컬 경로에 복사합니다.
2. 더블클릭으로 실행합니다.
3. GUI 안에서 **Browse…** 또는 **Recent** quick-select로 WSL project 경로를 선택합니다.
4. **Apply** 버튼으로 적용합니다.
5. **Setup/Check** 버튼으로 실행 전제를 확인합니다.
6. **Start** 버튼으로 pipeline을 시작합니다.

마지막 성공 경로는 `~/.pipeline-gui-last-project`에 저장되어 다음 실행 시 자동 복원됩니다.
최근 5개 경로를 기억하며 quick-select 버튼으로 전환할 수 있습니다.

exe 빌드 방법은 `scripts/PACKAGING.md`를 참고하세요.

## 파일

| 파일 | 설명 |
|------|------|
| `pipeline-gui.cmd` | tkinter desktop GUI (`.cmd` 방식, WSLg 필요) |
| `pipeline-tui.cmd` | curses 터미널 TUI |
| `dist/pipeline-gui.exe` | Windows native exe (빌드 후 생성) |

## 요구사항

- Windows 11 + WSL2 + WSLg
- WSL 내부: `python3`, `python3-tk` (GUI용), `tmux`
- Agent CLI: `claude`, `codex`, `gemini` (npm global install, nvm으로 Node 20+ 권장)
- Target repo: WSL 내부 git clone, `AGENTS.md` 필수

## `.cmd` vs `.exe` 비교

| 항목 | `.cmd` | `.exe` |
|------|--------|--------|
| 설치 | 없음 (텍스트 파일 복사) | PyInstaller 빌드 필요 |
| Python 필요 | WSL 내부 python3 | exe에 번들됨 |
| project path | `.cmd` 파일 안에서 하드코딩 | GUI 내 Browse…/Apply/Recent |
| 경로 저장 | 없음 (매번 `.cmd` 수정) | 최근 5개 자동 저장 |
| multi-project | `.cmd` 파일 복사해서 각각 설정 | GUI에서 전환 가능 |
| Setup/Check | 없음 | 실행 전제 자동 확인 + 설치 제안 |
| WSL 의존성 | 동일 | 동일 |

## project-aware session

각 target repo는 독립 tmux session으로 실행됩니다:

| repo | session |
|------|---------|
| `/home/user/code/projectH` | `aip-projectH` |
| `/home/user/code/finance` | `aip-finance` |

Stop은 해당 project session만 종료하며, 다른 project에 영향을 주지 않습니다.

## 문제 해결

- **GUI 창이 안 뜸**: `wsl --update` + `sudo apt install python3-tk`
- **배포판 못 찾음**: `wsl --list`로 확인 후 `WSL_DISTRO` 수정
- **경로 못 찾음**: `.cmd`의 `WSL_PROJECT` 확인 또는 exe에서 Browse… 재선택
- **Setup: Missing ...**: Setup/Check에서 설치 제안을 수락하거나 수동 설치 후 재확인
- **Gemini pane dead**: Node 18에서는 Gemini CLI가 실행 안 됨 — `nvm install 22 && nvm alias default 22`
- **agent 상태 OFF/BOOTING 고정**: tmux 세션이 없거나 pane capture 실패 — Start로 pipeline 재기동
- **legacy `ai-pipeline` 세션**: `tmux kill-session -t ai-pipeline`으로 정리
