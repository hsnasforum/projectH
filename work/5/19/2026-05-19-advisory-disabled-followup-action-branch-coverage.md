# 2026-05-19 advisory disabled followup action branch coverage

## 변경 파일

- `tests/test_pipeline_runtime_automation_health.py`
- `work/5/19/2026-05-19-advisory-disabled-followup-action-branch-coverage.md`
- `pipeline_runtime/automation_health.py`
  - 직전 slice의 `_followup_action(...)` source fix가 현재 dirty 상태로 남아 있어 검증 범위에 포함했습니다. 이번 라운드에서는 추가 수정하지 않았습니다.

## 사용 skill

- `work-log-closeout`: handoff 수행 결과, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1951`이 advisory-disabled profile에서 `_followup_action(...)`이 적용된 non-triage branches를 focused unit replay로 고정하라고 지시했습니다.
- 직전 slice는 triage branch와 supervisor surface를 확인했지만, `pending_operator`, degraded fallback, stale-control grace가 advisory-disabled 상태에서 `automation_next_action=advisory_followup`을 다시 표면화하지 않는지 추가 coverage가 필요했습니다.
- implement lane 지시에 따라 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release는 수행하지 않았고 다음 slice도 선택하지 않았습니다.

## 핵심 변경

- `tests/test_pipeline_runtime_automation_health.py`에 advisory-disabled `pending_operator` branch가 `verify_followup`을 내는 replay를 추가했습니다.
- degraded fallback에서 `degraded_reason=slice_ambiguity`가 advisory-disabled profile이면 `verify_followup`으로 라우팅되는 replay를 추가했습니다.
- stale-control grace path가 advisory-disabled profile에서 `stale_control_advisory`와 `verify_followup`을 함께 표면화하고 `stale_advisory_pending`을 유지하는 replay를 추가했습니다.
- advisory-enabled 기본 `slice_ambiguity` replay는 계속 `advisory_followup`을 기대해 기존 default behavior가 유지되는지도 함께 재확인했습니다.
- `pipeline_runtime/automation_health.py`는 이번 라운드에서 추가 수정하지 않았습니다.

## 검증

- `python3 -m py_compile pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py`
  - 출력 없이 통과했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_advisory_disabled_attention_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_advisory_disabled_pending_operator_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_advisory_disabled_degraded_fallback_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_advisory_disabled_stale_control_grace_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.AutomationHealthTest.test_slice_ambiguity_routes_to_advisory_followup`
  - `Ran 5 tests in 0.000s`
  - `OK`
- `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/19/2026-05-19-advisory-disabled-followup-action-branch-coverage.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- `git diff --check --no-index /dev/null work/5/19/2026-05-19-advisory-disabled-followup-action-branch-coverage.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- `git status --short -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/19/2026-05-19-advisory-disabled-followup-action-branch-coverage.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `pipeline_runtime/automation_health.py`, `tests/test_pipeline_runtime_automation_health.py` 수정과 새 `/work` closeout만 표시됐습니다.

## 남은 리스크

- 이번 handoff는 focused automation-health unit replay였으므로 broader unittest, Playwright/E2E, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- 이번 라운드에서는 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release, external publication을 수행하지 않았습니다.
