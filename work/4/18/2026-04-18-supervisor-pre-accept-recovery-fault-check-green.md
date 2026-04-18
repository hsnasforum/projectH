# Supervisor pre-accept recovery and fault-check gate green

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 299, HANDOFF_SHA `d07a38f6...`)가 직전 라운드에서 추가한 fault-check probe 경로는 초록이지만 live `lane recovery` 단계가 여전히 `FAIL ({})`로 끝나는 current-risk를 지목함. 보존된 synthetic workspace 증거는 `pid=149892` kill → wrapper `BROKEN reason=exit:-15` → 대체 `pid=150889 READY`로 살아나는 사이에 supervisor가 `recovery_started`/`recovery_completed`를 전혀 남기지 않고 `lane_broken` → 지연된 `lane_ready`만 찍는다는 것을 보여줬음.
- 현재 `pipeline_runtime/supervisor.py::_maybe_recover_lane(...)`이 `lane.get("note")`/`failure_reason`을 전부 terminal로 취급해 `claude_exit:-15`로 surface한 뒤 bounded restart 경로를 건너뛰고 있었음. 이 recovery ownership boundary를 좁혀 pre-accept wrapper exit note는 retry budget 안에서 실제로 restart되게 하는 편이 fault-check 기본 gate를 실제로 초록으로 만드는 가장 좁은 수정임.

## 핵심 변경

- `pipeline_runtime/supervisor.py`
  - 상단에 `_TERMINAL_LANE_FAILURE_REASONS = frozenset({_AUTH_LOGIN_REASON})` 집합을 추가. wrapper가 surface하는 `exit:<code>` / `pane_dead` / `heartbeat_timeout` 같은 pre-accept breakage note는 recoverable breakage로 분류되어 이 집합에 포함시키지 않음.
  - `_maybe_recover_lane(...)` 안에서 `if failure_reason:` terminal short-circuit을 `if failure_reason in _TERMINAL_LANE_FAILURE_REASONS:`로 좁힘. 그 결과 non-terminal breakage는 기존 post-accept guard 및 retry budget 경로를 거쳐 `restart_lane(...)`를 1회 호출하고 `recovery_started` / `recovery_completed` 이벤트를 실제로 emit함. `auth_login_required` 같은 terminal reason과 post-accept interrupted replay guard는 이전과 동일하게 restart를 막음.
- `tests/test_pipeline_runtime_supervisor.py`
  - `test_pre_accept_wrapper_exit_note_consumes_retry_budget_and_restarts` 추가. Claude lane이 `state=BROKEN`, `note=exit:-15`, `accepted_task=None`일 때 `_maybe_recover_lane`이 `""`를 리턴하고 `_lane_shell_command("Claude")` → `adapter.restart_lane("Claude", "run-claude")`를 정확히 한 번 호출하며 `_append_event`에 `recovery_started`와 `recovery_completed`가 모두 들어가는지 검증.
  - 기존 `test_auth_failure_breakage_blocks_restart`, `test_claude_post_accept_breakage_blocks_blind_replay`, `test_codex_pre_completion_breakage_restarts_within_retry_budget`, `test_codex_breakage_stops_after_retry_budget`는 그대로 통과시켜 terminal vs recoverable 분기 의미가 유지됨을 확인.
- `.pipeline/README.md`
  - fault-check 문단에 한 줄을 더해 "live `lane recovery` 단계는 wrapper가 남긴 `exit:<code>` / `pane_dead` / `heartbeat_timeout` 같은 pre-accept breakage note를 terminal로 보지 않고 retry budget 안에서 supervisor가 `recovery_started`/`recovery_completed`를 실제로 emit하는지까지 확인하며, terminal recovery block은 `auth_login_required` 같은 명시된 failure reason으로만 좁혀 유지합니다" 라고 명시.
- `scripts/pipeline_runtime_gate.py`
  - 이번 slice에서 추가 수정은 하지 않음. supervisor 쪽 fix만으로 live lane recovery 단계가 녹색으로 돌아와서 gate 계약 변경이 불필요했음.

## 검증

- `python3 -m py_compile pipeline_runtime/supervisor.py scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_gate` → 90/90 pass (supervisor 72 + gate 18).
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md` → 모든 단계 `PASS`. 순서대로 `receipt manifest mismatch degraded precedence`, `active lane auth failure degraded precedence`, `runtime start`, `status surface ready`, `session loss degraded`, `runtime stop after session loss`, `runtime restart`, `recoverable lane pid observed`, `lane recovery`. 마지막 `lane recovery` 단계의 detail에 `event_type=recovery_completed`, `payload={"lane":"Claude","attempt":1,"result":"restarted"}`가 기록돼 supervisor가 실제로 pre-accept kill을 bounded restart로 복구함을 확인. `workspace_retained=False, workspace_cleanup=background_delete_requested(...)`이므로 gate 전체가 녹색.
- `git diff --check -- pipeline_runtime/supervisor.py scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- `_TERMINAL_LANE_FAILURE_REASONS`가 현재 `auth_login_required` 하나만 담고 있음. 추후 새 terminal breakage 클래스(예: 인증 외의 비가역 실패)가 등장하면 이 집합을 명시적으로 확장해야 하며, wrapper 쪽에서 새 note를 terminal처럼 다루고 싶다면 그 이름을 `_detect_active_lane_failure_reason` 또는 동일 집합에 함께 등록해야 함. 조용히 추가되면 이번 slice가 만든 retry 경로가 다시 무력화됨.
- live `session loss degraded` 단계에서 `degraded_reasons`에 이제 `claude_recovery_failed`, `codex_recovery_failed`, `gemini_recovery_failed`가 `session_missing`과 함께 찍힘. session이 통째로 사라진 상태라 모든 lane이 BROKEN이고 restart_lane이 실패하기 때문에 자연스러운 결과지만, 이 surface가 실제 운영 dashboard에서 어떻게 해석되는지는 다음 controller/launcher 라운드에서 확인이 필요함. 이번 slice에서는 controller/browser 표면을 건드리지 않았음.
- fault-check가 이제 end-to-end green이므로 향후 CI/operator 흐름이 이를 default gate로 강하게 기대할 수 있음. fault-check 자체 런타임(특히 `lane recovery` 30초 타임아웃)이 느린 환경에서는 여유 시간을 두고 운영할 것.
