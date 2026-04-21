# 2026-04-21 operator gate alias followup recovery

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/21/2026-04-21-operator-gate-alias-followup-recovery.md`

## 사용 skill
- `security-gate`: operator control classification 변경이 파일 삭제/덮어쓰기나 외부 네트워크 실행을 새로 만들지 않고 runtime routing 경계에만 머무르는지 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, runtime 재시작 후 상태를 표준 `/work` 형식으로 남겼습니다.

## 변경 이유
- `.pipeline/operator_request.md` `CONTROL_SEQ: 622`가 `REASON_CODE: branch_commit_and_milestone_transition`, `OPERATOR_POLICY: gate_24h`를 사용했습니다.
- 기존 runtime은 이 reason code를 몰라 `gate_24h + unknown reason`을 `operator_request_gated_hibernate`로 분류했고, launcher가 할 일을 잃은 것처럼 `IDLE`에 머물렀습니다.
- branch commit / milestone transition 계열은 실제로 operator approval 성격이므로 `approval_required`로 정규화해 `pending_operator` / `codex_followup` 경로로 surface해야 합니다.

## 핵심 변경
- `normalize_reason_code(...)`에 `branch_commit_and_milestone_transition`와 `branch_commit_milestone_transition` alias를 추가해 `approval_required`로 수렴시켰습니다.
- `tests/test_operator_request_schema.py`에 해당 alias 회귀 assertion을 추가했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 `gate_24h + branch_commit_and_milestone_transition`이 `hibernate`가 아니라 `pending_operator`, `routed_to=codex_followup`로 남는 회귀 테스트를 추가했습니다.
- pipeline runtime을 재시작해 실제 `.pipeline/operator_request.md` seq 622가 새 코드에서 `VERIFY_FOLLOWUP`으로 재분류되는지 확인했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py`
  - 통과
- `python3 -m unittest tests.test_operator_request_schema tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_branch_commit_gate_stays_followup_visible`
  - `Ran 9 tests in 0.001s`
  - `OK (skipped=1)`
- `python3 - <<'PY' ... classify_operator_candidate(... branch_commit_and_milestone_transition ...)`
  - `mode='pending_operator'`
  - `reason_code='approval_required'`
  - `operator_policy='gate_24h'`
  - `routed_to='codex_followup'`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`
  - 출력 없음, `rc=0`
- startup grace 이후 runtime status 확인
  - `runtime_state='RUNNING'`
  - `autonomy.mode='pending_operator'`
  - `autonomy.reason_code='approval_required'`
  - `turn_state.state='VERIFY_FOLLOWUP'`
  - active verify lane: `Claude`, `state='WORKING'`, `note='followup'`

## 남은 리스크
- 이번 변경은 현재 seq 622 hibernate 고착을 follow-up-visible 상태로 되돌리는 좁은 alias 보강입니다. branch commit / milestone transition 자체의 operator decision은 여전히 verify/handoff follow-up이 다음 control로 닫아야 합니다.
- 전체 `tests.test_pipeline_runtime_supervisor`와 `tests.test_watcher_core`는 이번 긴급 recovery 범위에서는 다시 돌리지 않았습니다. 직전 라운드에서 각각 107/107, 152/152 OK였고 이번에는 alias 경계만 집중 확인했습니다.
- `.pipeline/operator_request.md` 자체는 보존했습니다. 새 runtime 분류로 더 이상 `hibernate`가 아니라 `VERIFY_FOLLOWUP`으로 route됩니다.
