# 2026-04-25 M30-axis3-watcher-decomposition-signals

## 결정: 후보 A (M30 Axis 3 — watcher_core.py 책임 단위 분리)

### 근거
1. **일관성 및 전략적 우선순위**: 이전 권고(2026-04-24) 및 M30의 핵심 목표인 "Watcher 구조적 부채 해결"을 계승합니다. Axis 1-2에서 legacy proxy 프록시를 제거하여 분리를 위한 기술적 토대를 마련했으므로, 이제 실질적인 파일 분리를 실행할 시점입니다.
2. **리스크 감소 (GEMINI.md 우선순위 1)**: 5,000라인에 달하는 `watcher_core.py`는 유지보수 리스크가 매우 높습니다. 가장 독립적이고 상태가 없는(stateless) "Signal Extraction(Parsing)" 로직을 먼저 분리함으로써 파일 크기를 줄이고 응집도를 높입니다.
3. **가이드라인 준수**: `GEMINI.md`의 tie-break 기준인 "same-family current-risk reduction"이 다른 family 작업(Cand C)보다 우선합니다.

### 권고 Slice (M30 Axis 3)
- **목표**: `watcher_core.py`에서 신호 추출 및 파싱 로직을 `watcher_signals.py`로 분리.
- **대상 함수 (9개)**:
    - `_extract_live_session_escalation`
    - `_extract_implement_blocked_signal`
    - `_extract_implement_forbidden_menu_signal`
    - `_extract_implement_completed_handoff_signal`
    - `_match_implement_blocked_status`
    - `_can_append_implement_blocked_wrap`
    - `_normalize_escalation_line`
    - `_decode_handoff_markdown_literal`
    - `_parse_handoff_sentence_replacement_target`
- **검증**:
    - `tests/test_watcher_signals.py`를 신설하여 해당 함수들의 단위 테스트를 이관.
    - `tests/test_watcher_core.py` 및 전체 unittest 202개가 통과함을 확인.

### 후보 검토
- **후보 B (M30 종결)**: Legacy proxy 제거만으로는 5,000라인의 거대 파일 문제를 해결할 수 없습니다. 구조적 개선이 더 필요합니다.
- **후보 C (Controller Monitor)**: 사용자 가시적 개선(user-visible improvement) 측면에서 가치가 있으나, Watcher family의 핵심 리스크 해결이 완료된 후에 진행하거나 별도의 Milestone(M31)으로 다루는 것이 적절합니다. 현재 untracked 상태인 파일들은 bundle 작업 시점에 함께 정리될 수 있습니다.
