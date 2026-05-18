# 2026-05-18 publish held codex dispatch fallback unit guard

## 변경 파일

- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `work/5/18/2026-05-18-publish-held-codex-dispatch-fallback-unit-guard.md`

## 사용 skill

- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 실행한 검사, 남은 리스크를 표준 `/work` 형식으로 기록하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1912` handoff는 publication을 held 상태로 유지하면서, 기존 dirty runtime bundle 안의 Codex literal fallback dispatch 경로를 별도 focused unit guard로 보강하라고 지시했습니다.
- 기존 테스트는 pasted prompt가 남을 때 fallback이 호출되는지까지 확인했지만, literal JSON wrapper 보존, stale transcript 오탐 방지, submit retry 실패 후 cleanup 경로는 직접 보호하지 않았습니다.

## 핵심 변경

- `tests/test_watcher_core.py`의 `CodexDispatchConfirmationTest`에 literal fallback 관련 테스트 3개를 추가했습니다.
- `_codex_literal_fallback_prompt`가 전체 instruction body를 JSON string으로 감싸고 newline escape와 NUL 제거를 보존하는지 확인했습니다.
- `_text_has_codex_literal_fallback_prompt`가 실제 입력 프롬프트 라인의 fallback prompt는 감지하되, 입력 커서 없는 과거 transcript 텍스트는 stuck prompt로 오인하지 않는지 확인했습니다.
- `_dispatch_codex_literal_fallback`이 Enter/C-m submit retry 후에도 fallback prompt가 남으면 cleanup 경로를 실행하고 false로 끝나는지 확인했습니다.
- `watcher_dispatch.py`의 literal fallback prompt 감지를 prefix 앞 120자 임의 검색에서 prefix가 붙은 실제 input prompt line 확인으로 좁혔습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication, readiness claim은 수행하지 않았고 publication은 계속 held 상태입니다.

## 검증

- `python3 -m py_compile watcher_dispatch.py`
  - 통과.
- `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest`
  - 통과. `Ran 19 tests in 6.423s`, `OK`.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py`
  - closeout 작성 전 기준 출력 없이 통과했습니다.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py work/5/18/2026-05-18-publish-held-codex-dispatch-fallback-unit-guard.md`
  - closeout 작성 후 기준 출력 없이 통과했습니다.
- `git status --short -- watcher_dispatch.py tests/test_watcher_core.py work/5/18/2026-05-18-publish-held-codex-dispatch-fallback-unit-guard.md .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - `tests/test_watcher_core.py`, `watcher_dispatch.py` modified와 새 `/work` closeout untracked만 표시했습니다.

## 남은 리스크

- 이번 라운드는 handoff 범위대로 `watcher_dispatch.py`와 `tests/test_watcher_core.py`의 Codex dispatch fallback unit guard만 다뤘습니다.
- 전체 watcher/runtime unittest, Playwright, `make e2e-test`, local socket/server startup, live tmux E2E, long soak는 실행하지 않았습니다.
- 기존 dirty tracked runtime/source/test bundle의 다른 파일들은 이번 라운드에서 수정하지 않았습니다.
- `stash@{0}`는 적용/삭제/검증하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하거나 수정하지 않았습니다.
