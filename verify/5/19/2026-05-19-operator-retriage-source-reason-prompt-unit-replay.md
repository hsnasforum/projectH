# 2026-05-19 operator retriage source reason prompt unit replay verify

STATUS: verified

## 대상

- 최신 `/work`: `work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md`
- 이전 기준 `/verify`: `verify/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md`
- 목적: operator retriage `source_reason` prompt helper unit replay의 진실성 확인

## 결론

- 최신 `/work`의 `## 변경 파일`은 `tests/test_watcher_core.py`, 새 `/work` closeout, 그리고 이전 slice의 source fix가 dirty 상태로 남은 `watcher_prompt_assembly.py`를 기록하며 현재 scoped status와 일치합니다.
- `tests/test_watcher_core.py`에는 `WatcherPromptAssemblyTest.test_operator_retriage_prompt_preserves_source_reason`이 추가됐고, `source_reason=pr_merge_completed`가 `REASON: pr_merge_completed`로 렌더링되는 직접 helper 계약을 검증합니다.
- `watcher_prompt_assembly.py`의 `source_reason` 보존 fix는 이전 slice에서 들어온 상태 그대로이며, 최신 `/work`가 말한 대로 이번 unit replay 라운드에서는 추가 source 변경이 없었습니다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=attention`, `automation_next_action=advisory_followup`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 제공됐습니다. advisory는 비활성화되어 있으므로 `.pipeline/advisory_request.md`를 쓰지 않고, 이 dispatcher surface mismatch는 다음 local replay로 줄이는 것이 맞습니다.
- lane-local runtime/status/tmux 명령은 사용하지 않았습니다.

## 실행한 검증

- PASS: `python3 -m py_compile watcher_prompt_assembly.py tests/test_watcher_core.py`
  - 출력 없이 통과했습니다.
- PASS: `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_preserves_source_reason tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify`
  - `Ran 2 tests in 0.020s`
  - `OK`
- PASS: `git diff --check -- tests/test_watcher_core.py watcher_prompt_assembly.py work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- CHECK: `git diff --check --no-index /dev/null work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- CHECK: `git status --short -- tests/test_watcher_core.py watcher_prompt_assembly.py work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `tests/test_watcher_core.py`, `watcher_prompt_assembly.py` 수정과 새 `/work` closeout만 표시됐습니다.
- CHECK: `git status --short`
  - 위 변경 외에 이전 PR127 docs/runbook 변경과 이전 `/work`·`/verify` 기록들이 함께 남아 있음을 확인했습니다.

## 실행하지 않은 검증

- `make e2e-test`, Playwright rerun, runtime live start/stop/restart, tmux control, long soak는 이번 prompt helper unit replay 검증 범위가 아니어서 실행하지 않았습니다.
- lane-local `status --json`, `doctor --json`, `tmux` 명령은 `RUNTIME_STATUS_AT_DISPATCH`가 제공됐고 해당 surface가 authoritative이므로 실행하지 않았습니다.

## Council 결정

COUNCIL_DECISION: implement
REASON_CODE: advisory_disabled_runtime_next_action_surface_replay
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 1950

EVIDENCE:

- `work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md`
- `verify/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md`
- `RUNTIME_STATUS_AT_DISPATCH`: `ADVISORY_ENABLED=false` prompt context, but `automation_next_action=advisory_followup`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`

REJECTED:

- advisory_request: `ADVISORY_ENABLED=false` 조건이므로 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- operator_request: 안전, 승인, truth-sync repair, auth/credential, merge/release/destructive publication 경계가 현재 local work를 막지 않습니다.
- another prompt-helper micro-test: latest unit replay already protects `source_reason` rendering directly.
- commit/push/PR/merge/release: publication backlog는 held 상태이며 implement lane에 넘길 수 없습니다.

## 다음 상태

- `.pipeline/implement_handoff.md#1950`로 advisory-disabled runtime status surface replay를 넘기는 것이 현재 가장 작은 같은-family current-risk reduction입니다.
- 다음 slice는 advisory가 비활성인 profile에서 runtime status가 `advisory_followup`을 다음 action으로 표면화하지 않도록 focused automation-health/supervisor test와 필요한 최소 source fix를 다뤄야 합니다.
