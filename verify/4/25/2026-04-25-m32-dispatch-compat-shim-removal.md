STATUS: verified
CONTROL_SEQ: 161
BASED_ON_WORK: work/4/25/2026-04-25-m32-dispatch-compat-shim-removal.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 161 (M32 complete — M33 direction)

---

## M32 Axis 2: _watcher_core_compat shim 제거 + test patch 정규화

### Verdict

PASS. `_watcher_core_compat` 헬퍼와 9개 thin wrapper가 완전 제거됐고, dispatch 함수가 `_shared_*`를 직접 호출하며, 216 unit tests 전체 통과.

### Checks Run

- `python3 -m py_compile watcher_dispatch.py watcher_core.py` → compile OK
- `grep -n "sys.modules|_watcher_core_compat|^def _capture_pane_text|..." watcher_dispatch.py` → exit 1 (매치 없음)
- `python3 -m unittest tests/test_watcher_core.py tests/test_watcher_signals.py tests/test_controller_monitor.py -v 2>&1 | tail -5` → `Ran 216 tests in 8.472s` `OK`
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py` → exit 0
- `grep -n '"watcher_dispatch\.'` in lines 8206–8417 → `watcher_dispatch.subprocess.run`, `watcher_dispatch._shared_capture_pane_text`, `watcher_dispatch._pane_has_working_indicator` 등 정규화 확인
- 범위 외 `watcher_core.*` dispatch 패치 잔존 여부 → exit 0 (매치 없음)

### M32 Full Summary

| Axis | 내용 | 상태 |
|---|---|---|
| Axis 1 (SEQ 157–158) | dispatch/tmux 13개 → watcher_dispatch.py + _watcher_core_compat shim | ✓ |
| Axis 2 (SEQ 160–161) | shim 제거, dispatch 직접 호출, CodexDispatchConfirmationTest patch 정규화 | ✓ |

**구조 현황 (M32 완료 후):**

| 파일 | 크기 | 역할 |
|---|---|---|
| `watcher_core.py` | ~4360 lines | WatcherCore 클래스 + 설정/prompt 헬퍼 |
| `watcher_dispatch.py` | ~640 lines | DispatchIntent, WatcherDispatchQueue, dispatch/tmux 헬퍼 |
| `watcher_signals.py` | 450 lines | 신호 추출 순수 함수 |

### Next

M32 Axes 1–2 완료. M33 방향 — 추가 구조 분리 또는 기능 milestone — advisory 판단 필요.
