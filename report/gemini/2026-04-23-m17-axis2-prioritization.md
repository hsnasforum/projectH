# Advisory Log: M17 Axis 2 - Detailed Evidence View Prioritization

## 개요
- **일시**: 2026-04-23
- **요청**: M17 Axis 2(Detailed Evidence View)와 Axis 3(Release Stabilization) 중 우선순위 판정
- **상태**: M17 Axis 1(Review Statement Editing)이 완료 및 검증됨. 현재 25개 커밋이 누적된 상태이며, 개인화 루프의 "사용자 제어" 능력은 확보되었으나 "판단 근거의 구체성"이 아직 부족함.

## 분석 및 판단
1.  **우선순위 (Axis 2 vs Axis 3)**: 
    - **Axis 2 선택**: M17의 핵심 목표인 "Review Depth"를 완성하는 것이 논리적 완결성 측면에서 우수함. 사용자가 문구를 편집(Axis 1)할 때, 실제 어떤 문장이 어떻게 바뀌었는지(Axis 2)를 한 화면에서 확인하는 것은 필수적인 UX임.
    - **안전성**: M16 Axis 2에서 이미 전체 Smoke Gate를 통과(139 tests PASS)했으므로, 기능 구현을 하나 더 추가한 뒤 최종적으로 Axis 3에서 전체 시스템을 공고히 하는 "Finish Implementation then Stabilize" 전략을 유지함.
2.  **구현 전략 (Axis 2)**: 
    - 현재 `delta_summary`는 수정된 단어 위주로 보여주지만, 실제 맥락을 파악하려면 `original_text`와 `corrected_text`의 스니펫 비교가 필요함.
    - 성능 및 페이로드 최적화를 위해 전체 텍스트가 아닌 변경 지점 주변의 스니펫만 포함하거나, 일정 길이(예: 400자)로 제한하여 직렬화함.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M17 Axis 2 (Detailed Evidence View)**

1.  **Backend (Serializer)**:
    - `app/serializers.py`의 `_build_review_queue_items`가 각 항목에 `original_text` 및 `corrected_text` 스니펫을 포함하도록 보강.
    - 긴 텍스트의 경우 가독성을 위해 적절히 Truncate 처리.
2.  **Frontend (UI)**:
    - `ReviewQueuePanel.tsx`의 각 카드에 '상세 보기' (View Details) 토글 추가.
    - 확장 시 기존(Original)과 수정(Corrected) 텍스트를 나란히 또는 상하로 배치하여 비교할 수 있는 대조 뷰 구현.
3.  **Validation**:
    - Playwright 시나리오: 리뷰 카드 확장 -> 스니펫 비교 영역 노출 확인 -> 텍스트 정합성 확인.

## 기대 효과
- 사용자가 시스템의 학습 의도를 100% 이해한 상태에서 규칙을 편집하거나 수락할 수 있게 함.
- 개인화 루프의 투명성(Transparency)과 정직성(Honesty) 강화.
- M17의 모든 기능적 요구사항을 충족하여 최종 안정화(Axis 3) 단계 진입 준비 완료.
