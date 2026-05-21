# 2026-05-20 active verify round status source runtime parity fix

## 변경 파일

- `work/5/20/2026-05-20-active-verify-round-status-source-runtime-parity-fix.md`

## 사용 skill

- `work-log-closeout`: handoff 실행 결과, source/runtime parity evidence, 실제 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2002`가 active verify round status source/runtime parity mismatch를 fix 또는 conclusively localize하라고 요구했습니다.
- 직전 verify는 file-backed `status.json`에서 `active_round.state=VERIFYING`, `turn_state.state=IDLE`, `automation_health=ok`, `automation_next_action=continue` 조합이 재현됐다고 기록했습니다.
- 이번 라운드는 현재 `status.json`을 현재 source의 `derive_automation_health`에 넣어 persisted automation field와 current source 계산을 비교하고, source gap이면 bounded fix를 적용하는 범위였습니다.

## 핵심 변경

- source/test/runtime 파일은 이번 라운드에서 수정하지 않았습니다.
- handoff SHA가 요청값 `ce1c4a218d37d813ebe45148d117021e9887f624f188f2e8d61199b287fc7ddb`와 일치해 실행 가능한 control임을 확인했습니다.
- 현재 file-backed `.pipeline/runs/20260520T061527Z-p65317/status.json`은 implement 라운드 시작 시점에 이미 `active_round=null`, `turn_state=IMPLEMENT_ACTIVE`, `automation_health=ok`, `automation_next_action=continue`로 갱신되어 있었습니다.
- 현재 `status.json` mapping을 현재 `derive_automation_health`에 직접 넣었을 때도 persisted field와 같은 `ok/continue`가 나왔습니다. 이 현재 snapshot은 active verify round를 숨기는 bad combination이 아닙니다.
- 별도의 bad-state fixture인 `active_round.state=VERIFYING` + `turn_state.state=IDLE`를 현재 `derive_automation_health`에 넣었을 때는 `recovering`, `dispatch_stall`, `retrying`을 반환했습니다.
- `pipeline_runtime/supervisor.py`의 write path는 `status.update(derive_automation_health(status))` 후 `atomic_write_json`을 호출하며, exact supervisor regression도 통과했습니다.
- 따라서 이번 라운드에서 확인된 결론은 current source gap이 아니라 이전 dispatch/verify 시점의 transient 또는 stale loaded runtime surface 가능성입니다. watcher/runtime 재시작은 handoff 금지 사항이라 수행하지 않았습니다.

## 검증

- `sed -n '1,220p' AGENTS.md`
  - 결과: CHECK. local-first, approval boundary, implement role stop rules를 확인했습니다.
- `sed -n '1,220p' .pipeline/harness/implement.md`
  - 결과: CHECK. implement role은 정확히 하나의 handoff만 수행하고 `/work` closeout 후 정지해야 함을 확인했습니다.
- `sed -n '1,240p' .pipeline/implement_handoff.md`
  - 결과: CHECK. `CONTROL_SEQ: 2002`와 source/runtime parity localization 범위를 확인했습니다.
- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA와 일치했습니다.
- `python3 - <<'PY' ... derive_automation_health(status.json) ... PY`
  - 결과: CHECK. 현재 file-backed snapshot은 `active_round_state=None`, `turn_state=IMPLEMENT_ACTIVE`, persisted `ok/continue`, derived `ok/continue`였습니다.
- `sed -n '2200,2240p' pipeline_runtime/supervisor.py`
  - 결과: CHECK. supervisor write path가 `status.update(derive_automation_health(status))` 후 `atomic_write_json`을 호출함을 확인했습니다.
- `sed -n '540,585p' tests/test_pipeline_runtime_automation_health.py`
  - 결과: CHECK. `VERIFY_PENDING` 및 `VERIFYING` active round가 `ok/continue`가 아니어야 한다는 exact unit coverage를 확인했습니다.
- `python3 - <<'PY' ... derive_automation_health(bad_state_fixture) ... PY`
  - 결과: PASS. `{'automation_health': 'recovering', 'automation_reason_code': 'dispatch_stall', 'automation_incident_family': 'dispatch_stall', 'automation_next_action': 'retrying'}`를 반환했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verify_pending_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verifying_round_is_not_ok_continue tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_idle_active_verify_round_as_recovering`
  - 결과: PASS. `Ran 3 tests in 0.015s`, `OK`.
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 출력 없음.
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py work/5/20/2026-05-20-active-verify-round-status-source-runtime-parity-fix.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-active-verify-round-status-source-runtime-parity-fix.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- 이번 라운드는 source/runtime parity localization만 수행했습니다. controller Playwright/webServer/full-smoke, broad unit, long soak는 실행하지 않았습니다.
- 관련 source/test 파일들은 handoff 시작 전부터 작업트리에 `M` 상태였습니다. 이번 라운드에서는 기존 변경을 되돌리거나 추가 수정하지 않았습니다.
- verify 시점의 bad file-backed surface는 현재 snapshot에서는 재현되지 않았습니다. current source와 exact tests는 올바른 값을 계산하므로, 남은 가능성은 실행 중 watcher의 stale loaded code, dispatch-time stale status, 또는 짧은 transient surface입니다.
- watcher/runtime 재시작, commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
