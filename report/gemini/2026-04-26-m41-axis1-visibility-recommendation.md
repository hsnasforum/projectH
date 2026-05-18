# 2026-04-26 Milestone 41 Axis 1 — Preference 감사 가시성 강화 권고

## 상황 개요
- **M40 (Review Auditability) 완료**: 리뷰 단계에서 원본 세션 정보와 결정 사유(Rationale)를 기록하는 인프라가 구축되었습니다.
- **현상**: 기록된 감사 데이터가 실제 '선호 기억(Preference Panel)' 화면에는 노출되지 않아, 학습된 규칙의 배경을 파악하기 어렵습니다.
- **기술적 부채**: M40 Axis 2에서 durable candidate 수락 시 `reason_note`가 `Preference` 기록에 누락되었고, 모든 경로에서 `source_session_title`이 `Preference`에 저장되지 않고 있습니다.

## 판단 근거
1. **감사 루프의 시각화**: 기록(Audit)은 조회(Visibility)될 때 비로소 가치를 가집니다. 운영자가 선호도 목록을 보며 "이 규칙이 왜 생겼지?"라는 질문에 즉시 답할 수 있어야 합니다.
2. **데이터 정합성 보강**: 세션이 삭제되더라도 선호도 기록은 남으므로, 기록 시점에 세션 제목을 함께 저장하는 것이 감사 추적성 면에서 안전합니다.
3. **운영 효율성**: 출처 세션과 사유가 보이면 잘못 학습된 선호를 식별하고 수정/삭제하는 의사결정이 훨씬 빨라집니다.

## 권고 사항 (RECOMMENDATION)
- **결정**: Milestone 41 Axis 1 구현을 시작합니다.
- **RECOMMEND: implement Milestone 41 Axis 1: Preference Auditability — Trace Visibility in PreferencePanel**
    - **Data Capture (Backend)**: `app/handlers/aggregate.py`의 `submit_candidate_review`를 수정하여, 수락(ACCEPT) 시 `source_session_title`과 `reason_note`(durable path 포함)를 `Preference`의 `source_refs`에 저장합니다.
    - **Data Delivery (Backend)**: `app/handlers/preferences.py`의 `list_preferences_payload`에서 각 선호도 항목의 최신 `reason_note`와 `source_session_title`을 추출하여 최상위 필드로 노출합니다.
    - **Frontend**: `PreferenceRecord` 타입을 업데이트하고, `PreferencePanel.tsx`에서 각 항목 하단에 "출처 세션"과 "승인 사유"를 표시합니다.

### 예상 결과
- '선호 기억' 화면에서 각 규칙의 승인 사유와 출처 세션 제목을 즉시 확인 가능.
- 누락되었던 사유 및 제목 데이터가 선호도 기록에 영속화되어 감사 가능성 완결.
- 학습된 지식 베이스에 대한 운영 신뢰도 및 관리 편의성 향상.
