# Advisory Log: M16 Definition - Review Depth and Reliability

## 개요
- **일시**: 2026-04-23
- **요청**: M15 완료 이후 M16 범위 정의 (m15_closed_m16_scope_needed)
- **상태**: M15(Personalization Stability & Review Surface Expansion)가 성공적으로 종료됨. 사이드바의 `ReviewQueuePanel`과 클릭 가능한 배지 인터랙션이 구축되었으나, 리뷰 정보의 깊이와 UI의 회복탄력성(Resilience) 측면에서 보강이 필요함.

## 분석 및 판단
1.  **리뷰 깊이 (Review Depth)**: 사용자가 검토 후보를 수락할 때, 제안된 문구(`statement`)만 보고 판단하는 것은 불충분함. 해당 후보가 어떤 교정 패턴(`delta_summary`: 수정/추가/제거)에서 유도되었는지 증거를 보여주어야 함.
2.  **UI 안정성 (UI Resilience)**: 현재 선호/리뷰 관련 API 호출이 실패할 경우 UI에서 아무런 피드백이 없음. "수락됨"과 같은 긍정적 피드백(Toast)과 네트워크 오류 등에 대한 대응이 필요함.
3.  **운영 부채 (Operational Debt)**: M15에서 브라우저 노출 계약이 확장되었으나 전체 테스트(`make e2e-test`)가 수행되지 않음. 또한 `app/static/dist` 파일들이 hash가 무시된 채 덮어쓰기되고 있는 패키징 정책 정리가 필요함.
4.  **M16 방향성**: "Review Depth and Reliability"
    - "무엇을 배우려 하는가"를 명확히 보여주고, "동작이 성공했는가"를 확신하게 함으로써 개인화 루프의 신뢰도를 높임.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M16 Axis 1 (Review Evidence Enrichment)**

1.  **Backend (Serializer)**:
    - `SerializerMixin._build_review_queue_items`가 `delta_summary`를 포함하도록 수정.
    - 해당 후보의 기반이 되는 `correction` 레코드에서 `delta_summary`를 추출하여 직렬화.
2.  **Frontend (UI)**:
    - `ReviewQueuePanel.tsx`에서 각 카드에 `delta_summary`를 표시 (예: "교정: A -> B").
    - `PreferencePanel.tsx`와의 일관성 유지.
3.  **Validation**:
    - Playwright 시나리오: 리뷰 카드에 `delta_summary` 텍스트가 정상적으로 렌더링되는지 확인.

**M16 전체 로드맵 계획**:
- **Axis 2 (Reliability)**: 선호/리뷰 액션에 대한 Toast 피드백 및 에러 핸들링.
- **Axis 3 (Integrity)**: `make e2e-test` 전수 통과 및 `dist` 에셋 관리 정책 확정.

## 기대 효과
- 사용자가 개인화 규칙을 수락하기 전 변경 내용을 구체적으로 파악 가능.
- 시스템 동작에 대한 가시적 피드백을 통해 사용자 신뢰 구축.
- 운영 부채 조기 상환을 통한 안정적인 배포 기반 마련.
