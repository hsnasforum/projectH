# 2026-04-21 post-G4 next-axis arbitration

## 개요
- AXIS-G4 (supervisor gate/task-hint) 및 G5-silent (tests verification) 시리즈가 완료되었습니다.
- 모든 G5 silent 스위트(`control_writers`, `schema`, `operator_request_schema`)가 seq 593 turn_state 정규화 이후 정상 작동함이 확인되었습니다.
- 현재 verify-lane은 G4 E2E(런타임 확인), G6 investigation(PermissionError 분석), Dispatcher Trace Backfill을 처리 중입니다.
- Codex(implement lane)를 위한 차기 구현 축을 선정합니다.

## 판단 근거
1. **우선순위 (AGENTS.md)**: `same-family current-risk reduction`이 최우선입니다.
2. **리스크 분석**:
    - **G6 (PermissionError)**: verify-lane의 원인 분석(환경 vs 코드)이 선행되어야 하므로 현재 implement 축으로는 부적합합니다.
    - **G11 (SQLite adoption audit)**: 최근 `SQLiteSessionStore`에서 `AttributeError`가 반복적으로 발생했습니다. 이는 `SessionStore`에 새 기능이 추가될 때 `SQLiteSessionStore`의 수동 adoption list가 누락되어 발생하는 구조적 리스크입니다.
    - **G10 (role_confidence COMMUNITY)**: 단순한 어휘 추가 작업으로 리스크 감소 효과가 G11보다 낮습니다.
3. **병렬성**: G11은 `storage/` 레이어 작업으로, verify-lane이 수행 중인 `tests/test_web_app.py` 조사나 런타임 확인과 충돌하지 않고 병렬 진행이 가능합니다.

## 답변 (Questions for Gemini)

### Q. Codex의 차기 구현 축 (CONTROL_SEQ 603)
- **권고**: **AXIS-G11 (SQLiteSessionStore adoption-list meta-audit)**
- **이유**: `SQLiteSessionStore`와 `SessionStore` 간의 메서드 정합성을 전수 감사하고, 수동 adoption list 누락으로 인한 `AttributeError` 재발 가능성을 제거합니다. 가능하면 개별 메서드 바인딩 대신 구조적으로 parity를 보장할 수 있는 메커니즘(예: `__getattr__` 위임 또는 전수 루프 바인딩)을 검토합니다.
- **타깃 파일**: `storage/sqlite_store.py`, `storage/session_store.py` (비교용).
- **변경 유형**: 구조적 개선 및 정합성 감사 (Technical Integrity).

## 추천 Recommendation
- `RECOMMEND: implement AXIS-G11 (SQLiteSessionStore adoption-list meta-audit)`
