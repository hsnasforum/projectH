# Fault-check lifecycle checks: structured data payload

## 변경 파일

- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 304, HANDOFF_SHA `2926d6a0...`)가 `fault-check`에 남아 있는 lifecycle check 네 개(`runtime start`, `status surface ready`, `runtime stop after session loss`, `runtime restart`)를 구조화 `data` payload로 옮겨 automation이 `started`/`stopped` 같은 literal detail 문자열을 scraping하지 않아도 되게 하라고 지목함.
- 같은 `fault-check` pass/fail 계약을 유지하면서 gate/harness 레이어만 손대면 되는 슬라이스. 직전 라운드까지 degraded precedence probe · session loss · live recovery 체크가 이미 구조화 payload를 가지고 있어, 남은 lifecycle 네 개만 같은 규약으로 맞추면 자동화의 scraping 의존이 사라짐.

## 핵심 변경

- `scripts/pipeline_runtime_gate.py::run_fault_check()`
  - `runtime start` / `runtime stop after session loss` / `runtime restart` 엔트리에 `data = {"action", "succeeded", "result"}` dict를 실음. `action`은 `"start"` / `"stop"` / `"restart"`, `succeeded`는 `bool`, `result`는 원본 detail 문자열. `detail` 필드는 기존 포맷 그대로 유지해 markdown report 가독성이 회귀하지 않음.
  - `status surface ready` 엔트리에 `data = {"wait_sec", "ready", "runtime_state", "watcher_alive", "active_control_status", "ready_lane_names", "ready_lane_count", "snapshot"}` dict를 실음. `snapshot`은 기존 `_status_readiness_snapshot(status)` 결과를 그대로 재사용해 detail JSON과 동일 tree 유지. `ready_lane_names`는 snapshot.lanes 중 state가 `READY` 또는 `WORKING`인 lane 이름만 골라 담고 `ready_lane_count`로 카운트도 제공.
  - 기존 `detail` 문자열(예: `wait_sec=1.0, {"active_round": ...}`)은 동일 snapshot 객체에서 파생되므로 사람이 보는 markdown report와 structured payload가 같은 source of truth를 공유.
- `tests/test_pipeline_runtime_gate.py`
  - `test_lifecycle_checks_expose_structured_data_on_green_path`: 프로브/live 단계를 모두 mock해 green path를 재현. `runtime start` / `stop` / `restart`의 `data` dict가 각각 `action`/`succeeded=True`/`result`를 정확히 담고, `status surface ready`의 `data`가 `wait_sec`, `ready_lane_names=["Claude","Codex"]`, `ready_lane_count=2`, `snapshot`을 포함하는지 검증. 직전 라운드의 `session loss degraded` / `recoverable lane pid observed` / `lane recovery` structured payload도 동시 존재하는지 확인.
  - `test_lifecycle_runtime_start_failure_exposes_structured_data`: `_start_runtime`이 `(False, "failed: adapter error")`를 돌려주는 경로에서 `runtime start`의 `data`가 `{"action":"start","succeeded":False,"result":"failed: adapter error"}`로 유지되며, 이후 lifecycle 체크(`status surface ready`, `runtime stop after session loss`, `runtime restart`)는 재시도되지 않고 aggregate `ok=False`임을 잠금.
- `.pipeline/README.md`
  - 직전 라운드의 probe 문단 다음에 한 줄을 추가해 lifecycle check 네 개의 `data` schema(`action` / `succeeded` / `result`, 그리고 `status surface ready`의 `wait_sec` / `ready` / `runtime_state` / `watcher_alive` / `active_control_status` / `ready_lane_names` / `ready_lane_count` / `snapshot`)를 문서화.

## 검증

- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_gate` → 26/26 pass (기존 24건 + 이번 라운드 추가 2건).
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md` → 전체 `PASS`. `runtime start`/`runtime stop after session loss`/`runtime restart` detail은 여전히 `started`/`stopped`로 간결하게 남고, `status surface ready` detail은 이전과 동일한 `wait_sec=... + snapshot JSON` 포맷으로 유지. 새 `data` payload가 같은 evidence를 structured 형태로 함께 싣고 있음. 앞선 probe/session-loss/live recovery structured payload도 회귀 없음.
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- lifecycle `data` schema(`action`, `succeeded`, `result`)는 세 action 경로(`start`/`stop`/`restart`) 모두 동일 contract로 고정. 앞으로 새 lifecycle action(예: pause, resume)이 추가되면 같은 dict 모양을 그대로 따라야 하며, 이번 slice에서는 taxonomy를 넓히지 않았음.
- `status surface ready`의 `snapshot`은 `_status_readiness_snapshot(...)` helper 결과를 그대로 싣기 때문에 helper schema가 바뀌면 자동화 consumer도 동반 갱신이 필요함. schema 안정성 관점에서는 helper 자체가 single source of truth로 남는 편이 안전.
- 현재 `result` 필드에는 upstream `_start_runtime`/`_stop_runtime`이 돌려주는 원본 문자열(`started`/`stopped`/`failed:...`)을 그대로 담음. 실패 사유가 다양해지면 별도 taxonomy 필드(예: `failure_reason`)가 필요할 수 있으며, 이번 slice에서는 schema를 넓히지 않고 기본 문자열 전달에 그침.
