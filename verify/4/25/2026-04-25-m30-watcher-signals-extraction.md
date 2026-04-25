STATUS: verified
CONTROL_SEQ: 145
BASED_ON_WORK: work/4/25/2026-04-25-m30-watcher-signals-extraction.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 145 (MILESTONES.md M30 doc sync)

---

## M30 Axis 3: watcher_core signal extraction

### Verdict

PASS. `watcher_signals.py` 신규 생성, `watcher_core.py`에서 신호 추출 함수 블록 제거 및 import 교체, `tests/test_watcher_signals.py` 신규 생성. 202 + 10 tests 전체 통과.

### Checks Run

- `python3 -m py_compile watcher_core.py watcher_signals.py tests/test_watcher_signals.py` → OK (출력 없음)
- `grep -n "^def _extract_implement_blocked_signal|^def _extract_live_session|..." watcher_core.py` → 매치 없음 (exit 1)
- `grep -n "^from watcher_signals import" watcher_core.py` → `686:from watcher_signals import (` 확인
- `python3 -m unittest tests/test_watcher_core.py -v 2>&1 | tail -5` → `Ran 202 tests in 8.743s` `OK`
- `python3 -m unittest tests/test_watcher_signals.py -v 2>&1 | tail -5` → `Ran 10 tests in 0.003s` `OK`
- `git diff --check -- watcher_core.py watcher_signals.py tests/test_watcher_signals.py` → exit 0

### What Was Not Checked

- `make e2e-test` 미재실행: 브라우저 계약 변경 없음, 변경이 `watcher_core.py` / `watcher_signals.py` / `tests/test_watcher_signals.py`에 한정.
- pipeline live soak 미재실행: 신호 추출 함수는 순수 파싱 로직으로 tmux/subprocess 의존 없음.

### Implementation Review

work 노트 기술과 일치:
- `watcher_signals.py:1–450` — regex 상수 12개 + `_HandoffSentenceReplacementTarget` + 함수 11개 (9 target + `_fallback_escalation_reasons` + `_normalize_control_path_hint`)
- `watcher_core.py:686` — `from watcher_signals import (...)` 블록으로 교체됨
- 보존 함수 4개 (`_line_looks_like_input_prompt`, `_pane_text_has_gemini_ready_prompt`, `_pane_has_input_cursor`, `_pane_has_working_indicator`) 수정 없음 확인
- `tests/test_watcher_signals.py` — 기존 10개 테스트를 `watcher_signals.*` import 버전으로 복사

### M30 Structural State After Axes 1–3

| Axis | 내용 | 상태 |
|---|---|---|
| Axis 1 (SEQ 136-137) | pane-surface stub 7개 제거, `_shared_*` 교체 | ✓ 완료 |
| Axis 2 (SEQ 141-142) | legacy patch proxy 제거, test target 마이그레이션 | ✓ 완료 |
| Axis 3 (SEQ 144-145) | 신호 추출 순수 함수 → `watcher_signals.py` 분리 | ✓ 완료 |

`watcher_core.py`: 5001 → 4608 lines, 45 → 33 top-level defs

### Noted Risk

`watcher_signals.py`에는 `watcher_core.py`의 보존 함수와 유사한 prompt-line 판별 로직이 소량 중복 존재. 순환 참조 방지를 위한 좁은 중복이며 현재 202 tests PASS. 추후 공용 parsing helper로 통합 가능.

### Next: MILESTONES.md Doc Sync

M30 Axes 1–3가 구현 완료됐으나 `docs/MILESTONES.md`에 M30 섹션이 없음. "Next 3 Implementation Priorities"도 M30을 pending으로 기술 중. 이 divergence 해소가 다음 bounded slice.
