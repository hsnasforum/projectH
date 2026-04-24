# Advisory Log: M20 Axis 2 - Preference Conflict Detection

## 개요
- **일시**: 2026-04-23
- **요청**: M20 Axis 2(Preference Conflict Detection)와 전체 Smoke Gate(Axis 3) 간의 우선순위 판정 및 범위 정의
- **상태**: M20 Axis 1(SQLite Default 및 Migration)이 성공적으로 완료됨. 현재 약 40여 개의 커밋이 누적된 상태이며, 개인화 시스템의 정교함이 올라감에 따라 선호 간의 상충/중복 관리가 시급한 "Integrity" 과제로 부상함.

## 분석 및 판단
1.  **우선순위 판정**: 
    - **Option A (Conflict Detection) 선택**: Milestone 20의 주제는 "Scaling and Conflict Integrity"임. 기능적으로 상충 감지 로직을 완성한 뒤, 마지막 Axis 3에서 누적된 모든 변경 사항(M18~M20)을 하나의 거대한 Smoke Gate로 묶어 검증하는 것이 마일스톤의 논리적 완결성과 검증 효율성 면에서 우수함.
    - **리스크 관리**: M20 Axis 1까지의 변경 사항은 이미 각 라운드의 focused smoke/unit 테스트를 통해 기술적 안정성이 확인됨.
2.  **구현 전략 (Axis 2)**: 
    - **감지 로직**: 선호 문구(`description`)의 키워드 중첩도(Keyword Overlap)를 기반으로 한 휴리스틱 엔진을 도입.
    - **범위**: 활성(Active) 선호 간의 상충뿐만 아니라, 사용자가 새로운 후보를 활성화하려 할 때 기존 선호와의 중복 여부를 미리 경고함.
    - **UI**: 사용자가 상충되는 규칙들을 인지하고 하나를 일시중지하거나 수정하도록 유도하는 시각적 피드백 제공.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M20 Axis 2 (Preference Conflict Detection)**

1.  **Backend (Logic)**:
    - `app/handlers/preferences.py`에 `detect_conflicts()` 헬퍼 추가.
    - 활성 선호들의 문구를 정규화(공백/특수문자 제거, 소문자화)하여 중복을 체크하고, 키워드 자카드 유사도(Jaccard Similarity)가 임계값(예: 0.7)을 넘는 항목들을 '상충 의심'으로 그룹화.
2.  **API (Payload)**:
    - `list_preferences_payload` 결과에 각 선호별 `conflict_info` (상충하는 타 선호 ID 목록) 주입.
3.  **Frontend (UI)**:
    - `PreferencePanel.tsx`에서 상충 항목 옆에 경고 아이콘 표시.
    - 활성화(Activate) 액션 시 기존 선호와 상충될 경우 확인 팝업 또는 경고 메시지 노출.
4.  **Validation**:
    - 동일하거나 매우 유사한 두 규칙을 등록했을 때 백엔드 API가 상충 정보를 정확히 반환하는지 단위 테스트 검증.

## 기대 효과
- 다수의 개인화 규칙이 누적되어도 상호 모순되거나 중복된 규칙이 시스템을 어지럽히는 것을 방지.
- 사용자에게 시스템의 학습 상태에 대한 투명한 정보를 제공 (정직성 원칙).
- Milestone 20의 모든 기능적 목표를 달성하고 최종 안정화 단계 진입 준비 완료.
