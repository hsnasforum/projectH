# 2026-05-21 Codex paste fail-closed hardening

## 변경 파일

- `watcher_dispatch.py`
- `verify_fsm.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `work/5/21/2026-05-21-codex-paste-fail-closed-hardening.md`

## 사용 skill

- `security-gate`: tmux 자동 입력, dispatch 로그, operator-visible degraded 표면화가 바뀌는 작업이라 fail-closed 경계와 감사 가능성을 점검했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- Codex pane에 사용자가 직접 넣지 않은 `[Pasted Content ...]` 잔상이 남은 상태에서 watcher가 새 prompt를 자동 재주입하거나 submit retry / fallback을 타면 의도하지 않은 지시 주입처럼 보일 수 있습니다.
- 이번 변경은 자동화 성공률보다 Codex pane 입력 안전성을 우선해, stale paste 또는 stuck paste가 보이는 경로를 operator-visible incident로 멈추게 하는 fail-closed hardening입니다.

## 핵심 변경

- `watcher_dispatch.py`에서 Codex lane readiness가 `prompt_contains_pasted_content`이면 `_send_keys`를 호출하지 않고 `codex_stale_paste_blocked`와 `lane_input_deferred` 이벤트만 남기도록 바꿨습니다.
- `_dispatch_codex()`는 paste 후 첫 `Enter` 뒤에도 `[Pasted Content ...]`가 남으면 best-effort cleanup 후 `False`를 반환하며, 자동 `C-j` retry와 literal fallback 호출을 제거했습니다.
- `verify_fsm.py`는 Codex verify dispatch 실패 snapshot 또는 현재 pane에 pasted-content marker가 있으면 backoff 재시도 없이 `dispatch_failed_submit` / `codex_verify_dispatch_failure_loop`로 degraded 처리하고 verify lease를 release합니다.
- 새 reason code를 만들지 않고 기존 `codex_verify_dispatch_failure_loop`를 재사용해 `operator_autonomy` / `automation_health`의 operator-required 표면을 유지했습니다.
- `tests/test_watcher_core.py`는 pre-existing paste block, stuck paste after first submit, verify pending backoff의 fail-closed 기대값을 보강했습니다.
- `.pipeline/README.md`에 Codex pasted-content fail-closed 계약과 operator-visible incident 표면화를 문서화했습니다.

## 검증

- `python3 -m py_compile watcher_dispatch.py verify_fsm.py tests/test_watcher_core.py`
  - 통과했습니다.
- `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.VerifyPendingBackoffTest`
  - `Ran 33 tests in 3.991s` / `OK`.
- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest`
  - `Ran 13 tests in 0.032s` / `OK`.
- `git diff --check -- watcher_dispatch.py verify_fsm.py tests/test_watcher_core.py .pipeline/README.md work/5/21`
  - closeout 작성 후 재실행해 통과를 확인했습니다.

## 남은 리스크

- 전체 unittest, Playwright, controller smoke, 장시간 soak는 실행하지 않았습니다. 변경 범위가 watcher/verify dispatch fail-closed와 관련 unit coverage로 제한되어 targeted 검증만 수행했습니다.
- literal fallback helper 자체는 기존 직접 테스트와 수동/레거시 호출 가능성을 위해 남겼지만, 자동 Codex dispatch 경로에서는 호출하지 않도록 분리했습니다.
- 이번 slice는 `controller/server.py`의 수동 `/api/runtime/send-input`, Codex TUI 자체, `.codex` 상태 파일 정리를 건드리지 않았습니다.
- 작업 시작 시점부터 worktree에는 여러 기존 dirty/untracked 파일이 있었으며, 이번 기록은 위 변경 파일 범위만 대상으로 합니다.
- commit, push, PR publish, merge는 수행하지 않았습니다.
