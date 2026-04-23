# Advisory Log: M19 Axis 2 - Discovery Integrity (Duplicate and Conflict Guards)

## 개요
- **일시**: 2026-04-23
- **요청**: M19 Axis 2 (Discovery Integrity)의 범위 및 구현 전략 정의
- **상태**: Milestone 18에서 글로벌 후보(Global Candidate) 기능이 도입되었으나, 현재 중복 검사가 지문(Fingerprint) 단위로만 수행됨. 동일하거나 유사한 제안 문구(`statement`)를 가진 중복 후보가 나타날 리스크와 품질 정보 누락 문제를 해결해야 함.

## 분석 및 판단
1.  **지문 기반 중복의 한계**: 지문이 다르더라도 최종적으로 도달하는 제안 문구(`statement`)나 규칙이 동일할 수 있음. 사용자 입장에서는 동일한 규칙을 여러 번 검토하는 번거로움이 발생함 (Redundancy).
2.  **데이터 품질 (Quality Integrity)**: 글로벌 후보는 여러 세션의 데이터를 합친 것이므로, 각 세션의 유사도 점수(`similarity_score`)를 평균하여 품질 정보를 제공해야 함. 현재 글로벌 후보는 `quality_info: None`으로 표시됨.
3.  **교차 세션 정의 강화**: 단순 반복 횟수(`COUNT(*)`)보다 실제 "몇 개의 세션"에서 나타났는지(`COUNT(DISTINCT session_id)`)가 글로벌 신호의 신뢰도를 결정함.
4.  **편집 무결성 (Override Integrity)**: M17에서 도입된 리뷰 문구 편집(`statement_override`) 기능이 글로벌 후보 수락 경로에서는 아직 무시되고 있는 버그성 누락이 확인됨.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M19 Axis 2 (Discovery Integrity Guards)**

1.  **Tighten Recurrence Detection**:
    - `storage/sqlite_store.py:find_recurring_patterns`를 수정하여 `COUNT(DISTINCT session_id) >= 2` 기준 적용 (진정한 교차 세션 신호 보장).
2.  **Deduplication by Statement**:
    - `app/serializers.py:_build_review_queue_items`에서 글로벌 후보 생성 시, 이미 존재하는 선호(`Preference`)의 `description`과 동일한 `statement`를 가진 후보는 제외.
    - 로컬 후보와 글로벌 후보 간에 문구가 중복될 경우 로컬 후보를 우선하고 글로벌은 억제(Suppress).
3.  **Global Quality Enrichment**:
    - 글로벌 후보의 `avg_similarity_score`를 모든 지원 교정본(`corrections`)의 평균으로 계산하여 `quality_info` 주입.
4.  **Action Logic Fix**:
    - `app/handlers/aggregate.py:submit_candidate_review` 글로벌 경로에서 `statement_override`가 있을 경우 이를 `description`으로 사용하도록 수정.

## 기대 효과
- 리뷰 큐의 노이즈(중복 제안)를 제거하여 사용자 검토 피로도 감소.
- 글로벌 후보에 대해서도 품질 배지(`고품질`)를 제공하여 수락 근거 강화.
- 세션 간 장벽을 넘는 개인화 학습의 신뢰도와 정밀도 향상.
