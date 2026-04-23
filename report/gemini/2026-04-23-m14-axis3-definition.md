# Advisory Log: M14 Axis 3 - Review Queue Quality Integration

## 개요
- **일시**: 2026-04-23
- **요청**: M14 완료 여부 판정 또는 Axis 3 정의 (m14_completion_or_axis3_definition)
- **상태**: M14 Axis 1(SQLite parity) 및 Axis 2(Quality Integration Bundle) 완료 및 검증됨.

## 분석 및 판단
1.  **현황**: Axis 2를 통해 `PreferencePanel` (설정창) 내의 선호 항목들에는 `고품질` 배지가 성공적으로 적용됨. 하지만 선호가 되기 전 단계인 `검토 후보` (Review Queue) UI에는 아직 품질 정보가 노출되지 않음.
2.  **M14 목표 재검토**: M14의 핵심 목표인 "Trace Quality Integration"을 완전히 달성하려면, 사용자가 수락/거부를 결정하는 시점인 **Review Queue**에서도 품질 신호가 제공되어야 함.
3.  **후보 비교**:
    - **Option A (종료)**: 설정창 배지만으로 충분하다고 볼 수 있으나, 결정 시점(Review)의 정보 부족으로 M14의 가치가 반감됨.
    - **Option B (Review Queue 통합)**: 가장 권장됨. 사용자가 교정 패턴을 선호로 승격시킬지 결정할 때 `is_high_quality` 정보를 제공함으로써 실질적인 "Quality Integration"을 완성함.
    - **Option C (SQLite Quality Parity)**: SQLite 경로의 데이터 누락 문제를 해결하는 것은 중요하나, 현재 설계상 `similarity_score`가 review flow에 포함되어 있지 않아 기술적 부채 해결에 가까움.
4.  **결론**: Option B를 M14의 마지막 슬라이스인 Axis 3으로 정의하여 품질 통합 루프를 완성하고 M14를 닫는 방향을 추천함.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M14 Axis 3 (Review Queue Quality Integration)**

1.  **Frontend API & Types**:
    - `app/frontend/src/api/client.ts`의 `ReviewQueueItem` (또는 관련 타입)에 `quality_info` 필드 추가.
2.  **Backend Enrichment**:
    - `SerializerMixin._build_review_queue_items` (in `app/serializers.py`)에서 `durable_candidate`를 직렬화할 때, 연관된 `artifact_id`와 `similarity_score`를 조회하여 `quality_info`를 주입하도록 보강.
    - `SQLitePreferenceStore`는 현재 점수가 없으므로 null 또는 0 점수로 안전하게 처리 (JSON 우선 지원).
3.  **Frontend UI**:
    - `app/frontend/src/components/Sidebar.tsx` (또는 Review Queue 렌더링 컴포넌트)에서 `검토 후보` 카드 옆에 `is_high_quality`인 경우 `고품질` 배지 표시.
4.  **Validation**:
    - TypeScript 타입 체크 및 수동 UI 확인. 신규 UI 요소가 추가되므로 가능하다면 간단한 browser smoke test 추가 고려.

## 기대 효과
- 사용자가 검토 대기 중인 후보의 신뢰도를 즉각적으로 파악 가능.
- Milestone 14의 품질 통합 목표를 일관성 있게 완성.
