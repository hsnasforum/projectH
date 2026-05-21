# 2026-05-19 advisory disabled runtime next action surface replay

## 변경 파일

- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md`

## 사용 skill

- `work-log-closeout`: handoff 수행 결과, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1950`이 advisory-disabled profile에서 runtime status가 `automation_next_action=advisory_followup`을 표면화하지 않도록 focused status-surface replay를 추가하라고 지시했습니다.
- 직전 verify에서 `ADVISORY_ENABLED=false` prompt context와 `automation_next_action=advisory_followup` dispatcher surface가 함께 보고되어 같은 family의 남은 runtime surface risk로 판단됐습니다.
- `PUBLISH_HELD=true`와 `ADVISORY_ENABLED=false` 조건에 따라 commit, push, branch publication, PR creation/reuse/update, PR merge, release는 수행하지 않았습니다.

## 핵심 변경

- `pipeline_runtime/supervisor.py` status payload에 `runtime_controls`를 포함해 automation-health가 active profile의 advisory enablement를 볼 수 있게 했습니다.
- `pipeline_runtime/automation_health.py`에 `_advisory_enabled(...)`와 `_followup_action(...)` helper를 추가해 advisory-disabled 상태에서는 advisory follow-up 대신 verify follow-up을 표면화하도록 했습니다.
- `tests/test_pipeline_runtime_automation_health.py`에 advisory-disabled attention 상태가 `verify_followup`으로 라우팅되고, advisory-enabled 기본 `slice_ambiguity`는 기존처럼 `advisory_followup`으로 남는 replay를 추가했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 advisory-disabled active profile에서 operator candidate status가 `automation_next_action=verify_followup`을 표면화하는 supervisor replay를 추가했습니다.
- 기존 advisory-enabled supervisor surface가 유지되는지 `test_write_status_gates_next_direction_after_launcher_close`도 재확인했습니다.

## 검증

- `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
  - 출력 없이 통과했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_advisory_disabled_attention_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_slice_ambiguity_routes_to_advisory_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_advisory_disabled_operator_candidate_routes_to_verify_followup`
  - `Ran 3 tests in 0.012s`
  - `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_next_direction_after_launcher_close`
  - `Ran 1 test in 0.009s`
  - `OK`
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- `git diff --check --no-index /dev/null work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- `git status --short -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py work/5/19/2026-05-19-advisory-disabled-runtime-next-action-surface-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `pipeline_runtime/automation_health.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_automation_health.py`, `tests/test_pipeline_runtime_supervisor.py` 수정과 새 `/work` closeout만 표시됐습니다.

## 남은 리스크

- `make e2e-test`, Playwright rerun, runtime live start/stop/restart, tmux control, long soak는 이번 focused runtime status replay 범위가 아니어서 실행하지 않았습니다.
- 이번 라운드에서는 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release, external publication을 수행하지 않았습니다.
