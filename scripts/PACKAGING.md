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
| `_data/token collector runtime` | ✅ (`_data/` 번들) | |
| `schemas/*.json` | ✅ (`_data/schemas/` 번들) | |
| WSL2 + WSLg | | ✅ Windows 11 필요 |
| tmux (WSL) | | ✅ `sudo apt install` |
| python3 (WSL) | | ✅ `sudo apt install` |
| Claude/Codex/Gemini CLI | | ✅ npm global install (nvm 권장) |
| target repo | | ✅ WSL 내부 clone, `AGENTS.md` 필수 |

## 패키징 절차

### 방법 A: 빌드 스크립트 사용

```bash
python3 -m venv .venv-build
. .venv-build/bin/activate
python -m pip install -U pip pyinstaller
bash scripts/build-gui-exe.sh
```

중요:
- `bash scripts/build-gui-exe.sh`는 **지금 실행 중인 bash 환경**의 Python/PyInstaller를 사용합니다.
- Windows PowerShell에서 `pip install pyinstaller`를 했더라도, 그 뒤 `bash ...`를 호출하면 WSL/bash 쪽에서는 안 보일 수 있습니다.
- Ubuntu/WSL에서는 `python3 -m pip install ...`가 `externally-managed-environment`로 막힐 수 있으므로, 위처럼 `venv`를 쓰는 편이 안전합니다.
- PowerShell에서 Windows exe를 바로 만들고 싶으면 아래 **방법 B**를 사용하시는 편이 가장 확실합니다.
- 이 방법을 WSL 안에서 실행하면 결과물은 보통 `dist/pipeline-gui` Linux 바이너리이며, Windows용 `.exe`가 아닙니다.

빌드 스크립트가 자동으로 런타임 자산을 `--add-data`로 포함합니다:
- `start-pipeline.sh` → `_data/start-pipeline.sh`
- `stop-pipeline.sh` → `_data/stop-pipeline.sh`
- `watcher_core.py` → `_data/watcher_core.py`
- `pipeline_gui/token_usage_shared.py` → `_data/token_usage_shared.py`
- `pipeline_gui/token_dashboard_shared.py` → `_data/token_dashboard_shared.py`
- `_data/` → `_data/` (`token_collector.py`, `token_store.py`, `job_linker.py`, `token_parsers/`, `token_schema.sql`)
- `schemas/*.json` → `_data/schemas/`
- `.pipeline/README.md` → `_data/.pipeline/`

exe 내부에서 이 자산은 `sys._MEIPASS/_data/` 아래에서 접근됩니다.
Windows native path(`C:\...\Temp\_MEIxxxx\_data\...`)는 자동으로
`/mnt/c/.../Temp/_MEIxxxx/_data/...`로 변환되어 WSL bash에 전달됩니다.

### 방법 B: 수동 빌드 (Windows PowerShell)

중요:
- **현재 PowerShell 위치가 repo 루트**이면 바로 아래 첫 번째 명령을 사용합니다.
- **현재 PowerShell 위치가 `windows-launchers/` 폴더**이면 그 다음 `..\\` 버전을 사용합니다.
- 두 명령을 섞으면 일부 번들 자산만 들어가고, 특히 `TOKENS` 패널용 `_data/token runtime`이 빠질 수 있습니다.
- **repo 루트에서 실행한 빌드 결과물은 `<repo>/dist/pipeline-gui.exe`**에 생성됩니다.
- **`windows-launchers/` 폴더에서 실행한 빌드 결과물은 `<repo>/windows-launchers/dist/pipeline-gui.exe`**에 생성됩니다.
- `scripts/build-gui-exe.sh`로 Windows `.exe`가 만들어진 경우에는 `<repo>/dist/pipeline-gui.exe`를 `<repo>/windows-launchers/dist/pipeline-gui.exe`로도 자동 동기화해 두 복사본이 stale drift를 일으키지 않게 합니다.

```powershell
pip install pyinstaller
# repo 루트에서 실행 (pipeline_gui/ 패키지가 있는 위치)
pyinstaller --clean -y --onefile --noconsole --name pipeline-gui `
    --paths "." `
    --add-data "start-pipeline.sh;_data" `
    --add-data "stop-pipeline.sh;_data" `
    --add-data "watcher_core.py;_data" `
    --add-data "pipeline_gui/token_usage_shared.py;_data" `
    --add-data "pipeline_gui/token_dashboard_shared.py;_data" `
    --add-data "_data;_data" `
    --add-data "schemas/agent_manifest.schema.json;_data/schemas" `
    --add-data "schemas/job_state.schema.json;_data/schemas" `
    --add-data ".pipeline/README.md;_data/.pipeline" `
    pipeline-gui.py
```

`windows-launchers/` 폴더에서 실행하는 경우:
```powershell
pyinstaller --clean -y --onefile --noconsole --name pipeline-gui `
    --paths ".." `
    --add-data "..\start-pipeline.sh;_data" `
    --add-data "..\stop-pipeline.sh;_data" `
    --add-data "..\watcher_core.py;_data" `
    --add-data "..\pipeline_gui\token_usage_shared.py;_data" `
    --add-data "..\pipeline_gui\token_dashboard_shared.py;_data" `
    --add-data "..\_data;_data" `
    --add-data "..\schemas\agent_manifest.schema.json;_data/schemas" `
    --add-data "..\schemas\job_state.schema.json;_data/schemas" `
    --add-data "..\.pipeline\README.md;_data/.pipeline" `
    ..\pipeline-gui.py
```

`_data` 번들을 `;.`로 잘못 넣어도 `token_collector.py`가 bundle root로 들어가 버려 `Setup`은 살아 보여도 `TOKENS > FULL HISTORY / REBUILD DB`가 실패할 수 있습니다. token runtime은 반드시 `_data;_data`로 넣어야 합니다.
Windows 수동 빌드는 `--clean -y`를 포함한 명령으로 매번 새로 만드는 편이 안전합니다. 이전 캐시가 남아 있으면 수정한 runtime 경로 로직이 exe에 반영되지 않은 것처럼 보일 수 있습니다.
최신 exe는 WSL이 `_MEIPASS` 임시 폴더를 직접 실행하지 않도록, 필요한 GUI/runtime 파일을 target project 아래 `.pipeline/gui-runtime/_data/`로 staging한 뒤 그 안정 경로를 사용합니다.

Windows에서 exe를 배포용으로 만들 때는, 환경 혼선을 줄이려면 이 PowerShell 방법을 우선 권장합니다. 현재 기준 기본 권장 경로도 이 방법입니다.

### 방법 C: PowerShell safe-copy 빌드 (권장)

WSL 파일시스템을 Windows Python이 직접 읽으면 bytecode 캐시가 꼬여서 소스 수정이 exe에 반영되지 않는 문제가 있습니다. 이 방법은 소스를 Windows `%TEMP%`로 복사한 뒤 빌드하여 문제를 회피합니다.

```powershell
cd \\wsl.localhost\Ubuntu\home\xpdlqj\code\projectH
.\scripts\build-gui-exe.ps1
```

스크립트가 자동으로:
1. WSL 소스를 `%TEMP%\pipeline-gui-build\`로 복사
2. `__pycache__` 제거
3. 복사된 소스에 최신 코드가 포함됐는지 검증
4. PyInstaller 빌드
5. 결과물을 `dist/pipeline-gui.exe`와 `windows-launchers/dist/pipeline-gui.exe`로 복사
6. exe 내부에 코드 변경이 반영됐는지 검증

### 방법 D: WSL 안에서 빌드 (Linux 바이너리)

```bash
python3 -m venv .venv-build
. .venv-build/bin/activate
python -m pip install -U pip pyinstaller
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

### 2. Guide 모드

상단 `OPS / GUIDE` 전환을 제공합니다:

- `OPS`: Setup/Start/Restart, agent 상태, pane tail, watcher log를 보는 운영 화면
- `GUIDE`: read-only canonical `Pipeline Agent Orchestration Guide`
- `Export .md`: GUIDE 본문을 현재 project 이름 기반 기본 파일명으로 저장

Guide는 project별 draft 편집기가 아니라, 앱 안에 내장된 기준 운영 문서 뷰어입니다.

### 3. Setup/Check

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

### 4. Start / Stop / Restart

- **Start**: Setup이 ready/ready_warn일 때만 활성. pipeline 시작만 수행.
- **Stop**: 현재 project session만 종료 (다른 project 영향 없음)
- **Restart**: Stop → Start 순차 실행
- **Attach tmux**: 별도 터미널에서 현재 project session에 attach

### 5. Token maintenance

`TOKENS` 패널은 usage DB를 직접 다루는 수동 action 두 개를 제공합니다.

- `FULL HISTORY`
  - 기존 `usage.db`를 유지한 채 전체 히스토리를 누적 보강합니다.
  - `force-rescan`으로 기존 `file_state`가 있어도 전체 로그를 다시 스캔합니다.
  - dedup가 중복 적재를 막습니다.
- `REBUILD DB`
  - 임시 DB로 전체 스캔을 다시 수행합니다.
  - 성공 시 기존 `usage.db`는 timestamp backup으로 남기고 새 DB로 교체합니다.

두 action 모두 실행 중 collector가 살아 있으면 잠시 멈췄다가 작업 후 다시 시작합니다.
자동 daemon collector 기본값은 `--since-days 7`입니다.
collector 복귀 경로는 `tmux usage-collector` window 우선이며, tmux session이 없을 때만 background fallback을 사용합니다.
job별 비용 집계는 `Codex slot_verify dispatch` 외에 `Claude artifact_seen`, `Gemini notify` 기반 저신뢰 링크도 함께 사용하며, UI에서는 confidence를 같이 표시합니다.
`Top jobs` 줄은 대표 link method와 `low-confidence/total` 비율도 함께 보여줍니다.
linked sample이 아직 없는 source는 `Agents` 줄에 `no-link`로 표시됩니다.
agent 카드를 클릭하면 `TOKENS` 패널에 해당 source 기준 선택 상세(`usage`, latest-day 합계, linked/no-link)가 함께 표시됩니다.
수동 token action 진행 중에는 `Action:` 줄에 `0~100%`와 `scan x/y` 진행률이 표시됩니다.
아직 `usage.db`가 없는 project에서는 action 도중 `Collector/Today/Agents/Top jobs`가 `loading...`으로 표시되며, 완료 후 실제 집계로 전환됩니다.
오늘 usage가 없고 최근 usage만 남아 있는 경우에는 `TOKENS` 패널이 최신 usage day로 자동 fallback됩니다.
agent 카드의 `Quota:` summary는 초반 전체 화면 로딩을 막지 않도록 비동기 캐시로 갱신됩니다.
기존 collector를 잠시 멈춰야 하는 경우에는 `stopping collector` 단계가, action 완료 후 복귀 시에는 `starting collector` 단계가 `Action:` 줄에 표시됩니다.

### 6. Project-aware session

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
| frozen asset → /mnt/ 변환 | ✅ | Windows exe 재빌드 + 사용자 실행 확인 |
| PyInstaller temp dir 수명 | 알려진 제한 | exe 종료 시 번들 자산 삭제됨 (아래 참고) |
| Windows 10 (WSLg 없음) | 미테스트 | GUI 창이 뜨지 않을 것으로 예상 |

## 알려진 제한

1. **PyInstaller onefile temp 디렉터리**: exe 종료 시 `_MEIxxxx` temp 디렉터리가 삭제됩니다. 이 안에 번들된 `start-pipeline.sh`, `watcher_core.py`가 포함되어 있으므로, exe가 종료되면 이미 실행 중인 watcher가 참조하는 `SCRIPT_DIR` 경로가 사라질 수 있습니다. 현재는 exe가 살아있는 동안에는 temp 디렉터리도 유지됩니다.

2. **source 실행 시 session 이름**: `python3 pipeline-gui.py`로 직접 실행하면 `APP_ROOT`가 projectH repo root가 됩니다. launcher 자산은 repo에서 직접 참조되므로 temp 문제가 없습니다.

3. **legacy `ai-pipeline` 세션**: 이전 구조에서 만들어진 `ai-pipeline` 세션이 남아 있을 수 있습니다. `tmux kill-session -t ai-pipeline`으로 정리할 수 있습니다.

4. **Token DB rebuild backup**: `REBUILD DB`는 성공 시 기존 `usage.db`를 `.pipeline/usage/usage.backup-<timestamp>.db`로 남깁니다. 자동 삭제는 하지 않으므로 필요 시 수동 정리해야 합니다.

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
