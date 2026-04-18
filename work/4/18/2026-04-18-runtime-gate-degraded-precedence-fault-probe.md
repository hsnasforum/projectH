# Runtime gate fault-check degraded precedence probe

## 변경 파일

- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 298, HANDOFF_SHA `c6c6232f...`)가 직전 라운드에서 고친 receipt/auth degraded precedence boundary가 live stability gate 표면에서는 아직 검사되지 않는다는 current-risk를 지목함. `scripts/pipeline_runtime_gate.py::run_fault_check()`는 session-loss degrade + lane recovery만 보고 있어서 supervisor가 다시 `STARTING`/`STOPPED`로 숨기면 default fault-check가 조용히 통과할 수 있었음.
- 해당 boundary는 supervisor 내부가 아닌 gate/harness 레이어에서 synthetic fixture와 direct `RuntimeSupervisor._write_status()` 호출만으로 재현할 수 있으므로, supervisor production 코드를 다시 여는 대신 fault-check에 probe 두 개를 추가함.

## 핵심 변경

- `scripts/pipeline_runtime_gate.py`에 두 개의 synthetic probe 함수를 추가:
  - `_probe_receipt_manifest_mismatch_degraded_precedence()`: 전용 `tempfile.TemporaryDirectory` 위에 `_write_active_profile`, `.pipeline/claude_handoff.md`, `turn_state.json`, mismatched `artifact_hash` 가진 VERIFY_DONE job state, 그리고 matching receipt manifest (`role: verify`)를 seed. `RuntimeSupervisor(root, start_runtime=False)._write_status()`를 직접 호출한 뒤 `runtime_state == "DEGRADED"`이며 `degraded_reasons`에 `receipt_manifest:job-fault-manifest`로 시작하는 항목이 있어야 ok로 인정.
  - `_probe_active_lane_auth_failure_degraded_precedence()`: synthetic workspace에 CLAUDE_ACTIVE turn_state를 seed하고, `supervisor.adapter.lane_health` / `capture_tail` / `session_exists`를 `unittest.mock`으로 패치해 Claude 팬으로 auth 401 tail을 내려보냄. `_write_status()` 결과가 `runtime_state == "DEGRADED"`이며 `claude_auth_login_required`가 `degraded_reasons`에 있어야 ok로 인정.
- `run_fault_check()` 본문 최상단에서 두 probe를 실행하고 결과를 `checks` 리스트에 `receipt manifest mismatch degraded precedence` / `active lane auth failure degraded precedence` 이름으로 append. live `_start_runtime` 이전이므로 tmux 시작이 실패해도 probe 실패 신호가 그대로 남음.
- `tests/test_pipeline_runtime_gate.py`에 5개 focused 테스트 추가:
  - probe 두 개가 현재 supervisor 상태에서 ok=True를 돌려주는 smoke 두 건
  - `RuntimeSupervisor._write_status`를 `STOPPED`/`STARTING` 리턴으로 패치했을 때 probe가 ok=False로 flag하는 회귀 감지 두 건
  - `run_fault_check`가 live start 이전에 probe 두 개를 먼저 기록하는지 확인하는 순서 보장 한 건
- `.pipeline/README.md`의 degrade 우선순위 문단 바로 다음에 `scripts/pipeline_runtime_gate.py fault-check`가 이 boundary를 synthetic 경로로 먼저 검사한다는 한 줄을 추가해 문서와 harness 실제 동작이 일치하게 맞춤.
- `pipeline_runtime.supervisor.RuntimeSupervisor` import 한 줄만 gate 스크립트 상단에 추가. 다른 supervisor 내부 동작은 건드리지 않음.

## 검증

- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_gate` → 18/18 pass (기존 13건 + 이번 라운드 추가 5건).
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md` → 새 probe 두 단계는 모두 `PASS`(각각 `runtime_state=DEGRADED`, `receipt_manifest:job-fault-manifest:artifact_hash_mismatch` / `claude_auth_login_required` 확인). 기존 `session loss degraded`, `runtime stop after session loss`, `runtime restart`, `recoverable lane pid observed`도 모두 `PASS`. 마지막 `lane recovery` 단계만 `FAIL (detail: {})`로 남았는데, 이는 `recovery_completed` wrapper event를 대기하는 live 경로의 기존 문제이고 이번 slice에서 추가한 probe 경로와는 분리돼 있음. 핸드오프가 "unrelated preexisting runtime issue는 기록만 하고 중단" 하도록 명시했으므로 이번 라운드에서는 widening하지 않고 그대로 기록함.
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- 기존 `lane recovery` FAIL은 이번 slice가 만지는 보드에서 벗어나 있어 여기서는 fix하지 않았음. 다음 라운드에서 synthetic wrapper-event path / retry budget / fake-lane kill 응답을 다시 볼 필요가 있음. 현재 fault-check 종료 코드는 여전히 실패(1)로 떨어지므로 CI/operator 관점에서는 이번 slice의 probe 성공과 preexisting 실패가 섞여 있다는 점을 염두에 두어야 함.
- 새 probe는 `RuntimeSupervisor`를 직접 인스턴스화하므로 향후 supervisor 초기화 비용(autonomy state / adapter wiring 등)이 크게 늘면 fault-check 속도에 영향을 줄 수 있음. 현재 실행 관측상 per-probe 수백 ms 수준이라 허용 가능함.
- `.pipeline/README.md` 추가 문장은 gate 계약을 설명할 뿐 supervisor 코드 경로를 다시 좁히지는 않음. 다음 라운드에서 fault-check 이름 체계가 바뀌면 같은 줄을 함께 갱신해야 함.
