# 2026-05-19 advisory disabled runtime next action surface replay verify

STATUS: verified

## 대상

- 최신 `/work`: `work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md`
- 이전 기준 `/verify`: `verify/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md`
- 목적: advisory-disabled runtime next-action surface replay 구현의 진실성 확인

## 결론

- 최신 `/work`의 `## 변경 파일`은 `pipeline_runtime/automation_health.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_automation_health.py`, `tests/test_pipeline_runtime_supervisor.py`, 새 `/work` closeout이며 현재 scoped status와 일치합니다.
- `pipeline_runtime/supervisor.py`는 status payload에 `runtime_controls`를 포함해 automation-health가 active profile의 `advisory_enabled` 값을 볼 수 있게 됐습니다.
- `pipeline_runtime/automation_health.py`는 `_advisory_enabled(...)`와 `_followup_action(...)`을 통해 advisory-disabled profile에서 attention follow-up을 `verify_followup`으로 표면화합니다.
- 새 automation-health test는 advisory-disabled `slice_ambiguity`가 `verify_followup`으로, advisory-enabled 기본 `slice_ambiguity`가 기존처럼 `advisory_followup`으로 남는 것을 확인합니다.
- 새 supervisor test는 advisory-disabled active profile에서 operator candidate status가 `automation_next_action=verify_followup`을 표면화하는 것을 확인합니다.
- `RUNTIME_STATUS_AT_DISPATCH`는 이번 verify dispatch에서 `runtime_state=RUNNING`, `automation_health=ok`, `automation_next_action=continue`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 제공됐습니다. lane-local runtime/status/tmux 명령은 사용하지 않았습니다.

## 실행한 검증

- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
  - 출력 없이 통과했습니다.
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_advisory_disabled_attention_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_slice_ambiguity_routes_to_advisory_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_advisory_disabled_operator_candidate_routes_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_next_direction_after_launcher_close`
  - `Ran 4 tests in 0.017s`
  - `OK`
- PASS: `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- CHECK: `git diff --check --no-index /dev/null work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- CHECK: `git status --short -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `pipeline_runtime/automation_health.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_automation_health.py`, `tests/test_pipeline_runtime_supervisor.py` 수정과 새 `/work` closeout만 표시됐습니다.

## 실행하지 않은 검증

- `make e2e-test`, Playwright rerun, runtime live start/stop/restart, tmux control, long soak는 이번 runtime status unit/supervisor replay 범위가 아니어서 실행하지 않았습니다.
- lane-local `status --json`, `doctor --json`, `tmux` 명령은 `RUNTIME_STATUS_AT_DISPATCH`가 authoritative surface로 제공되어 실행하지 않았습니다.

## Council 결정

COUNCIL_DECISION: implement
REASON_CODE: advisory_disabled_followup_action_branch_coverage
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 1951

EVIDENCE:

- `work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md`
- `verify/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md`
- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_automation_health.py`

REJECTED:

- advisory_request: `ADVISORY_ENABLED=false` 조건이므로 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- operator_request: 안전, 승인, truth-sync repair, auth/credential, merge/release/destructive publication 경계가 현재 local work를 막지 않습니다.
- docs-only follow-up: 현재 변경은 runtime helper/test coverage이며 docs drift가 확인되지 않았습니다.
- commit/push/PR/merge/release: publication backlog는 held 상태이며 implement lane에 넘길 수 없습니다.

## 다음 상태

- `.pipeline/implement_handoff.md#1951`로 `_followup_action(...)`이 적용된 remaining advisory-disabled branches를 직접 test하는 bounded unit replay를 넘기는 것이 현재 가장 작은 같은-family current-risk reduction입니다.
- 다음 slice는 `pending_operator`, degraded fallback, stale-control grace처럼 이번 source fix가 건드린 non-triage follow-up branches가 advisory-disabled 상태에서 `verify_followup`을 표면화하는지 확인해야 합니다.
