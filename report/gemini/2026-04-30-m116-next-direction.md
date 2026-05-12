# 2026-04-30 M116 다음 방향 권고 — advisory

## 요약
- **RECOMMEND: implement relevance quality improvement (Candidate C)**
- **Exact slice**: `core/agent_loop.py`의 `_preference_context_terms` (stop-word 제거 및 정규화) 및 `_select_context_relevant_preferences` (매칭 품질 개선)

## 현황 및 근거
M115에서 도입된 컨텍스트 관련성 필터는 단순 `split()` 기반 키워드 중첩 매칭을 사용하고 있어, "의", "를", "is", "the"와 같은 일반적인 기능어(stop-word) 매칭으로 인해 관련 없는 선호가 과잉 주입되는 품질 저하가 관찰됩니다.

장기 목표인 'Teachable local personal agent'가 사용자에게 유능하게 느껴지기 위해서는, 주입되는 선호의 '정확도'가 양보다 중요합니다. 따라서 노이즈를 제거하는 관련성 품질 개선이 가장 시급한 단계입니다.

## 권고 상세

### 1. 추천 방향: C) 관련성 품질 개선
- **이유**: 현재의 naive 매칭은 컨텍스트 예산(budget)을 낭비하고 모델의 응답 일관성을 해칠 수 있습니다. stop-word 제거와 매칭 기준 강화는 가장 적은 비용으로 가장 큰 품질 향상을 기대할 수 있는 'Low-hanging fruit'입니다.
- **우선순위 고려**: 후보 B(`is_highly_reliable` 정렬)는 품질 개선(C) 과정에서 간단한 정렬 로직 추가로 병행 구현이 가능하므로, C를 주축으로 삼는 것이 효율적입니다.

### 2. 첫 번째 implement 슬라이스 scope
- **대상 파일**: `core/agent_loop.py`
- **핵심 변경**:
    - `_preference_context_terms()`:
        - 한국어/영어 핵심 stop-word 리스트 도입 및 필터링.
        - 단어 길이 제한 및 소문자 정규화 로직 강화.
    - `_select_context_relevant_preferences()`:
        - 단순 합집합 크기가 아닌, 매칭된 키워드의 수나 `is_highly_reliable` 여부에 따른 가중치 정렬 도입.
        - `preference_injected` 이벤트의 `reason` 필드에 매칭 키워드 또는 점수 기록.

## 리스크 및 중단 조건 (Stop Rule)
- stop-word 리스트가 너무 비대해져서 정규 표현식 성능 이슈가 발생할 경우, 단순 `set` 기반 룩업으로 전환하십시오.
- `_get_active_preferences`의 `highly_reliable_only` 옵션과 충돌하여 아무것도 주입되지 않는 케이스가 빈번해지면 `fallback_all` 동작이 정상 작동하는지 재검증하십시오.
