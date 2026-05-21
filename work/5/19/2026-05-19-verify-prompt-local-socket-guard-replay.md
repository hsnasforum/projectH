# 2026-05-19 verify prompt local socket guard replay

## 변경 파일

- `tests/test_watcher_core.py`
- `work/5/19/2026-05-19-verify-prompt-local-socket-guard-replay.md`
- `watcher_prompt_assembly.py`는 handoff의 확인 대상이었지만 이번 라운드에서 직접 수정하지 않았습니다. 기존 dirty diff는 그대로 두었습니다.

## 사용 skill

- `work-log-closeout`: handoff #1990의 실제 변경 파일, 실행한 검증, publication-held 경계, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1990`가 verify prompt의 local socket guard 지시를 non-socket unit replay로 고정하라고 지시했습니다.
- 최신 `/work`는 `make controller-test`가 controller webServer socket startup에서 `PermissionError: [Errno 1] Operation not permitted`로 environment-held 되어 `local_socket_guard_auto_held`로 기록됐다고 남겼습니다.
- 같은 full-smoke/release gate handoff를 반복하거나 socket hold를 operator stop/release-ready evidence로 바꾸지 않도록 prompt contract를 테스트로 보호해야 했습니다.
- publication은 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.

## 핵심 변경

- `WatcherPromptAssemblyTest`에 `test_verify_prompt_preserves_local_socket_guard_rules`를 추가했습니다.
- 새 테스트는 advisory disabled verify prompt를 생성하고, next control options가 implement/operator로만 제한되는지 확인합니다.
- controller Playwright webServer socket permission denial 규칙이 `/verify`의 `local_socket_guard_auto_held` 기록, operator request 재작성 금지, controller-smoke/release readiness claim 금지, safe local implement handoff 선택을 포함하는지 검증합니다.
- local full-smoke external-check evidence의 `local_socket_guard_auto_held` 규칙이 같은 full-smoke handoff 재발행 금지, release/full-smoke pass claim 금지, `/verify` 기록, next safe local slice 선택을 포함하는지 검증합니다.
- prompt source contract는 이미 요구 문구를 포함하고 있어 `watcher_prompt_assembly.py`는 수정하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `1e7fe5460f21b9d6af4860c2a370dd9e81932ea64ca9aa6bf832bcc0879b259a`와 일치했습니다.
- `python3 -m py_compile watcher_prompt_assembly.py tests/test_watcher_core.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest`
  - 결과: PASS. `Ran 20 tests in 0.472s`, `OK`.
- `git diff --check -- watcher_prompt_assembly.py tests/test_watcher_core.py work/5/19/2026-05-19-verify-prompt-local-socket-guard-replay.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- 이번 라운드는 non-socket prompt replay입니다. `make e2e-test`, `make controller-test`, Playwright, controller startup, local socket probe, live runtime, tmux, long soak는 실행하지 않았습니다.
- `make controller-test`는 최신 `/work` 기준 local socket permission hold로 남아 있으므로 release-ready, full-smoke-pass, publication-ready, merge-ready 상태를 주장하지 않습니다.
- 기존 dirty tree에는 handoff 범위 밖 source/test/docs 변경과 다수 `/work`/`/verify` 기록이 남아 있습니다. 이번 라운드는 unrelated dirty 변경을 되돌리거나 정리하지 않았습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, `/verify`, 다음 handoff는 작성하지 않았습니다.
