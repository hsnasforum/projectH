# 2026-04-21 pipeline automation health contract

## 변경 파일
- `pipeline_runtime/automation_health.py` (새 파일)
- `pipeline_runtime/supervisor.py`
- `pipeline_gui/backend.py`
- `pipeline_gui/home_models.py`
- `pipeline_gui/home_controller.py`
- `pipeline_gui/home_presenter.py`
- `pipeline_gui/app.py`
- `pipeline-launcher.py`
- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_automation_health.py` (새 파일)
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.gitignore`
- `report/pipeline_runtime/verification/2026-04-21-pipeline-runtime-live-fault-check.md`
- `report/pipeline_runtime/verification/2026-04-21-pipeline-runtime-live-fault-check.json`
- `work/4/21/2026-04-21-pipeline-automation-health-contract.md` (새 파일)

## 사용 skill
- `security-gate`: runtime status/events, launcher 표시, synthetic gate report가 자동화/로그/안전 stop 경계에 영향을 주므로 real-risk operator boundary와 local-first 범위를 확인했습니다.
- `doc-sync`: `.pipeline/README.md`와 pipeline runtime 문서 세트에 새 public interface와 6h baseline 규칙을 동기화했습니다.
- `work-log-closeout`: 이번 구현/검증 라운드의 변경 파일, 검증, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유
- pipeline 런처 자동화가 멈춘 것처럼 보일 때 launcher/GUI가 pane text나 raw note를 직접 추론하지 않고 supervisor가 제공하는 구조화 health만 표시하도록 경계를 고정하기 위해서입니다.
- 선택지 메뉴, next-slice ambiguity, session rollover, context exhaustion 같은 agent-resolvable 상황은 operator stop으로 고정하지 않고 verify/advisory follow-up으로 계속 진행할 수 있어야 합니다.
- 1차 자동화 milestone을 "PR 전 정지 + 6시간 synthetic soak 통과"로 두기 위해, 실패 시 status/events/active control/current run context가 JSON sidecar에 남는 보고서 경로가 필요했습니다.

## 핵심 변경
- `pipeline_runtime/automation_health.py`를 추가해 `automation_health`, `automation_reason_code`, `automation_incident_family`, `automation_next_action` 산출을 supervisor/launcher/GUI/gate가 공유하도록 했습니다.
- canonical incident family를 `signal_mismatch`, `dispatch_stall`, `completion_stall`, `operator_retriage_no_next_control`, `idle_release_pending`, `lane_recovery_exhausted`로 정리했습니다.
- `auth_login_required`와 lane-prefix `*_auth_login_required` reason은 자동 follow-up이 아니라 `needs_operator / operator_required`로 고정했습니다.
- supervisor `status.json`에 automation health 필드를 쓰고, `ok`이 아닌 새 health/reason/action 조합이 승격될 때 `automation_incident` event를 남기도록 했습니다.
- launcher와 GUI는 raw machine note 대신 `정상 / 복구 중 / 주의 / 개입 필요` health label을 우선 표시하고, raw reason/family/action은 recent event 또는 상세 console에 유지합니다.
- synthetic/plain soak summary와 JSON sidecar에 `runtime_context`를 추가했습니다. 이 context에는 current run id, open control, active round, latest status snapshot, recent events, automation health/reason/family/action이 들어갑니다.
- `synthetic-soak` 기본 report slug가 duration에 따라 `6h-synthetic-soak` 또는 `24h-synthetic-soak`로 승격되도록 했습니다.
- `.pipeline/README.md`와 runtime docs에 no-silent-stall contract, health field public interface, `automation_incident`, 6h baseline/24h adoption gate 위치를 반영했습니다.
- worktree 정리 중 생성된 `.pipeline/live-blocked-smoke-*`, `tmp/`, `projectH-selected-files-*.zip`, `errlog/` 같은 로컬 scratch 산출물이 status를 오염시키지 않도록 `.gitignore`를 보강했습니다. 기존 tracked smoke fixture는 복구해 유지했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py pipeline_runtime/wrapper_events.py pipeline_gui/backend.py pipeline_gui/home_models.py pipeline_gui/home_controller.py pipeline_gui/home_presenter.py pipeline_gui/app.py scripts/pipeline_runtime_gate.py pipeline-launcher.py` 통과.
- `python3 -m unittest tests.test_pipeline_runtime_automation_health` 통과. 8 tests.
- `python3 -m unittest tests.test_pipeline_gui_home_presenter` 통과. 16 tests.
- `python3 -m unittest tests.test_pipeline_launcher` 통과. 24 tests.
- `python3 -m unittest tests.test_pipeline_runtime_gate` 통과. 37 tests.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` 통과. 117 tests.
- `python3 -m unittest tests.test_watcher_core` 통과. 159 tests.
- `python3 scripts/pipeline_runtime_gate.py --mode experimental fault-check` 통과. report와 JSON sidecar를 `report/pipeline_runtime/verification/` 아래에 생성했습니다.
- `git diff --check` 통과.
- worktree cleanup 후 `git diff --check` 재실행 통과.

## 남은 리스크
- `python3 scripts/pipeline_runtime_gate.py --mode experimental synthetic-soak --duration-sec 21600 --sample-interval-sec 10 --min-receipts 10`는 6시간이 필요한 baseline gate라 이번 라운드에서는 실행하지 않았습니다.
- 이번 변경은 commit/push/PR 자동화 범위를 열지 않았습니다. PR/publication은 여전히 operator boundary입니다.
- 현재 worktree에는 이번 라운드 이전부터 `.pipeline`, runtime/operator-flow, 여러 `/work`/`verify`/`report` dirty 파일이 많이 남아 있습니다. 이번 라운드는 그 변경을 되돌리지 않고 automation health/gate 계약 범위만 보강했습니다.
