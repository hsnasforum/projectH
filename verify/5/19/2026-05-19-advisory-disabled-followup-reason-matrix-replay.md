# 2026-05-19 advisory disabled followup reason matrix replay verify

STATUS: verified

## 대상

- 최신 `/work`: `work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md`
- 이전 기준 `/verify`: `verify/5/19/2026-05-19-advisory-disabled-followup-action-branch-coverage.md`
- 목적: advisory-disabled follow-up reason matrix replay 구현의 진실성 확인

## 결론

- 최신 `/work`의 `## 변경 파일`은 `tests/test_pipeline_runtime_automation_health.py`, 새 `/work` closeout, 그리고 직전 slice에서 남은 `pipeline_runtime/automation_health.py` source fix를 검증 범위로 적은 현재 상태와 일치합니다.
- `tests/test_pipeline_runtime_automation_health.py`에는 `context_exhaustion`, `session_rollover`, `continue_vs_switch`, `operator_retriage_no_next_control`이 advisory-disabled profile에서 `verify_followup`으로 라우팅되는 table-driven replay가 추가됐습니다.
- 같은 reason matrix가 advisory-enabled default profile에서는 계속 `advisory_followup`으로 남는 replay도 추가되어 default advisory-first behavior가 유지됩니다.
- 새 replay가 기존 `_followup_action(...)` helper로 통과해 `pipeline_runtime/automation_health.py`는 최신 `/work` 라운드에서 추가 수정되지 않았습니다.
- `RUNTIME_STATUS_AT_DISPATCH`는 이번 verify dispatch에서 `runtime_state=RUNNING`, `automation_health=ok`, `automation_next_action=continue`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 제공됐습니다. lane-local runtime/status/tmux 명령은 사용하지 않았습니다.

## 실행한 검증

- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py`
  - 출력 없이 통과했습니다.
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.AutomationHealthTest`
  - `Ran 7 tests in 0.001s`
  - `OK`
- PASS: `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- CHECK: `git diff --check --no-index /dev/null work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- CHECK: `git status --short -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `pipeline_runtime/automation_health.py`, `tests/test_pipeline_runtime_automation_health.py` 수정과 새 `/work` closeout만 표시됐습니다.

## 실행하지 않은 검증

- broader unittest, Playwright/E2E, `make e2e-test`, runtime live start/stop/restart, tmux control, long soak는 이번 focused automation-health unit replay 범위가 아니어서 실행하지 않았습니다.
- lane-local `status --json`, `doctor --json`, `tmux` 명령은 `RUNTIME_STATUS_AT_DISPATCH`가 authoritative surface로 제공되어 실행하지 않았습니다.

## Council 결정

COUNCIL_DECISION: implement
REASON_CODE: advisory_disabled_runtime_aggregate_guard
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 1953

EVIDENCE:

- `work/5/19/2026-05-19-advisory-disabled-followup-reason-matrix-replay.md`
- `verify/5/19/2026-05-19-advisory-disabled-followup-action-branch-coverage.md`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `watcher_prompt_assembly.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`

REJECTED:

- advisory_request: `ADVISORY_ENABLED=false` 조건이므로 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- Gemini/advisory follow-up: 이번 prompt는 `ADVISORY_ENABLED=false`이고 callable Gemini lane이 없어 council evidence로 local convergence를 수행했습니다.
- operator_request: 안전, 승인, truth-sync repair, auth/credential, merge/release/destructive publication 경계가 현재 local work를 막지 않습니다.
- publish work: publication backlog는 held 상태이며 implement lane에 넘길 수 없습니다.
- another reason-matrix micro-slice: latest work already covers the remaining ordinary advisory follow-up reason values.
- docs-only follow-up: same-day docs-only loops are already numerous, and latest evidence points to a bounded runtime aggregate guard instead of another docs-only micro-slice.

## 다음 상태

- `.pipeline/implement_handoff.md#1953`로 현재 dirty runtime automation bundle의 focused aggregate guard를 넘기는 것이 가장 작은 같은-family current-risk reduction입니다.
- 다음 slice는 새 source/test를 더 추가하기보다 현재 변경된 `automation_health`, supervisor status surface, watcher prompt/retriage replay가 함께 통과하는지 compile과 focused unit 묶음으로 확인하고 `/work` closeout을 남겨야 합니다. 실패할 때만 해당 파일에 최소 수정합니다.
