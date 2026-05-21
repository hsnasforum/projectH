# 2026-05-19 PR127 pr merge recovery advisory disabled replay

## 변경 파일

- `tests/test_watcher_core.py`
- `watcher_prompt_assembly.py`
- `work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md`

## 사용 skill

- `work-log-closeout`: handoff 수행 결과, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1948`이 `pr_merge_completed` recovery 뒤 `operator_retriage_no_next_control`이 advisory-disabled profile에서 verify follow-up으로 되돌아오는지 focused watcher replay로 고정하라고 지시했습니다.
- 같은 PR127 post-merge local-guard family가 docs-only micro-loop로 반복되지 않도록, 문서화한 운영 규칙을 실제 watcher replay로 보호해야 했습니다.
- `PUBLISH_HELD=true`와 `ADVISORY_ENABLED=false` 조건에 따라 commit, push, branch publication, PR creation/reuse/update, PR merge, release는 수행하지 않았습니다.

## 핵심 변경

- `tests/test_watcher_core.py`에 `test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify` replay를 추가했습니다.
- 새 replay는 completed `pr_merge_gate`가 `pr_merge_completed`로 recovery된 뒤 advisory-disabled 환경에서 `.pipeline/advisory_request.md`를 만들지 않고 verify follow-up으로 되돌아오는지 확인합니다.
- 새 replay는 payload의 `advisory_disabled`, `publish_held`와 turn-state reason `verify_followup_no_next_control`을 검증합니다.
- `watcher_prompt_assembly.py`에서 operator retriage prompt의 `REASON` header가 `source_reason`을 보존하도록 조정했습니다.
- source fix 전 새 replay가 prompt에 `pr_merge_completed`가 빠지는 문제를 잡았고, source fix 뒤 replay가 통과했습니다.

## 검증

- `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py tests/test_watcher_core.py`
  - 출력 없이 통과했습니다.
- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_pr_merge_recovery_no_next_control_promotes_to_advisory_request tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_operator_retriage_no_next_control_advisory_disabled_returns_to_verify tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify`
  - 실패했습니다. 원인은 behavior failure가 아니라 handoff의 selector가 현재 파일 구조와 맞지 않는 점입니다.
  - 세 method는 `WatcherDispatchQueueControlMismatchTest`가 아니라 `RollingSignalTransitionTest`에 있습니다.
- `python3 -m unittest -v tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_promotes_to_advisory_request tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_advisory_disabled_returns_to_verify tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify`
  - source fix 전에는 새 replay가 `pr_merge_completed` prompt 누락을 잡아 실패했습니다.
  - source fix 뒤 `Ran 3 tests in 0.047s`, `OK`로 통과했습니다.
- `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner tests.test_watcher_core.WatcherPromptAssemblyTest.test_pr_creation_gate_routes_to_verify_owner_publish_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_legacy_milestone_commit_push_doc_sync_operator_request_routes_to_verify_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_b1_dirty_tree_release_gate_operator_request_routes_to_verify_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_pr_merge_gate_internal_only_routes_to_verify_followup_backlog tests.test_watcher_core.WatcherPromptAssemblyTest.test_compound_milestone_pr_merge_gate_routes_to_verify_followup_backlog`
  - `Ran 6 tests in 0.251s`, `OK`로 통과했습니다.
- `git diff --check -- tests/test_watcher_core.py watcher_core.py watcher_prompt_assembly.py work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- `git diff --check --no-index /dev/null work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- `git status --short -- tests/test_watcher_core.py watcher_core.py watcher_prompt_assembly.py work/5/19/2026-05-19-pr127-pr-merge-recovery-advisory-disabled-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `tests/test_watcher_core.py`, `watcher_prompt_assembly.py` 수정과 새 `/work` closeout만 표시됐습니다.

## 남은 리스크

- handoff의 unittest selector는 현재 test class 배치와 맞지 않아 그대로는 통과하지 않습니다. 실제 관련 test class인 `RollingSignalTransitionTest` selector로 동일한 세 replay를 검증했습니다.
- `make e2e-test`, Playwright rerun, runtime live start/stop/restart, tmux control, long soak는 이번 focused watcher replay 범위가 아니어서 실행하지 않았습니다.
- 이번 라운드에서는 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release, external publication을 수행하지 않았습니다.
