# 2026-05-19 operator retriage source reason prompt unit replay

## 변경 파일

- `tests/test_watcher_core.py`
- `work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md`
- `watcher_prompt_assembly.py`
  - 이전 slice에서 수정된 source fix가 현재 dirty 상태로 남아 있으며, 이번 라운드에서는 추가 수정하지 않았습니다.

## 사용 skill

- `work-log-closeout`: handoff 수행 결과, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1949`가 `WatcherPromptAssembler.format_operator_retriage_prompt(...)`의 `source_reason` 보존 계약을 직접 고정하는 prompt-helper unit replay를 추가하라고 지시했습니다.
- 이전 slice에서 `pr_merge_completed` recovery prompt의 `REASON:` header 보존 문제가 수정됐으므로, 이번 라운드는 해당 helper 계약을 test-only로 보호하는 범위였습니다.
- `PUBLISH_HELD=true`와 `ADVISORY_ENABLED=false` 조건에 따라 commit, push, branch publication, PR creation/reuse/update, PR merge, release는 수행하지 않았습니다.

## 핵심 변경

- `tests/test_watcher_core.py`의 `WatcherPromptAssemblyTest`에 `test_operator_retriage_prompt_preserves_source_reason`을 추가했습니다.
- 새 test는 `reason=operator_retriage_no_next_control`, `source_reason=pr_merge_completed`, `publish_held=True` marker를 직접 렌더링합니다.
- 새 test는 prompt가 `REASON: pr_merge_completed`, `ADVISORY_DISABLED: false`, `PUBLISH_HELD: true`를 포함하는지 확인합니다.
- 새 test는 `REASON: operator_retriage_no_next_control`이 렌더링되지 않는지도 확인합니다.
- 새 test가 통과해 `watcher_prompt_assembly.py`에는 이번 라운드 추가 source 변경을 하지 않았습니다.

## 검증

- `python3 -m py_compile watcher_prompt_assembly.py tests/test_watcher_core.py`
  - 출력 없이 통과했습니다.
- `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_preserves_source_reason tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify`
  - `Ran 2 tests in 0.022s`
  - `OK`
- `git diff --check -- tests/test_watcher_core.py watcher_prompt_assembly.py work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- `git diff --check --no-index /dev/null work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md`
  - 출력 없음. 새 untracked 파일과 `/dev/null` 비교라 exit code는 `1`이지만 whitespace error는 없었습니다.
- `git status --short -- tests/test_watcher_core.py watcher_prompt_assembly.py work/5/19/2026-05-19-operator-retriage-source-reason-prompt-unit-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `tests/test_watcher_core.py`, `watcher_prompt_assembly.py` 수정과 새 `/work` closeout만 표시됐습니다.

## 남은 리스크

- `make e2e-test`, Playwright rerun, runtime live start/stop/restart, tmux control, long soak는 이번 focused prompt-helper unit replay 범위가 아니어서 실행하지 않았습니다.
- 이번 라운드에서는 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release, external publication을 수행하지 않았습니다.
