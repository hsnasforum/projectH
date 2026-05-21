# 2026-05-19 advisory disabled followup reason matrix replay

## 변경 파일

- `tests/test_pipeline_runtime_automation_health.py`
- `work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md`
- `pipeline_runtime/automation_health.py`
  - 직전 slice의 `_followup_action(...)` source fix가 현재 dirty 상태로 남아 있어 검증 범위에 포함했습니다. 이번 라운드에서는 추가 수정하지 않았습니다.

## 사용 skill

- `work-log-closeout`: handoff 수행 결과, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1952`가 advisory-disabled profile에서 남은 advisory follow-up reason 값들이 `automation_next_action=verify_followup`으로 라우팅되는지 focused unit replay로 고정하라고 지시했습니다.
- 직전 slice는 `pending_operator`, degraded fallback, stale-control grace branch를 확인했지만, `context_exhaustion`, `session_rollover`, `continue_vs_switch`, `operator_retriage_no_next_control` reason matrix는 직접 고정하지 않았습니다.
- implement lane 지시에 따라 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release는 수행하지 않았고 다음 slice도 선택하지 않았습니다.

## 핵심 변경

- `tests/test_pipeline_runtime_automation_health.py`에 advisory-disabled ordinary follow-up reason matrix가 모두 `verify_followup`을 내는 table-driven replay를 추가했습니다.
- 같은 reason matrix가 advisory-enabled default profile에서는 계속 `advisory_followup`으로 남는 table-driven replay를 추가했습니다.
- 이미 검증된 `slice_ambiguity` branch replay와 stale-control grace replay는 중복하지 않았습니다.
- 새 replay가 기존 `_followup_action(...)` helper로 통과해 `pipeline_runtime/automation_health.py`는 이번 라운드에서 추가 수정하지 않았습니다.

## 검증

- `python3 -m py_compile pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py`
  - 출력 없이 통과했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.AutomationHealthTest`
  - `Ran 7 tests in 0.001s`
  - `OK`
- `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- `git diff --check --no-index /dev/null work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- `git status --short -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `pipeline_runtime/automation_health.py`, `tests/test_pipeline_runtime_automation_health.py` 수정과 새 `/work` closeout만 표시됐습니다.

## 남은 리스크

- 이번 handoff는 focused automation-health unit replay였으므로 broader unittest, Playwright/E2E, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- 이번 라운드에서는 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release, external publication을 수행하지 않았습니다.
