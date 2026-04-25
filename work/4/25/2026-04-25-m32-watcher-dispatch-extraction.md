# 2026-04-25 M32 watcher dispatch extraction

## 변경 파일
- `watcher_core.py`
- `watcher_dispatch.py`
- `work/4/25/2026-04-25-m32-watcher-dispatch-extraction.md`

## 사용 skill
- `security-gate`: tmux pane dispatch와 shell 실행 경계가 이동되는 변경이라 기존 로컬 runtime control 범위와 위험을 확인했습니다.
- `work-log-closeout`: 구현 파일, 검증 결과, 남은 리스크를 `/work` closeout으로 기록하기 위해 사용했습니다.

## 변경 이유
- M32 Axis 1 handoff에 따라 `watcher_core.py`에 남아 있던 tmux dispatch/window helper 그룹을 기존 `watcher_dispatch.py`로 옮겨 watcher core의 구조적 책임을 줄였습니다.

## 핵심 변경
- `_DISPATCH_LOCKS_GUARD`, `_DISPATCH_LOCKS`, `_DISPATCH_LOCK_TIMEOUT_SEC`와 `_wait_for_input_ready`, `_wait_for_dispatch_window`, `_is_pane_dead`, `_respawn_pane`, `_clear_prompt_input_line`, `_dispatch_lock_for`, `tmux_send_keys`, `_dispatch_codex`, `_dispatch_claude`, `_dispatch_gemini` 구현을 `watcher_dispatch.py`로 이동했습니다.
- `watcher_core.py`는 위 심볼을 `watcher_dispatch`에서 import해 기존 `watcher_core.tmux_send_keys`, `watcher_core._is_pane_dead` 등 re-export 계약을 유지합니다.
- 기존 테스트의 `mock.patch("watcher_core...")` 계약이 유지되도록 `watcher_dispatch.py`에서 `watcher_core` re-export alias를 호환 조회하는 경로를 추가했습니다.
- `_prompt_cleanup_list`, `_cleanup_prompt_files`, `atexit.register(...)`, `_write_prompt_file`, `_normalize_prompt_text`는 `watcher_core.py`에 그대로 유지했습니다.
- 보안 경계: tmux shell dispatch 동작은 기존과 같고, 새 권한 상승/외부 네트워크/파일 쓰기 범위는 추가하지 않았습니다.

## 검증
- `python3 -m py_compile watcher_core.py watcher_dispatch.py`
  - 통과, 출력 없음.
- `python3 -m unittest tests.test_watcher_core.CodexDispatchConfirmationTest -v`
  - `Ran 12 tests` / `OK`.
- `python3 -m unittest tests/test_watcher_core.py tests/test_watcher_signals.py tests/test_controller_monitor.py -v 2>&1 | tail -5`
  - `Ran 216 tests in 9.111s` / `OK`.
- `grep -n "^def _dispatch_codex\|^def tmux_send_keys\|^def _dispatch_lock_for\|^def _wait_for_dispatch_window\|^def _is_pane_dead\|^def _clear_prompt_input_line" watcher_core.py`
  - 매치 없음.
- `git diff --check -- watcher_core.py watcher_dispatch.py`
  - 통과, 출력 없음.

## 남은 리스크
- 이번 변경은 dispatch 구현 위치를 바꾸는 구조 이동입니다. 런타임 tmux 실제 전송 동작은 unit mock 중심으로 확인했으며, 실제 tmux pane live dispatch는 별도 운영 환경에서 자연 사용 중 확인이 필요합니다.
- `watcher_dispatch.py`가 `watcher_core` re-export patch 호환을 위해 런타임에 `sys.modules["watcher_core"]`를 선택적으로 조회합니다. 이는 기존 테스트/호출자 계약 보존용이며, 독립 사용 시에는 `watcher_dispatch.py` 내부 구현을 그대로 사용합니다.
