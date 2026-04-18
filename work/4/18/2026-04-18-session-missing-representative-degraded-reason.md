# Session-missing representative degraded_reason over lane recovery failures

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 300, HANDOFF_SHA `6c8686e7...`)가 직전 라운드에서 green이 된 fault-check의 live `session loss degraded` 단계 surface 의미를 좁힐 current-risk를 지목함. 보존된 증거에서는 `reason=claude_recovery_failed`, `reasons=["claude_recovery_failed","codex_recovery_failed","gemini_recovery_failed","session_missing"]`로 나와서, 실제 root cause인 `session_missing`이 per-lane `*_recovery_failed` 뒤로 밀려 있었음.
- `docs/TASK_BACKLOG.md`는 supervisor-owned runtime surface가 하나의 representative `degraded_reason` + 전체 `degraded_reasons` 리스트를 제공해야 한다고 이미 정해뒀기 때문에, 이 ordering을 supervisor 쪽에서 먼저 고정하고 fault-check도 같이 assert하는 편이 controller/browser로 widening하는 것보다 좁은 다음 슬라이스임.

## 핵심 변경

- `pipeline_runtime/supervisor.py::_write_status()`
  - `session_missing_reasons`를 `active_breakage_reasons` 앞으로 이동시켜, 세션이 사라진 상태에서 per-lane `*_recovery_failed`가 같이 붙어도 representative `degraded_reason`이 `session_missing`으로 유지되도록 함. `runtime_inactive` 분기(`launch_failed_reason`가 없는 정리 경로)와 `_launch_failed_reason` 우선순위는 건드리지 않음. secondary lane 실패는 그대로 `degraded_reasons` 뒤쪽에 남아 evidence로 유지됨.
- `scripts/pipeline_runtime_gate.py::run_fault_check()`
  - 기존 `session loss degraded` wait 조건을 그대로 쓰면서, wait 성공 이후에 `representative_reason == "session_missing"`을 추가로 assert. 이 assertion이 실패하면 `session_loss_ok=False`로 떨어뜨려 gate가 바로 실패하도록 함.
  - detail 포맷에 `secondary_recovery_failures` 키를 추가해, `degraded_reasons` 안의 `*_recovery_failed` entry들을 evidence로 그대로 노출. 이들은 존재할 때만 기록되고 필수 아님(예: 단순 세션 상실 시 해당 경로가 발생하지 않아도 허용).
- `tests/test_pipeline_runtime_supervisor.py`
  - `test_session_loss_keeps_session_missing_as_representative_reason_over_lane_recovery_failures` 추가. 세 lane을 BROKEN + `note=exit:-15`로 mock하고 `restart_lane`을 False로 return시켜 `claude_recovery_failed`, `codex_recovery_failed`, `gemini_recovery_failed`가 모두 생성되는 상황을 재현. 결과 `status["degraded_reason"]`과 `status["degraded_reasons"][0]`이 모두 `session_missing`이며, 세 secondary 실패도 `degraded_reasons`에 함께 남는지 검증. 기존 session-loss 관련 테스트는 그대로 통과.
- `tests/test_pipeline_runtime_gate.py`
  - `test_run_fault_check_session_loss_requires_session_missing_as_representative_reason` 추가. 올바른 ordering 상태와 잘못된 ordering(representative가 `claude_recovery_failed`) 상태를 각각 `_read_status` return으로 주입. `_wait_until`를 one-shot evaluator로 patch해 live 대기를 skip. 올바른 경우 `session loss degraded` entry의 `ok=True`, detail에 `reason=session_missing` + `secondary_recovery_failures=[...]` 포함. 잘못된 경우 `ok=False` 이며 전체 `run_fault_check`가 False로 떨어짐을 확인.
- `.pipeline/README.md`
  - fault-check degrade 문단에 한 줄 추가: tmux session이 사라진 경우 supervisor는 representative `degraded_reason`을 `session_missing`으로 유지하고 `*_recovery_failed`는 `degraded_reasons` 뒤쪽의 secondary evidence로 남긴다는 규칙을 문서화.

## 검증

- `python3 -m py_compile pipeline_runtime/supervisor.py scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_gate` → 92/92 pass (supervisor 73 + gate 19).
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md` → 모든 단계 `PASS`. 특히 `session loss degraded` detail이 `runtime_state=DEGRADED, reason=session_missing, reasons=["session_missing", "claude_recovery_failed", "codex_recovery_failed", "gemini_recovery_failed"], secondary_recovery_failures=["claude_recovery_failed", "codex_recovery_failed", "gemini_recovery_failed"]`로 기록됨. 이후 `lane recovery` 단계에서도 `recovery_completed payload={"lane":"Claude","attempt":1,"result":"restarted"}` 그대로 유지돼 직전 라운드의 pre-accept 복구 경로는 회귀하지 않음.
- `git diff --check -- pipeline_runtime/supervisor.py scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- representative `degraded_reason`을 `session_missing`으로 고정한 것은 tmux session이 사라진 family에 한정된 의미고, 앞으로 `_launch_failed_reason`이나 receipt manifest mismatch 등 다른 root cause와 동시에 발생하는 경우에는 `_launch_failed_reason` → `session_missing` → active/receipt/lane → job-state 순서를 유지함. 새 root-cause class가 등장해 `session_missing`보다 먼저 와야 한다면 이 배열을 다시 정렬해야 하며, 이번 slice에서는 taxonomy를 넓히지 않았음.
- gate 쪽 test는 `_wait_until`를 one-shot evaluator로 mock해 live 루프를 생략함. 실제 tmux 환경의 시간/재시도 특성은 CLI 실행(앞 `fault-check` 결과)으로만 커버됨. 다음 라운드에서 fault-check 대기 시간 자체가 길어지면 별도 타임아웃 튜닝이 필요할 수 있음.
- `secondary_recovery_failures`는 detail 문자열에만 노출되고 machine-parse를 위한 별도 필드로 리턴되지 않음. 만약 CI 대시보드가 secondary evidence를 별도 파싱해야 하면, 다음 라운드에서 `checks` payload에 list 필드를 추가하는 작은 후속 slice가 필요할 수 있음.
