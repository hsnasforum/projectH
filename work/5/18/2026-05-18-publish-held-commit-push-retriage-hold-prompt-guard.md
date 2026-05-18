# 2026-05-18 publish held commit push retriage hold prompt guard

## 변경 파일

- `watcher_prompt_assembly.py`
- `tests/test_watcher_core.py`
- `work/5/18/2026-05-18-publish-held-commit-push-retriage-hold-prompt-guard.md`

## 사용 skill

- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 실행한 검사, 남은 리스크를 표준 `/work` 형식으로 기록하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1915` handoff는 publication을 held 상태로 유지하면서, operator retriage prompt가 canonical `commit_push_bundle_authorization + internal_only + release_gate` publish backlog도 기본 hold 대상으로 명시하게 하라고 지시했습니다.
- 직전 retriage 흐름에서 `commit_push_bundle_authorization` operator stop이 반복됐고, implement lane은 commit, push, branch/PR publication, PR creation/reuse, merge, release를 수행할 수 없으므로 prompt/test contract를 더 명확히 고정했습니다.

## 핵심 변경

- `DEFAULT_OPERATOR_RETRIAGE_PROMPT`의 publish-held 출력 규칙에 `commit_push_bundle_authorization + internal_only + release_gate` canonical metadata를 명시했습니다.
- `WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner`가 canonical commit/push release-gate metadata를 직접 확인하도록 보강했습니다.
- `WatcherPromptAssemblyTest.test_legacy_milestone_commit_push_doc_sync_operator_request_routes_to_verify_followup`가 publish backlog hold 문구를 직접 확인하도록 보강했습니다.
- 기존 dirty runtime/source/test bundle과 root instruction docs는 이번 라운드에서 추가 수정하지 않았습니다.
- publication은 계속 held 상태입니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication, readiness claim은 수행하지 않았습니다.

## 검증

- `python3 -m py_compile watcher_prompt_assembly.py watcher_core.py`
  - 통과.
- `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner tests.test_watcher_core.WatcherPromptAssemblyTest.test_legacy_milestone_commit_push_doc_sync_operator_request_routes_to_verify_followup`
  - 통과. `Ran 2 tests in 0.020s`, `OK`.
- `git diff --check -- watcher_prompt_assembly.py tests/test_watcher_core.py work/5/18/2026-05-18-publish-held-commit-push-retriage-hold-prompt-guard.md`
  - closeout 작성 후 기준 출력 없이 통과했습니다.
- `git status --short -- watcher_prompt_assembly.py tests/test_watcher_core.py work/5/18/2026-05-18-publish-held-commit-push-retriage-hold-prompt-guard.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `watcher_prompt_assembly.py`, `tests/test_watcher_core.py` modified와 새 `/work` closeout untracked만 표시했습니다.

## 남은 리스크

- 이번 라운드는 operator-retriage prompt/test guard만 다뤘습니다. 전체 watcher/runtime unittest, Playwright, `make e2e-test`, local socket/server startup, live tmux E2E, runtime start/stop, long soak는 실행하지 않았습니다.
- 기존 dirty tracked runtime/source/test bundle과 root instruction docs 변경은 여전히 dirty 상태입니다.
- `stash@{0}`는 적용/삭제/검증하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하거나 수정하지 않았습니다.
