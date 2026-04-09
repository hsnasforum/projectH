# Windows Launchers

Windows에서 pipeline GUI를 실행하는 두 가지 방법을 제공합니다.

이 디렉터리의 launcher/controller 보조 도구는 현재 **operator tooling / experimental 축**이며,
문서 비서 본체(`python3 -m app.web`) 릴리즈 게이트와는 별도로 취급합니다.

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

`.cmd`는 별도 UI가 아니라 **같은 `pipeline-gui.py` GUI를 WSL에서 띄우는 Windows-side launcher**입니다.
즉 실행 후에는 `.exe`와 동일하게 GUI 안에서 `찾아보기… / 적용 / 설정 / 시작 / 가이드`를 사용할 수 있습니다.

## 방법 2: `.exe` (GUI 내부에서 경로 설정)

1. `dist/pipeline-gui.exe`를 Windows 로컬 경로에 복사합니다.
2. 더블클릭으로 실행합니다.
3. GUI 안에서 **찾아보기…** 또는 **Recent** quick-select로 WSL project 경로를 선택합니다.
4. **적용** 버튼으로 반영합니다.
5. **설정** 버튼으로 설정 화면으로 들어가고, 필요하면 현재 실행 전제도 다시 확인합니다.
6. **시작** 버튼으로 pipeline을 시작합니다.

마지막 성공 경로는 `~/.pipeline-gui-last-project`에 저장되어 다음 실행 시 자동 복원됩니다.
최근 5개 경로를 기억하며 quick-select 버튼으로 전환할 수 있습니다.

상단 `운영 / 가이드 / 설정` 전환도 공통으로 제공합니다.
- `운영`: 실행/상태/로그를 보는 운영 화면
- `가이드`: read-only canonical guide를 보는 화면 (`.md 내보내기` 가능)
- `설정`: agent 선택, 역할 바인딩, draft/preview/apply를 다루는 setup 화면
  - 우측 pane에는 현재 `setup_id`, 현재 `preview fingerprint`, 지원 수준, 유효성 요약, 적용 준비 상태가 따로 표시됩니다.
  - `초안 저장 -> 미리보기 생성 -> 적용`은 `.pipeline/config/agent_profile.draft.json`과 `.pipeline/setup/{request,preview,apply,result}.json`을 통해 round-trip 됩니다.
  - launcher 기본값은 local setup executor adapter이며, `미리보기 대기 중` / `적용 진행 중` 상태가 실제로 보이도록 preview/result materialization은 UI에서 비동기로 처리됩니다.
  - local executor는 `preview.<setup_id>.staged.json`, `result.<setup_id>.staged.json` 같은 setup-id별 임시 파일을 먼저 쓴 뒤 current setup과 맞을 때만 canonical `preview.json` / `result.json`으로 승격합니다. 오래된 non-current staged 파일은 자동 정리되며, current request/apply가 진행 중인 setup id는 cleanup에서 보호됩니다.
  - launcher는 시작 시와 project 전환 시에도 같은 보호 규칙으로 `.pipeline/setup/*.staged.json`를 한 번 정리합니다. 현재 request/apply 문맥에 걸린 setup id는 startup cleanup에서도 지우지 않습니다.
  - setup 화면의 `staged 정리` 버튼은 같은 보호 규칙으로 오래된 non-current `*.staged.json`만 수동 정리합니다. current `PreviewWaiting` / `ApplyPending` setup id는 이 수동 clean에서도 건드리지 않습니다.
  - setup 우측 pane의 `정리 기록`에는 초기 정리 / 자동 정리 / 수동 정리 결과가 최근 순으로 누적됩니다. 수동 정리에서 삭제 대상이 없을 때도 마지막 시도를 바로 확인할 수 있게 no-op 결과를 남깁니다.
  - `result.restart_required=true`인 적용 결과가 도착하면 setup 화면에서 재시작 확인 후 바로 watcher/launcher 재시작을 요청할 수 있습니다.

최근 launcher는 agent 카드의 `사용량:` 줄에 pane 텍스트 추정값뿐 아니라
로컬 CLI usage 로그(Claude/Codex/Gemini)가 있으면 해당 summary를 우선 표시합니다.
Windows exe에서도 이 정보는 WSL 내부 홈 디렉터리 로그를 기준으로 읽습니다.
agent 상태는 live pane tail을 우선 보며, 오래된 `Working ...` scrollback이나 stale watcher hint보다 현재 prompt-ready 상태를 더 강하게 반영합니다. Codex/Gemini가 실제로 작업 중일 때는 note에 `verify 37s`, `advice 22s`처럼 현재 phase가 함께 표시될 수 있습니다.
`시스템` 카드의 `폴링:` 줄은 상태 스냅샷 신선도를 보여 줍니다. `최신 0초`는 live pane 기준 최신 poll, `지연 4초`는 UI가 이전 스냅샷을 잠깐 들고 있는 상태, `마지막 실행`은 session/watcher가 내려간 뒤 마지막 스냅샷입니다.
`시스템` 카드의 `활성 제어:` 줄은 현재 newest-valid-control 기준으로 어떤 control 슬롯이 실행 입력인지 보여 줍니다. `비활성:` 줄은 더 새로운 유효 슬롯이 있어 무시되는 오래된 stale control 파일을 표시합니다.

`토큰` 패널은 추가로 아래 read/write maintenance action을 제공합니다.
- `전체 히스토리`: 기존 `usage.db`를 유지한 채 전체 히스토리를 누적 보강합니다. dedup로 중복을 막습니다.
- `DB 재구성`: 임시 DB로 전체 스캔을 다시 수행한 뒤 성공 시 기존 `usage.db`를 backup으로 남기고 교체합니다.
- collector 복귀는 `tmux usage-collector` window를 우선 사용합니다. tmux session이 없을 때만 background fallback을 사용합니다.
- job별 비용은 `Codex slot_verify dispatch`를 최우선으로, `Claude work artifact`, `Gemini notify`는 낮은 confidence 휴리스틱으로 함께 합산합니다.
- `주요 작업` 줄에는 대표 link method, 대표 confidence, 저신뢰 비율(`low=a/b`)이 함께 표시됩니다.
- `Agents` 줄에서 usage는 있지만 linked sample이 아직 없는 source는 `no-link`로 표시됩니다.
- agent 카드를 클릭하면 `TOKENS` 패널에 해당 agent 기준의 선택 상세(`usage`, latest-day 합계, linked/no-link)가 함께 표시됩니다.
- 수동 token action 실행 중에는 `작업:` 줄에 `0~100%` 진행률과 `scan x/y` 진행 상황이 함께 표시됩니다.
- `전체 히스토리`는 기존 `file_state`가 있어도 `force-rescan`으로 전체 로그를 다시 훑고, dedup로 이미 적재된 usage는 중복 없이 건너뜁니다.
- 수동 token action 시작 전 기존 collector가 살아 있으면 `stopping collector` 단계가 먼저 표시되고, 완료 후에는 `starting collector` 단계가 표시됩니다.
- 아직 `usage.db`가 없는 project에서 `전체 히스토리` / `DB 재구성`을 실행하면, 스캔이 시작되기 전까지 `수집기/오늘/에이전트/주요 작업`은 `불러오는 중...`으로 표시됩니다.
- 오늘 usage가 없지만 최근 usage가 남아 있는 경우, `TOKENS` 패널은 비우지 않고 최신 usage day를 기준으로 표시합니다.
- agent 카드의 `사용량:` usage summary는 첫 화면 표시를 막지 않도록 비동기 캐시로 갱신됩니다.

자동 collector 기본값은 `--since-days 7`이며, 현재 실측 기준 `14일` 이상은 첫 스캔 체감이 커서 기본값에서 제외했습니다.

exe 빌드 방법은 `scripts/PACKAGING.md`를 참고하세요.
PowerShell에서 `pip install pyinstaller`를 했는데 `bash scripts/build-gui-exe.sh`가 못 찾는 경우에는,
Windows Python과 bash/WSL Python 환경이 분리된 상황일 가능성이 큽니다. 이때는 `scripts/PACKAGING.md`의 PowerShell 수동 빌드 방법을 사용하시거나, bash/WSL 안에서는 `venv`를 만든 뒤 그 안에 PyInstaller를 설치해 주셔야 합니다. Ubuntu/WSL에서는 시스템 Python에 바로 `python3 -m pip install ...`가 `externally-managed-environment`로 막힐 수 있습니다.
수동 PowerShell 빌드 시에는 `start/stop/watcher`만이 아니라 `--add-data "_data;_data"`와 `pipeline_gui/token_usage_shared.py`, `pipeline_gui/token_dashboard_shared.py`도 반드시 포함해야 `토큰` 패널의 `전체 히스토리 / DB 재구성`과 usage 조회가 동작합니다. `--add-data "_data;."`로 넣으면 `token_collector.py`가 bundle root로 들어가서 여전히 missing 경고가 뜰 수 있습니다. 캐시 혼선을 줄이려면 `pyinstaller --clean -y ...`로 빌드하는 편이 안전합니다. 최신 exe는 필요한 GUI/runtime 파일을 target project 아래 `.pipeline/gui-runtime/_data/`로 staging한 뒤 WSL에서 그 안정 경로를 사용합니다.

## 파일

| 파일 | 설명 |
|------|------|
| `pipeline-gui.cmd` | tkinter desktop GUI (`.cmd` 방식, WSLg 필요) |
| `pipeline-tui.cmd` | curses 터미널 TUI |
| `open-controller.cmd` | 현재 WSL IP를 찾아 Windows 기본 브라우저로 controller를 엽니다 |
| `open-controller.ps1` | UNC/PowerShell 환경에서도 현재 WSL IP로 controller를 엽니다 |
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
| project path | `.cmd`의 `WSL_PROJECT`로 기본값 주입 + GUI에서 찾아보기…/적용/Recent 가능 | GUI 내 찾아보기…/적용/Recent |
| 경로 저장 | GUI 최근 5개 저장 지원 (실행 기본값은 `.cmd`의 `WSL_PROJECT`) | GUI 최근 5개 저장 지원 |
| multi-project | 가능 (기본값은 `.cmd`에서, 실행 후 GUI에서도 전환 가능) | 가능 (GUI에서 전환) |
| 설정 점검 | 있음 | 있음 |
| Guide | read-only canonical guide + `Export .md` | read-only canonical guide + `Export .md` |
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
- **경로 못 찾음**: `.cmd`의 `WSL_PROJECT` 확인 또는 exe에서 찾아보기…로 재선택
- **설정: ■ 누락 ...**: 설정 화면에서 설치 제안을 수락하거나 수동 설치 후 재확인
- **Gemini pane dead**: Node 18에서는 Gemini CLI가 실행 안 됨 — `nvm install 22 && nvm alias default 22`
- **agent 상태 OFF/BOOTING 고정**: tmux 세션이 없거나 pane capture 실패 — Start로 pipeline 재기동
- **토큰 패널에서 전체 히스토리 / DB 재구성 실행 중**: collector가 잠시 멈췄다가 작업 후 다시 시작될 수 있음
- **legacy `ai-pipeline` 세션**: `tmux kill-session -t ai-pipeline`으로 정리
- **controller가 Windows 브라우저 `127.0.0.1:8780`에서 안 열림**:
  - 이 환경은 WSL localhost 자동 포워딩이 죽어 있고, 대신 WSL IP (`172.20.x.x`)로는 열릴 수 있습니다.
  - 우선 `python3 -m controller.server` 로그에 출력되는 `Windows fallback: http://<WSL-IP>:8780/controller` 주소로 접속해 보세요.
  - 가장 간단한 우회는 `open-controller.ps1` 또는 `open-controller.cmd`를 실행하는 것입니다. 두 파일 모두 현재 WSL IP를 찾아 기본 브라우저로 `http://<WSL-IP>:8780/controller`를 바로 엽니다.
  - `\\wsl.localhost\...` UNC 경로에서 바로 실행 중이면 `open-controller.ps1` 쪽이 더 안전합니다:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\open-controller.ps1
    ```
  - `127.0.0.1:8780`도 항상 쓰고 싶다면 관리자 PowerShell에서 아래 스크립트를 실행해 localhost portproxy를 잡아 주세요:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\windows-launchers\configure-controller-portproxy.ps1
    ```
  - 적용 확인만 먼저 하고 싶다면:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\windows-launchers\configure-controller-portproxy.ps1 -ShowOnly
    ```
