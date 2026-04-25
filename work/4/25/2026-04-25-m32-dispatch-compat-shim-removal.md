# 2026-04-25 M32 dispatch compat shim 제거

## 변경 파일
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `work/4/25/2026-04-25-m32-dispatch-compat-shim-removal.md`

## 사용 skill
- `security-gate`: tmux pane dispatch 경로의 shell 실행 경계가 유지되는지 확인했습니다.
- `work-log-closeout`: 구현 범위, 검증 결과, 남은 리스크를 `/work` closeout으로 기록하기 위해 사용했습니다.

## 변경 이유
- M32 Axis 2 handoff에 따라 Axis 1에서 임시로 남긴 `watcher_dispatch.py` -> `watcher_core` 런타임 compat shim을 제거하고, dispatch 구현의 소유권을 `watcher_dispatch.py` 내부 직접 호출로 정리했습니다.

## 핵심 변경
- `watcher_dispatch.py`에서 `sys.modules["watcher_core"]`를 조회하던 `_watcher_core_compat`와 9개 thin wrapper를 제거했습니다.
- `_wait_for_input_ready`, `_wait_for_dispatch_window`, `tmux_send_keys`, `_dispatch_codex`, `_dispatch_claude`, `_dispatch_gemini`, `_pane_has_working_indicator` 내부 호출을 `_shared_*` 또는 같은 모듈 helper 직접 호출로 바꿨습니다.
- `WatcherDispatchQueue`의 `self._capture_pane_text` 인스턴스 속성은 변경하지 않았습니다.
- `tests/test_watcher_core.py`의 `CodexDispatchConfirmationTest` 범위 안에서 dispatch mock patch 대상을 `watcher_dispatch.*`로 정규화했습니다.
- 보안 경계: 새 권한 상승, 외부 네트워크, 승인 없는 파일 쓰기, destructive 동작은 추가하지 않았고 기존 tmux dispatch 흐름만 같은 모듈 직접 호출로 정리했습니다.

## 검증
- `python3 -m py_compile watcher_dispatch.py watcher_core.py`
  - 통과, 출력 없음.
- `python3 -m unittest tests.test_watcher_core.CodexDispatchConfirmationTest -v`
  - `Ran 12 tests` / `OK`.
- `python3 -m unittest tests/test_watcher_core.py tests/test_watcher_signals.py tests/test_controller_monitor.py -v 2>&1 | tail -5`
  - `Ran 216 tests in 9.052s` / `OK`.
- `grep -n "sys.modules\|_watcher_core_compat\|_capture_pane_text\b\|_pane_text_has_input_cursor\b" watcher_dispatch.py | grep "^[0-9]*:def "`
  - 출력 없음. 삭제 대상 def 잔존 매치 없음.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py`
  - 통과, 출력 없음.

## 남은 리스크
- 이번 변경은 테스트 mock 대상과 dispatch 내부 호출 소유권을 함께 바꾸는 정리입니다. 지정된 unit 묶음은 통과했지만 실제 tmux pane live dispatch는 운영 중 자연 사용이나 별도 live smoke에서만 확인됩니다.
- `watcher_core.py`의 re-export 심볼은 그대로 유지했습니다. 향후 별도 handoff 없이는 `watcher_core.py` 정리나 추가 테스트 범위 변경을 진행하지 않았습니다.
