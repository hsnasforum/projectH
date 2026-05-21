# 2026-05-19 PR127 pr merge recovery advisory disabled replay verify

STATUS: verified

## 대상

- 최신 `/work`: `work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md`
- 이전 기준 `/verify`: `verify/5/19/2026-05-19-pr127-post-merge-truth-docs-bundle.md`
- 목적: PR merge recovery advisory-disabled replay 구현의 진실성 확인

## 결론

- 최신 `/work`의 `## 변경 파일`은 `tests/test_watcher_core.py`, `watcher_prompt_assembly.py`, 새 `/work` closeout이며 현재 scoped status와 일치합니다.
- `tests/test_watcher_core.py`에는 `RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify`가 추가됐고, completed `pr_merge_gate` recovery가 advisory-disabled profile에서 verify follow-up으로 되돌아오는 경로를 검증합니다.
- `watcher_prompt_assembly.py`는 operator retriage prompt의 `REASON` header에 이미 계산한 `source_reason` 우선 reason을 쓰도록 바뀌었습니다. 이 변경으로 `pr_merge_completed`가 prompt에 보존됩니다.
- handoff에 적힌 `WatcherDispatchQueueControlMismatchTest.*` unittest selector는 현재 파일 구조와 맞지 않습니다. `rg` 확인 결과 관련 세 method는 `RollingSignalTransitionTest`에 있습니다.
- 실제 관련 selector와 prompt helper selector는 모두 통과했습니다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=ok`, `automation_next_action=continue`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 제공됐으므로 lane-local runtime/tmux 명령은 사용하지 않았습니다.

## 실행한 검증

- PASS: `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py tests/test_watcher_core.py`
  - 출력 없이 통과했습니다.
- PASS: `python3 -m unittest -v tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_promotes_to_advisory_request tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_advisory_disabled_returns_to_verify tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify`
  - `Ran 3 tests in 0.069s`
  - `OK`
- PASS: `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner tests.test_watcher_core.WatcherPromptAssemblyTest.test_pr_creation_gate_routes_to_verify_owner_publish_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_legacy_milestone_commit_push_doc_sync_operator_request_routes_to_verify_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_b1_dirty_tree_release_gate_operator_request_routes_to_verify_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_pr_merge_gate_internal_only_routes_to_verify_followup_backlog tests.test_watcher_core.WatcherPromptAssemblyTest.test_compound_milestone_pr_merge_gate_routes_to_verify_followup_backlog`
  - `Ran 6 tests in 0.256s`
  - `OK`
- PASS: `git diff --check -- tests/test_watcher_core.py watcher_core.py watcher_prompt_assembly.py work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- CHECK: `git diff --check --no-index /dev/null work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- CHECK: `git status --short -- tests/test_watcher_core.py watcher_core.py watcher_prompt_assembly.py work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `tests/test_watcher_core.py`, `watcher_prompt_assembly.py` 수정과 새 `/work` closeout만 표시됐습니다.
- CHECK: `rg -n "class WatcherDispatchQueueControlMismatchTest|class RollingSignalTransitionTest|def test_pr_merge_recovery_no_next_control_promotes_to_advisory_request|def test_operator_retriage_no_next_control_advisory_disabled_returns_to_verify|def test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify" tests/test_watcher_core.py`
  - 관련 세 method가 `RollingSignalTransitionTest` 아래에 있음을 확인했습니다.

## 실행하지 않은 검증

- handoff의 stale selector인 `tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.*` 세 tests는 이번 verify에서 재실행하지 않았습니다.
- 이유: 최신 `/work`가 이미 해당 selector mismatch를 기록했고, `rg`와 실제 related selector 재실행으로 현재 truth를 확인했습니다.
- `make e2e-test`, Playwright rerun, runtime live start/stop/restart, tmux control, long soak는 이번 watcher prompt/test 변경 범위가 아니어서 실행하지 않았습니다.

## Council 결정

COUNCIL_DECISION: implement
REASON_CODE: operator_retriage_source_reason_prompt_unit_replay
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 1949

EVIDENCE:

- `work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md`
- `verify/5/19/2026-05-19-pr127-post-merge-truth-docs-bundle.md`
- `watcher_prompt_assembly.py`
- `tests/test_watcher_core.py`

REJECTED:

- advisory_request: `ADVISORY_ENABLED=false` 조건이므로 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- operator_request: 안전, 승인, truth-sync repair, auth/credential, merge/release/destructive publication 경계가 현재 local work를 막지 않습니다.
- stale selector class reshuffle: handoff selector mismatch를 맞추기 위한 class 이동은 shipped runtime contract 보호가 아니라 test organization churn입니다.
- commit/push/PR/merge/release: publication backlog는 held 상태이며 implement lane에 넘길 수 없습니다.

## 다음 상태

- `.pipeline/implement_handoff.md#1949`로 prompt helper 단위 replay를 추가하는 것이 현재 가장 작은 같은-family current-risk reduction입니다.
- 다음 slice는 `WatcherPromptAssembler.format_operator_retriage_prompt(...)`가 `source_reason`을 `REASON` header에 보존하는 계약을 직접 고정해야 합니다.
