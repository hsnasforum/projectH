# Pipeline GUI exe 패키징 가이드

## exe가 의미하는 것

`pipeline-gui.exe`는 **독립 실행형 앱이 아닙니다.**

현재 구조에서 exe의 역할:
```
[Windows]                         [WSL]
pipeline-gui.exe ──wsl.exe──→ tmux / watcher / agent CLIs
(frontend wrapper)                (backend runtime)
```

exe는 `wsl.exe`를 통해 WSL 내부의 tmux/watcher/agent CLI를 제어하고 상태를 읽는 **Windows-side GUI wrapper**입니다. 백엔드(tmux, watcher, CLI)는 WSL 안에 있어야 합니다.

## 포함/비포함 경계

| 항목 | exe에 포함 | 외부 전제 |
|------|-----------|----------|
| `pipeline-gui.py` 로직 | ✅ | |
| tkinter GUI | ✅ | |
| tmux 호출 코드 | ✅ | |
| Python runtime | ✅ (PyInstaller 번들) | |
| WSL2 + WSLg | | ✅ Windows 11 필요 |
| python3-tk (WSL) | | ✅ `sudo apt install` |
| tmux (WSL) | | ✅ `sudo apt install` |
| Claude/Codex/Gemini CLI | | ✅ npm global install |
| projectH repo | | ✅ WSL 내부 clone |
| `start-pipeline.sh` | | ✅ repo 안에 포함 |
| `watcher_core.py` | | ✅ repo 안에 포함 |

## 패키징 절차

### 방법 A: Windows Python으로 빌드 (권장 — native .exe)

```powershell
# Windows PowerShell에서
pip install pyinstaller
pyinstaller --onefile --noconsole --name pipeline-gui pipeline-gui.py
# → dist\pipeline-gui.exe
```

이 방법이 진짜 Windows native exe를 만듭니다.
`pipeline-gui.py`는 `sys.platform == "win32"` 감지로 자동으로
모든 tmux/bash 호출을 `wsl.exe`로 감쌉니다.

### 방법 B: WSL 안에서 빌드 (Linux 바이너리)

```bash
# WSL 안에서
pip install pyinstaller
bash scripts/build-gui-exe.sh
# → dist/pipeline-gui (Linux ELF, Windows에서 실행 불가)
```

이 방법은 Linux 바이너리를 만들므로 Windows 더블클릭에는 사용 불가합니다.
WSL 안에서 직접 실행할 때만 유용합니다.

### 결과

```
dist/pipeline-gui.exe    (방법 A, ~15-25MB 예상)
dist/pipeline-gui        (방법 B, Linux only)
```

### 배포

1. `dist/pipeline-gui.exe`를 Windows 로컬 경로에 복사
2. 더블클릭으로 실행
3. GUI가 WSL 내부의 pipeline을 제어

## 사용자 사전 조건

exe를 받은 사용자가 준비해야 할 것:

1. **Windows 11** + WSL2 + WSLg
2. **WSL 배포판** (Ubuntu 권장): `wsl --install`
3. **WSL 내부 패키지**: `sudo apt install python3 python3-tk tmux`
4. **Agent CLI**: `npm install -g @anthropic-ai/claude-code`, `npm install -g codex`, `npm install -g @google/gemini-cli`
5. **projectH repo**: `git clone` + 경로 확인

## exe 실행 시 내부 동작

1. exe가 `pipeline-gui.py`의 tkinter GUI를 표시
2. GUI가 `wsl.exe -d Ubuntu --cd /path -- ...` 형태로 WSL 명령 호출
3. Start 버튼 → `bash -l start-pipeline.sh` 실행
4. 상태 폴링 → `tmux has-session`, `tmux capture-pane` 호출
5. Stop 버튼 → `bash stop-pipeline.sh` 실행

## 현재 제한

- exe는 WSL 내부 project 경로를 **하드코딩하지 않습니다** — 실행 시 인자 또는 환경변수로 전달
- exe 단독으로는 파이프라인이 동작하지 않습니다 — WSL 백엔드가 필수
- WSLg가 없는 Windows 10에서는 GUI 창이 뜨지 않습니다

## 빌드 검증 체크리스트

- [ ] `pyinstaller --version` 확인
- [ ] `python3 -c "import tkinter"` 성공
- [ ] `bash scripts/build-gui-exe.sh` 성공
- [ ] `dist/pipeline-gui.exe` 파일 생성 확인
- [ ] Windows에서 exe 더블클릭 → GUI 창 표시
- [ ] Start → pipeline 기동 확인
- [ ] 상태 표시 truth 확인
