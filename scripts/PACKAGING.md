# Pipeline GUI exe 패키징 가이드

## exe가 의미하는 것

`pipeline-gui.exe`는 **독립 실행형 앱이 아닙니다.**

```
[Windows]                         [WSL]
pipeline-gui.exe ──wsl.exe──→ tmux / watcher / agent CLIs
(frontend wrapper)                (backend runtime)
```

exe는 `wsl.exe`를 통해 WSL 내부의 tmux/watcher/agent CLI를 제어하고 상태를 읽는 **Windows-side GUI wrapper**입니다.

대상 repo는 projectH 자체일 필요가 없습니다. `AGENTS.md`가 있는 임의의 WSL 내부 repo를 target으로 지정할 수 있습니다.

## 포함/비포함 경계

| 항목 | exe에 포함 | 외부 전제 |
|------|-----------|----------|
| `pipeline-gui.py` 로직 | ✅ | |
| tkinter GUI | ✅ | |
| tmux/WSL 호출 코드 | ✅ | |
| Python runtime | ✅ (PyInstaller 번들) | |
| `start-pipeline.sh` | ✅ (`_data/` 번들) | |
| `stop-pipeline.sh` | ✅ (`_data/` 번들) | |
| `watcher_core.py` | ✅ (`_data/` 번들) | |
| `schemas/*.json` | ✅ (`_data/schemas/` 번들) | |
| WSL2 + WSLg | | ✅ Windows 11 필요 |
| tmux (WSL) | | ✅ `sudo apt install` |
| python3 (WSL) | | ✅ `sudo apt install` |
| Claude/Codex/Gemini CLI | | ✅ npm global install (nvm 권장) |
| target repo | | ✅ WSL 내부 clone, `AGENTS.md` 필수 |

## 패키징 절차

### 방법 A: 빌드 스크립트 사용 (권장)

```bash
pip install pyinstaller
bash scripts/build-gui-exe.sh
```

빌드 스크립트가 자동으로 런타임 자산을 `--add-data`로 포함합니다:
- `start-pipeline.sh` → `_data/start-pipeline.sh`
- `stop-pipeline.sh` → `_data/stop-pipeline.sh`
- `watcher_core.py` → `_data/watcher_core.py`
- `schemas/*.json` → `_data/schemas/`
- `.pipeline/README.md` → `_data/.pipeline/`

exe 내부에서 이 자산은 `sys._MEIPASS/_data/` 아래에서 접근됩니다.
Windows native path(`C:\...\Temp\_MEIxxxx\_data\...`)는 자동으로
`/mnt/c/.../Temp/_MEIxxxx/_data/...`로 변환되어 WSL bash에 전달됩니다.

### 방법 B: 수동 빌드 (Windows PowerShell)

```powershell
pip install pyinstaller
# repo 루트에서 실행 (pipeline_gui/ 패키지가 있는 위치)
pyinstaller --onefile --noconsole --name pipeline-gui `
    --paths "." `
    --add-data "start-pipeline.sh;_data" `
    --add-data "stop-pipeline.sh;_data" `
    --add-data "watcher_core.py;_data" `
    --add-data "schemas/agent_manifest.schema.json;_data/schemas" `
    --add-data "schemas/job_state.schema.json;_data/schemas" `
    pipeline-gui.py
```

`windows-launchers/` 폴더에서 실행하는 경우:
```powershell
pyinstaller --onefile --noconsole --name pipeline-gui `
    --paths ".." `
    --add-data "..\start-pipeline.sh;_data" `
    --add-data "..\stop-pipeline.sh;_data" `
    --add-data "..\watcher_core.py;_data" `
    --add-data "..\schemas\agent_manifest.schema.json;_data/schemas" `
    --add-data "..\schemas\job_state.schema.json;_data/schemas" `
    ..\pipeline-gui.py
```

`--add-data`를 빼고 빌드하면 `Setup: Missing start-pipeline.sh, ...`가 뜹니다.

### 방법 C: WSL 안에서 빌드 (Linux 바이너리)

```bash
pip install pyinstaller
bash scripts/build-gui-exe.sh
# → dist/pipeline-gui (Linux ELF, Windows에서 실행 불가)
```

## 사용자 사전 조건

1. **Windows 11** + WSL2 + WSLg
2. **WSL 배포판** (Ubuntu 권장): `wsl --install`
3. **WSL 내부 패키지**: `sudo apt install python3 python3-tk tmux`
4. **Node.js** (nvm 권장): Gemini CLI가 Node 20+ 필요
5. **Agent CLI**: `npm install -g @anthropic-ai/claude-code`, `npm install -g codex`, `npm install -g @google/gemini-cli`
6. **Target repo**: WSL 내부 git clone, `AGENTS.md` 필수

## 사용 흐름

### 1. Project path 설정

exe 시작 시 다음 순서로 project path를 결정합니다:

1. **명령줄 인자**: `pipeline-gui.exe /home/user/code/finance`
2. **환경변수**: `PROJECT_ROOT`
3. **저장된 경로**: `~/.pipeline-gui-last-project` (최근 5개, 최신순)
4. **현재 디렉터리**: `cwd`

GUI 안에서:
- **Browse…** 버튼으로 WSL 폴더 선택 (UNC 경로 자동 정규화)
- **Apply** 버튼으로 적용 (marker 기반 validation)
- **Recent** quick-select 버튼으로 최근 사용한 경로 선택

### 2. Setup/Check

**Setup/Check** 버튼은 실행 전제를 확인합니다:

**Hard blockers** (없으면 Start 불가):
- CLI: tmux, python3, claude, codex, gemini
- launcher 자산: start-pipeline.sh, stop-pipeline.sh, watcher_core.py
- target repo: AGENTS.md

**Soft warnings** (없어도 Start 가능):
- schemas/agent_manifest.schema.json
- schemas/job_state.schema.json

**Guide 파일 생성**: AGENTS.md, CLAUDE.md, GEMINI.md가 target repo에 없으면 승인 후 기본 템플릿 생성 (기존 파일은 덮어쓰지 않음)

Setup 상태:
- `Setup: ● Ready` — hard blocker 전부 OK, soft 전부 OK
- `Setup: ● Ready (warnings)` — hard OK, soft warning
- `Setup: ■ Missing ...` — hard blocker 미충족
- `Setup: ■ Install failed` — 설치 실패

### 3. Start / Stop / Restart

- **Start**: Setup이 ready/ready_warn일 때만 활성. pipeline 시작만 수행.
- **Stop**: 현재 project session만 종료 (다른 project 영향 없음)
- **Restart**: Stop → Start 순차 실행
- **Attach tmux**: 별도 터미널에서 현재 project session에 attach

### 4. Project-aware session

| project | session name |
|---------|-------------|
| `/home/user/code/projectH` | `aip-projectH` |
| `/home/user/code/finance` | `aip-finance` |

규칙: `aip-<safe-dirname>` (알파벳/숫자/하이픈/밑줄만)

동시에 여러 project의 pipeline을 독립적으로 실행할 수 있습니다.
GUI는 현재 선택된 project의 session만 추적합니다.

## Windows path 정규화

| 입력 | 변환 결과 | 용도 |
|------|----------|------|
| `\\wsl.localhost\Ubuntu\home\...` | `/home/...` | Browse → Apply |
| `//wsl.localhost/Ubuntu/home/...` | `/home/...` | tkinter filedialog |
| `C:\...\Temp\_MEI...\start-pipeline.sh` | `/mnt/c/.../start-pipeline.sh` | frozen asset → WSL bash |
| `/home/user/proj` | `/home/user/proj` | passthrough |

## 현재 확인 상태

| 항목 | 상태 | 확인 방법 |
|------|------|----------|
| WSL에서 `python3 pipeline-gui.py` | ✅ | 개발 중 직접 실행 |
| external repo (`finance`) Start | ✅ | Linux에서 직접 실행 확인 |
| project-aware session 분리 | ✅ | `aip-projectH` ≠ `aip-finance` 동시 확인 |
| Stop이 다른 project에 영향 없음 | ✅ | finance stop 후 projectH 유지 확인 |
| watcher가 target repo를 감시 | ✅ | finance watcher.log 기록 확인 |
| Windows `.cmd` launcher | ✅ | 코드 확인 + 사용자 실행 |
| Windows native exe GUI 표시 | ✅ | 사용자 직접 확인 |
| exe에서 Pipeline/Watcher/agent 상태 | ✅ usable | 사용자 직접 확인 |
| exe에서 Browse/Apply/recent | ✅ | 사용자 직접 확인 |
| exe에서 WORKING elapsed 1s tick | ✅ | 사용자 확인 |
| frozen asset → /mnt/ 변환 | 코드 적용 완료 | Windows exe 재빌드 후 검증 필요 |
| PyInstaller temp dir 수명 | 알려진 제한 | exe 종료 시 번들 자산 삭제됨 (아래 참고) |
| Windows 10 (WSLg 없음) | 미테스트 | GUI 창이 뜨지 않을 것으로 예상 |

## 알려진 제한

1. **PyInstaller onefile temp 디렉터리**: exe 종료 시 `_MEIxxxx` temp 디렉터리가 삭제됩니다. 이 안에 번들된 `start-pipeline.sh`, `watcher_core.py`가 포함되어 있으므로, exe가 종료되면 이미 실행 중인 watcher가 참조하는 `SCRIPT_DIR` 경로가 사라질 수 있습니다. 현재는 exe가 살아있는 동안에는 temp 디렉터리도 유지됩니다.

2. **source 실행 시 session 이름**: `python3 pipeline-gui.py`로 직접 실행하면 `APP_ROOT`가 projectH repo root가 됩니다. launcher 자산은 repo에서 직접 참조되므로 temp 문제가 없습니다.

3. **legacy `ai-pipeline` 세션**: 이전 구조에서 만들어진 `ai-pipeline` 세션이 남아 있을 수 있습니다. `tmux kill-session -t ai-pipeline`으로 정리할 수 있습니다.

## 빌드 검증 체크리스트

- [ ] `pyinstaller --version` 확인
- [ ] `python3 -c "import tkinter"` 성공
- [ ] `bash scripts/build-gui-exe.sh` 또는 수동 빌드 성공
- [ ] `dist/pipeline-gui.exe` 파일 생성 확인
- [ ] Windows에서 exe 더블클릭 → GUI 창 표시
- [ ] Browse… → WSL 경로 선택 → Apply → 정상 적용
- [ ] Setup/Check → Ready (또는 Ready with warnings)
- [ ] Start → pipeline 기동 → Pipeline: Running
- [ ] agent 상태 표시 truth 확인
- [ ] WORKING elapsed 1초 tick 확인
- [ ] Stop → 해당 project session만 종료
