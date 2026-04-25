STATUS: verified
CONTROL_SEQ: 158
BASED_ON_WORK: work/4/25/2026-04-25-m32-watcher-dispatch-extraction.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 158 (M32 Axis 2 direction)

---

## M32 Axis 1: watcher_core dispatch helpers → watcher_dispatch.py

### Verdict

PASS. dispatch/tmux helper 그룹이 `watcher_dispatch.py`로 이동했고 216 unit tests 전체 통과.

### Checks Run

- `python3 -m py_compile watcher_core.py watcher_dispatch.py` → OK (출력 없음)
- `python3 -m unittest tests/test_watcher_core.py tests/test_watcher_signals.py tests/test_controller_monitor.py -v 2>&1 | tail -5` → `Ran 216 tests in 9.138s` `OK`
- `grep -n "^def _dispatch_codex|^def tmux_send_keys|^def _dispatch_lock_for|..." watcher_core.py` → exit 1 (매치 없음)
- `grep -n "^from watcher_dispatch import" watcher_core.py` → `128:from watcher_dispatch import (` 확인
- `git diff --check -- watcher_core.py watcher_dispatch.py` → exit 0

### Implementation Review

work 노트 기술과 일치:
- `watcher_dispatch.py`: `_DISPATCH_LOCKS_GUARD/LOCKS/TIMEOUT_SEC` 상수 + 11개 함수 추가됨
- `watcher_core.py:128` → `from watcher_dispatch import (...)` 블록으로 교체
- `_prompt_cleanup_list`, `_cleanup_prompt_files`, `_write_prompt_file`, `_normalize_prompt_text` watcher_core에 유지

### Noted Risk: _watcher_core_compat Pattern

구현이 `sys.modules.get("watcher_core")` 조회를 사용하는 `_watcher_core_compat()` 헬퍼와 7개 thin wrapper(`_capture_pane_text`, `_pane_text_has_input_cursor`, 등)를 `watcher_dispatch.py`에 추가했다.

- **목적**: 기존 `mock.patch("watcher_core._shared_*")` 테스트 계약을 dispatch 함수 경로에서도 유지
- **현재 영향**: 216 tests PASS — 동작 정확성 확인됨
- **위험**: `watcher_dispatch.py`가 `watcher_core`가 `sys.modules`에 있을 때 묵시적으로 의존. 독립 import 시 fallback(기본값) 사용
- **규모**: 현재 139개 `watcher_core._shared_*` mock 중 대다수는 WatcherCore._poll() 경로로, dispatch 내부와 무관할 가능성이 높음
- **해소 방법**: 향후 `_watcher_core_compat` 제거 + 영향받는 테스트 mock 대상을 `watcher_dispatch._shared_*`로 교체

이번 round 클레임은 모두 사실이므로 PASS. 구조 debt는 M32 Axis 2 advisory 판단에 포함.

### M32 Structural State After Axis 1

| 파일 | 이전 | 이후 |
|---|---|---|
| `watcher_core.py` | ~4608 lines | ~4360 lines (dispatch 그룹 제거) |
| `watcher_dispatch.py` | 429 lines | ~680 lines (dispatch 그룹 추가) |
| `watcher_signals.py` | 450 lines | 450 lines (M30 Axis 3, 무변경) |
