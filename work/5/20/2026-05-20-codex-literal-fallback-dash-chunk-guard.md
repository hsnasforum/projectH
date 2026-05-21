# 2026-05-20 codex literal fallback dash chunk guard

## 변경 파일

- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `work/5/20/2026-05-20-codex-literal-fallback-dash-chunk-guard.md`

## 사용 skill

- `round-handoff`: #1991 closeout 검증 중 runtime dispatch failure loop의 직접
  원인을 확인했습니다.
- `next-slice-triage`: 같은 incident family의 가장 작은 local repair를
  `watcher_dispatch.py` literal fallback 경계로 좁혔습니다.
- `security-gate`: tmux shell dispatch 호출이 새 권한이나 publication 동작을
  만들지 않는지 확인했습니다.
- `finalize-lite`: 실제 변경 파일, 검증, doc-sync 필요 여부, 남은 리스크를
  정리했습니다.
- `work-log-closeout`: 구현 라운드 closeout을 한국어 기록으로 남겼습니다.

## 변경 이유

- live watcher log에서 Codex verify prompt literal fallback이 tmux
  `send-keys` 호출 중 `invalid flag -`로 실패했습니다.
- `_send_literal_text_to_pane()`는 chunk를 tmux 인자로 직접 넘기는데, chunk가
  `-`로 시작하면 tmux가 이를 literal text가 아니라 옵션처럼 해석할 수
  있었습니다.
- 이 실패는 `codex_verify_dispatch_failure_loop`를 반복시켜 runtime을
  `needs_operator`로 degraded 시키는 직접 원인이었습니다.

## 핵심 변경

- `watcher_dispatch._send_literal_text_to_pane()`의 tmux 호출에 `--` option
  terminator를 추가했습니다.
- literal fallback chunk가 `-`로 시작해도 tmux 옵션으로 해석되지 않고
  literal text 인자로 남도록 했습니다.
- `CodexDispatchConfirmationTest`에 dash-leading chunk 회귀 테스트를
  추가했습니다.
- 자동 승인, 파일 삭제/덮어쓰기, 외부 publication, merge/release 동작은
  추가하지 않았습니다.

## 검증

- `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.VerifyPendingBackoffTest`
  - 결과: PASS. `Ran 32 tests in 6.533s`, `OK`.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- live tmux runtime restart, controller startup, local socket probe,
  `make controller-test`, Playwright, `make e2e-test`, long soak는 실행하지
  않았습니다.
- 현재 떠 있는 runtime이 수정된 `watcher_dispatch.py`를 아직 로드하지
  않았을 수 있으므로 status surface는 재시작 또는 self-reload 전까지
  기존 degraded 상태를 계속 보일 수 있습니다.
- publication remains held. commit, push, branch/PR publication,
  PR creation/reuse/update, merge, release, external publication은 수행하지
  않았습니다.
