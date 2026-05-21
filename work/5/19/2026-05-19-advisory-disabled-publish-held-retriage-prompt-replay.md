# 2026-05-19 advisory disabled publish held retriage prompt replay

## 변경 파일

- `tests/test_watcher_core.py`
- `work/5/19/2026-05-19-advisory-disabled-publish-held-retriage-prompt-replay.md`

## 사용 skill

- `work-log-closeout`: handoff 수행 결과, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1956`이 advisory-disabled profile에서 `commit_push_bundle_authorization + internal_only + release_gate` operator retriage prompt가 publication을 보류하고 local-only control로 수렴하는지 focused replay로 고정하라고 지시했습니다.
- 기존 watcher prompt test는 commit/push retriage의 publish 보류 문구와 source reason 보존은 확인했지만, `ADVISORY_DISABLED: true` 상태에서 advisory option이 빠지는 현재 incident를 직접 고정하지 않았습니다.
- implement lane 지시에 따라 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release는 수행하지 않았고 다음 slice도 선택하지 않았습니다.

## 핵심 변경

- `WatcherPromptAssemblyTest.test_operator_retriage_prompt_advisory_disabled_commit_push_holds_publication_locally`를 추가했습니다.
- 새 replay는 Codex-only advisory-disabled active profile에서 `commit_push_bundle_authorization`, `operator_policy=internal_only`, `decision_class=release_gate`, `publish_held=true` marker로 operator retriage prompt를 생성합니다.
- prompt가 `ADVISORY_DISABLED: true`, `PUBLISH_HELD: true`, publish backlog hold 문구, publication 명령 금지 문구, implement-lane commit/push 금지 문구를 포함하는지 확인합니다.
- prompt의 next control 후보가 `.pipeline/implement_handoff.md [implement] | .pipeline/operator_request.md [needs_operator]`로 제한되고 `.pipeline/advisory_request.md [request_open]`를 포함하지 않는지 확인합니다.
- `watcher_prompt_assembly.py`는 이번 라운드에서 수정하지 않았습니다.

## 검증

- `python3 -m py_compile watcher_prompt_assembly.py tests/test_watcher_core.py`
  - 출력 없이 통과했습니다.
- `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_advisory_disabled_commit_push_holds_publication_locally tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_advisory_disabled_returns_to_verify`
  - `Ran 3 tests in 0.021s`
  - `OK`
- `git diff --check -- watcher_prompt_assembly.py tests/test_watcher_core.py work/5/19/2026-05-19-advisory-disabled-publish-held-retriage-prompt-replay.md .pipeline/implement_handoff.md`
  - 출력 없이 통과했습니다.
- `git status --short -- watcher_prompt_assembly.py tests/test_watcher_core.py work/5/19/2026-05-19-advisory-disabled-publish-held-retriage-prompt-replay.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `tests/test_watcher_core.py` 수정과 새 `/work` closeout이 표시됐습니다.
  - `watcher_prompt_assembly.py`는 이전 라운드의 기존 dirty 상태로 함께 표시됐고, 이번 handoff에서는 수정하지 않았습니다.

## 남은 리스크

- 이번 handoff는 focused watcher prompt replay라 broader unittest, Playwright/E2E, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- 이번 라운드에서는 commit, push, branch/PR publication, PR creation/reuse/update, PR merge, release, external publication을 수행하지 않았습니다.
