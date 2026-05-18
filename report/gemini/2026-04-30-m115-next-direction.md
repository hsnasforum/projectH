# 2026-04-30 M115 다음 방향 권고 — advisory

## 요약
- **RECOMMEND: implement cross-session memory Axis 1**
- **Exact slice**: `core/agent_loop.py`의 `AgentLoop._get_active_preferences()` 고도화 (context-relevance 필터링 + `preference_injected` task log 트레이스 추가)

## 현황 및 근거
M114(수동 활성화 즉시 주입 신뢰도 보정) 완료로, 사용자가 명시적으로 선택한 선호가 즉시 주입 자격을 갖추는 인프라가 구축되었습니다. 하지만 현재 `AgentLoop._get_active_preferences()`는 단순히 활성화된 선호 중 선착순(budget)으로 10개를 가져오는 초기 구현 상태입니다.

장기 목표인 'Teachable local personal agent'로 나아가기 위해서는, 주입되는 선호가 현재 작업의 맥락과 얼마나 관련이 있는지(context-relevance)를 판단하는 로직이 필요합니다. 또한, 어떤 선호가 왜 주입되었는지 task log에 명확히 남겨야 추후 디버깅과 사용자 피드백 루프가 정교해집니다.

## 권고 상세

### 1. 추천 방향: A) cross-session memory Axis 1
- **이유**: PR 머지 백로그(B)는 인프라 성격이 강하고 백엔드 로직 충돌 리스크가 낮으므로 병행 가능합니다. 리뷰 큐 확장(C)보다는 핵심 지능인 '주입 로직'의 신뢰성과 투명성을 먼저 확보하는 것이 North Star에 부합합니다.

### 2. 첫 번째 implement 슬라이스 scope
- **대상 파일**: `core/agent_loop.py`
- **핵심 변경**:
    - `_get_active_preferences()`:
        - 현재 작업의 `intent`나 `content`를 기반으로 한 간단한 relevance score 기반 정렬/필터링 도입.
        - 주입 시 `budget` 소진 정책 및 우선순위(highly reliable vs normal) 조정.
    - **Task Log**:
        - 선호 주입 시 `preference_injected` 이벤트를 생성하여 fingerprint와 주입 사유(relevance score 등)를 기록.

## 리스크 및 중단 조건 (Stop Rule)
- `_get_active_preferences` 내의 relevance 연산이 루프 성능에 유의미한 영향을 줄 경우, 계산 비용이 낮은 매칭 로직으로 제한하거나 캐싱 도입을 고려해야 합니다.
- PR #103–#108 머지 시 frontend UI와 backend 주입 로직 간의 필드명 불일치가 발견되면 즉시 중단하고 truth-sync를 수행하십시오.
