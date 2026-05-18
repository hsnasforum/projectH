# 2026-04-25 M32-direction-watcher-decomposition-dispatch

## 결정: 후보 A (M32 Axis 1 — watcher_core.py 책임 단위 분리)

### 근거
1. **구조적 리스크 감소 (GEMINI.md 우선순위 1)**: `watcher_core.py`는 여전히 4,608라인의 거대 파일이며, 핵심 제어 로직과 저수준 dispatch 로직이 섞여 있습니다. Dispatch helpers를 분리함으로써 파일 크기를 줄이고 "Pane 제어" 책임을 `watcher_dispatch.py`로 응집시킵니다.
2. **이전 작업(M30)과의 정렬**: M30에서 신호 추출(`watcher_signals.py`)을 분리한 전략의 연장선입니다. 저수준 tmux/pane 통신 로직을 추출하여 `WatcherCore` 클래스가 더 고수준의 오케스트레이션에 집중하게 합니다.
3. **가이드라인 준수**: `GEMINI.md`의 tie-break 기준인 "same-family current-risk reduction"이 UX 개선(후보 B)보다 우선합니다. 현재 검증 루프가 이미 PASS 상태(M31)이므로, 다시 구조적 안정성을 다질 적기입니다.

### 권고 Slice (M32 Axis 1)
- **목표**: `watcher_core.py`에서 저수준 dispatch 및 tmux 통신 로직을 `watcher_dispatch.py`로 분리.
- **대상 함수**:
    - `tmux_send_keys`
    - `_dispatch_codex`
    - `_dispatch_claude`
    - `_dispatch_gemini`
    - `_dispatch_lock_for`
- **검증**:
    - `watcher_core.py` 및 `watcher_dispatch.py`가 상호작용하며 기존 202+10+4 tests를 통과하는지 확인.
    - 특히 `WatcherCore`가 `watcher_dispatch` 모듈의 함수를 호출하도록 변경 시 mock patch target 영향 확인.

### 후보 검토
- **후보 B (UX 개선)**: 활성 선호 반영 표시(`[선호 N건 반영]`)가 이미 존재하므로 추가 개선은 가치가 있으나, 현재 거대 파일인 `watcher_core.py`의 구조적 결합도를 낮추는 것이 장기적 유지보수 관점에서 더 시급합니다.
- **후보 C (기타)**: 현재 M31까지의 기능적 루프가 Playwright로 확인되었으므로, 구조적 부채(technical debt) 해결을 우선순위로 둡니다.
