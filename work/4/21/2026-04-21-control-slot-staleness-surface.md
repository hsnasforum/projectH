# 2026-04-21 control slot staleness surface

## 변경 파일
- `watcher_core.py`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `pipeline-launcher.py`
- `pipeline_gui/home_presenter.py`
- `pipeline_gui/backend.py`
- `pipeline_runtime/cli.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `tests/test_pipeline_gui_backend.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-control-slot-staleness-surface.md`

## 사용 skill
- `security-gate`: control slot 관측이 자동 rollover, control rewrite, commit/push, destructive action으로 이어지지 않는지 확인했습니다.
- `doc-sync`: runtime status field와 launcher/GUI 상세 노출 계약을 `.pipeline/README.md`와 runtime docs에 맞췄습니다.
- `release-check`: 실행한 검사와 미실행 범위를 분리해 handoff 가능 상태를 점검했습니다.
- `finalize-lite`: 구현 종료 전 검증 사실, 문서 동기화, `/work` closeout 필요성을 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 기준으로 현재 closeout을 남겼습니다.

## 변경 이유
- 같은 active `CONTROL_SEQ`가 여러 watcher/supervisor cycle 동안 유지될 때 silent stall처럼 보일 수 있었습니다.
- 이번 slice는 control slot을 수정하지 않고, status/launcher/GUI 상세 surface에서 `control_age_cycles`와 `stale_control_seq`를 볼 수 있게 하는 read-only 관측 경로입니다.

## 핵심 변경
- `advance_control_seq_age()`와 `STALE_CONTROL_CYCLE_THRESHOLD=900`을 `pipeline_runtime/automation_health.py`에 추가하고, health snapshot에 `control_age_cycles`, `stale_control_seq`, `stale_control_cycle_threshold`, `automation_health_detail`을 통과시켰습니다.
- watcher는 `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/operator_request.md`의 valid active `CONTROL_SEQ` 중 최고값을 cycle마다 추적하고, missing/unreadable 경로는 0/false로 fail-safe 처리합니다.
- supervisor도 같은 helper로 status writer 경로의 age를 계산해 launcher/GUI가 실제 canonical `status.json`에서 값을 읽을 수 있게 했습니다.
- launcher line-mode와 GUI console detail은 stale 상태일 때 `제어 슬롯 고착 감지됨 (N 사이클)` 및 raw age/threshold를 표시합니다.
- 자동 action은 추가하지 않았습니다. `stale_control_seq=true`는 detection surface일 뿐 control slot rewrite, rollover, operator stop, commit/push를 트리거하지 않습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/automation_health.py` → 통과
- `python3 -m py_compile watcher_core.py pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py pipeline-launcher.py pipeline_gui/home_presenter.py pipeline_gui/backend.py pipeline_runtime/cli.py` → 통과
- `python3 -m unittest tests.test_pipeline_runtime_automation_health` → 15 tests OK
- `python3 -m unittest tests.test_watcher_core` → 171 tests OK
- `python3 -m unittest tests.test_pipeline_launcher` → 26 tests OK
- `python3 -m unittest tests.test_pipeline_gui_home_presenter` → 17 tests OK
- `python3 -m unittest tests.test_pipeline_gui_backend` → 46 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` → 126 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_watcher_core` → 186 tests OK
- `python3 -m unittest tests.test_pipeline_launcher tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_backend tests.test_pipeline_runtime_supervisor` → 215 tests OK
- `git diff --check watcher_core.py pipeline_runtime/automation_health.py tests/test_watcher_core.py tests/test_pipeline_runtime_automation_health.py` → 통과
- `git diff --check watcher_core.py pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py pipeline-launcher.py pipeline_gui/home_presenter.py pipeline_gui/backend.py pipeline_runtime/cli.py tests/test_watcher_core.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_launcher.py tests/test_pipeline_gui_home_presenter.py tests/test_pipeline_gui_backend.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` → 통과

## 남은 리스크
- threshold는 watcher 기본 1초 polling 기준 약 15분으로 잡았습니다. 실제 운영에서 너무 민감하거나 둔하면 이후 별도 정책 slice로 조정해야 합니다.
- 이번 변경은 read-only surface만 추가했습니다. stale 상태를 자동 복구하거나 다음 control을 쓰는 동작은 의도적으로 구현하지 않았습니다.
- worktree에는 이전 seq 691/정책 문서 라운드의 dirty 변경이 함께 남아 있습니다. 이번 closeout은 그 변경을 되돌리거나 commit/push하지 않았습니다.
