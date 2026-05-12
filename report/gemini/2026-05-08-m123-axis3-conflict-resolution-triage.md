# 2026-05-08 M123 Axis 3 스코프 및 다음 슬라이스 권고

## 목표
정보 상충(`CONFLICT`) 상태인 슬롯에 대해 다중 후보 값을 모두 포함한 교차 검증 쿼리를 생성하여, 자동화된 조사 루프 내에서 상충 해소 및 `STRONG` 상태 전환 확률을 높인다.

## 성공 기준
- `summarize_slot_coverage` 결과에서 `CONFLICT` 상태인 슬롯이 상충하는 후보 값(competing claims) 정보를 포함함.
- `_build_entity_second_pass_queries`가 `CONFLICT` 슬롯 발견 시, 단순히 주 후보(primary claim) 확인에 그치지 않고 후보 값들 간의 차이나 사실 관계를 묻는 교차 검증 쿼리를 생성함.
- 신규 회귀 테스트를 통해 `CONFLICT` 슬롯에 대해 다중 후보가 반영된 쿼리 생성이 확인됨.

## 근거
현재 M123의 테마는 "웹 조사 품질 개선"이며, Axis 1과 2를 통해 `UNRESOLVED`(신뢰 출처 없음) 상태의 조사 가드레일과 품질이 강화되었다. 다음 논리적 단계는 `CONFLICT`(상충하는 신뢰 출처들 존재) 상태의 해소이다. 현재 루프는 상충 상황에서도 `primary_claim` 하나만 확인하려고 시도하므로, 상충하는 다른 신뢰 출처의 주장을 검증하거나 두 값 사이의 진위를 가리는 쿼리를 명시적으로 던지는 것이 품질 향상에 필수적이다.

## Stop Rule
- 상충 해소 쿼리 추가가 조사 루프의 횟수를 불필요하게 늘려 전체 지연 시간을 악화시키는 경우 쿼리 생성 전략을 간소화한다.
- 후보 값이 3개 이상인 극단적 상충 상황에서는 상위 2개 후보에 집중하거나 조사를 중단하고 `[정보 상충]` 상태를 유지한다.

## 권고 슬라이스

**RECOMMEND: implement m123_axis3_conflict_resolution_queries**
- **대상 파일**: `core/web_claims.py`, `core/agent_loop.py`
- **구현 내용**:
    1. `core/web_claims.py`: `SlotCoverage` 데이터 클래스에 `competing_claims` 필드 추가 및 `summarize_slot_coverage`에서 상충하는 `ClaimRecord`들을 수집하여 전달하도록 수정.
    2. `core/agent_loop.py`: `_build_entity_second_pass_queries`에서 `CONFLICT` 슬롯에 대해 `primary_claim.value`와 `competing_claims`의 값들을 조합한 교차 검증 쿼리(예: `"{query} {val1} {val2} 확인"`) 생성 로직 추가.
- **검증**: `tests/test_smoke.py`에 `CONFLICT` 슬롯 존재 시 다중 후보 반영 쿼리 생성 여부를 확인하는 테스트 케이스 추가 및 160+N개 테스트 PASS 확인.

## 절차
1. `core/web_claims.py`의 `SlotCoverage` 및 `summarize_slot_coverage` 수정.
2. `core/agent_loop.py`의 쿼리 생성부 수정.
3. `tests/test_smoke.py` 회귀 테스트 추가.
4. `docs/MILESTONES.md` 및 `docs/TASK_BACKLOG.md`에 M123 Axis 3 정의 및 진행 상황 기록.
