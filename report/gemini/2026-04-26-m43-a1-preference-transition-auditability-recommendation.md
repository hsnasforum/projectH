# Advisory Log: 2026-04-26-m43-a1-preference-transition-auditability-recommendation

## 요약
B1 Release Gate가 정적 감사 및 운영자 승인을 통해 성공적으로 종료(Closed)되었습니다. 차기 구현 마일스톤인 M43의 첫 번째 슬라이스로 **후보 C (Preference 상태 전환 개선)**를 선정합니다. 이는 선호 기억의 라이프사이클을 견고하게 다듬고, 오작동 위험을 줄이는 "same-family risk reduction" 원칙에 가장 부합하는 선택입니다.

## 분석 및 판단
1. **B1 Gate 종료 확인**:
   - Live E2E 테스트는 샌드박스 보안 정책(Socket 생성 제한)으로 인해 `PermissionError`가 발생했으나, 정적 감사(`09c806d`)와 운영자 Q1 승인을 통해 인프라 정합성이 인정되었습니다. `docs/MILESTONES.md`가 최신 상태로 갱신되었음을 확인했습니다.

2. **M43 후보 비교 및 선정**:
   - **후보 A (Audit Depth)**: 현재 `PreferencePanel`에서 이미 출처 세션과 결정 사유를 표시하고 있어, "UI 회수" 가치는 이미 상당 부분 달성되었습니다. 세션별 추이(Trend) 표시는 데이터 스토리지 확장이 수반되어야 하므로 첫 슬라이스로는 다소 무겁습니다.
   - **후보 B (Application Quality)**: 반영 근거(Match Trace) 표시는 투명성 면에서 매우 중요하나, LLM의 반영 로직과 밀접하게 연계되어 있어 구현 복잡도가 높습니다.
   - **후보 C (Transition Auditability) — 선정**: M42에서 추가된 상태 필터(Candidate, Active, Paused) 간의 이동을 더 신중하고 투명하게 만드는 단계입니다. 특히 `candidate` → `active` 전환 시 "왜 이 선호를 지금 활성화하는지" 기록하게 함으로써, 전체 기억 시스템의 신뢰도(Audit Trail)를 완결 짓습니다.

3. **우선순위 타당성**:
   - `GEMINI.md`의 tie-break 원칙인 "same-family risk reduction"을 우선합니다. 잘못된 선호의 활성화를 방지하고, 모든 상태 변경에 이유를 남기는 것은 "가르칠 수 있는 로컬 에이전트"의 핵심 가치입니다.

## 권고 사항
- **RECOMMEND: implement Candidate C (M43 Axis 1: Preference Transition Auditability & Confirmation)**
- **Task**: `PreferencePanel`에서 상태 전이(활성화/일시중지/거부) 시 이유 입력 UI 추가 및 API/Store 확장.
- **Files**:
    - `storage/preference_store.py`: `transition_history` 수납 또는 `reason_note` 필드 확장.
    - `app/handlers/preferences.py`: `reason_note`를 받는 API 핸들러 수정.
    - `app/frontend/src/components/PreferencePanel.tsx`: 액션 시 확인/이유 입력 모달 추가.
    - `docs/ARCHITECTURE.md`: 전이 감사(Transition Audit) 사양 명시.

## Next 3 Implementation Priorities (Proposed)
1. **M43 Axis 1: 선호 상태 전이 감사 강화**: 상태 변경 시 이유 입력 및 이력 보존 (Candidate C).
2. **Active preference 적용 품질 개선**: 적용 뱃지 상세 trace 연결 (Candidate B).
3. **Preference audit depth 확장**: 세션별 적용 이력 추이 표시 (Candidate A).
