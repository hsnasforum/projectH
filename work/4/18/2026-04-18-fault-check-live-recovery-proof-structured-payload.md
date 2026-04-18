# Fault-check live recovery proof checks: structured data payload

## 변경 파일

- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 302, HANDOFF_SHA `be3898ff...`)가 직전 라운드에서 `session loss degraded`에 추가한 구조화 `data` payload를 live 복구 증거 체크(`recoverable lane pid observed`, `lane recovery`)로 확장하라고 지목함. 해당 두 체크는 그동안 lane pid와 `recovery_completed` 이벤트 전체를 human-readable `detail` 문자열로만 노출하고 있었음.
- 같은 fault-check 계약을 유지하면서 gate/harness 레이어만 손대면 되는 슬라이스이므로 supervisor 의미를 다시 열거나 controller/browser로 넓히는 것보다 좁음.

## 핵심 변경

- `scripts/pipeline_runtime_gate.py::run_fault_check()`
  - `recoverable lane pid observed` 체크 앞에서 `lane_pid_data = {"lane": ..., "pid": ..., "pid_available": bool(lane_pid)}`를 먼저 조립하고 check entry에 `data`로 실음. `detail` 문자열은 같은 dict 값에서 파생.
  - `lane recovery` 체크를 성공/실패 두 경로 모두에서 구조화. 성공 경로는 `recovery_data = {"event_observed", "event_type", "lane", "attempt", "result", "event"}` dict(마지막 필드는 원본 event JSON), 실패 경로(`lane_pid_unavailable_before_fault_injection`)는 빈 event + 명시적 `reason` 문자열을 담은 dict를 `data`에 실음. 기존 `detail` 문자열(raw event JSON 또는 안내 문구)은 그대로 보존해 markdown report 가독성은 유지.
- `tests/test_pipeline_runtime_gate.py`
  - `test_live_recovery_proof_checks_expose_structured_data_for_success_path`: `_pick_fault_lane`이 Claude/pid=9876을 돌려주고 `_read_events`가 `recovery_completed` 이벤트를 가진 경우, 두 체크의 `data`가 정확한 값을 담고 markdown report가 여전히 읽히며, 이전 `session loss degraded` 구조화 payload도 회귀하지 않는지 확인.
  - `test_live_recovery_proof_checks_expose_structured_empty_payload_when_lane_pid_unavailable`: `_pick_fault_lane`이 pid=0을 돌려주면 `recoverable lane pid observed`가 `pid_available=False`, `lane recovery`가 `event_observed=False` + `event={}` + `reason="lane_pid_unavailable_before_fault_injection"` 로 structured schema를 유지하는지 잠금. 전체 fault-check가 실패로 끝나는지도 확인.
  - 두 테스트 모두 `_wait_until`을 one-shot evaluator로 patch해 tmux live 대기를 생략.
- `.pipeline/README.md`
  - 직전 라운드의 `session loss degraded` 문단 다음에 한 줄을 추가해, `recoverable lane pid observed`의 `data.lane`/`data.pid`/`data.pid_available`와 `lane recovery`의 `data.event_observed`/`data.event_type`/`data.lane`/`data.attempt`/`data.result`/`data.event`, 그리고 실패 경로의 `data.reason` 명시 문자열 규약을 문서화.

## 검증

- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_gate` → 23/23 pass (기존 21건 + 이번 라운드 추가 2건).
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md` → 모든 단계 `PASS`. `recoverable lane pid observed` detail이 `lane=Claude, pid=201213`로 기록되고 `lane recovery`는 `recovery_completed payload={"lane":"Claude","attempt":1,"result":"restarted"}` raw event를 유지. 새 `data` payload가 같은 evidence를 구조화해 들고 있음. `session loss degraded` 구조화 payload는 직전 라운드와 동일하게 녹색 유지.
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- live 복구 체크 두 개 모두 `data`에 원본 `event` dict를 그대로 싣기 때문에 자동화가 해당 필드를 consume할 때 필드 추가/삭제에 유연해야 함. 필드가 늘거나 줄어도 상위 키(`event_observed`, `event_type`, `lane`, `attempt`, `result`, `reason`)는 schema 안정 계약으로 유지해야 함.
- 현재 `recoverable lane pid observed`의 `data.lane`은 `_pick_fault_lane`이 lane 이름을 돌려주면 채워지므로, pid=0이어도 lane 이름만 있는 중간 상태가 가능함. 이번 테스트에서 그 케이스를 잠갔고, 문서도 이를 감안해 "pid가 없으면 `pid_available=False`"로만 엄격히 표현함.
- `lane recovery` 실패 경로의 `data.reason`은 현재 하나(`lane_pid_unavailable_before_fault_injection`)만 쓰임. 향후 다른 실패 사유가 추가되면 이 필드 값 taxonomy를 함께 확장해야 하며, 이번 slice에서는 taxonomy를 의도적으로 넓히지 않았음.
