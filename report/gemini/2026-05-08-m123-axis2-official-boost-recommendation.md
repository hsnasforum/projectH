# 2026-05-08 M123 Axis 2 스코프 및 다음 슬라이스 권고

## 목표
`UNRESOLVED` 슬롯(비신뢰 출처 합의만 존재)을 `STRONG`으로 전환하기 위해 공식 출처 탐색 쿼리를 강화하고, 교차 검증을 위한 후보 출처 선택 범위를 확대한다.

## 성공 기준
- `UNRESOLVED` 슬롯 존재 시 2차/3차 조사에서 공식 홈페이지 탐색 쿼리가 추가로 생성됨.
- 재조사 단계에서 `_select_ranked_web_sources`의 `max_items`가 상향되어 더 넓은 범위의 출처가 교차 검증 후보로 활용됨.
- 신규 회귀 테스트를 통해 `UNRESOLVED` 슬롯이 있는 경우와 없는 경우의 쿼리 생성 및 소스 선택 차별화가 검증됨.

## 근거
M123 Axis 1은 `UNRESOLVED` 슬롯이 남아있을 때 조사를 "실행"하는 가드레일을 구축했다. Axis 2는 실행되는 조사가 실제 신뢰 출처(Official/Wiki 등)를 찾아낼 확률을 높이는 "품질" 단계이다. 현재 3개로 제한된 소스 선택 범위는 좁은 니치 분야에서 신뢰 소스를 누락할 위험이 있으며, 슬롯별 쿼리 외에 전체 엔티티의 공식 사이트를 찾는 범용 쿼리가 병행될 때 `OFFICIAL` 롤 획득이 더 용이해진다.

## Stop Rule
- 3차 조사 이후에도 `UNRESOLVED`가 해결되지 않는 경우, 추가 조사를 무한 루프화하지 않고 `[미해결]` 상태로 응답을 확정한다.
- `max_items` 확대가 전체 토큰 소모량을 2배 이상 급증시키거나 응답 지연을 10초 이상 유도하는 경우 스코프를 다시 좁힌다.

## 권고 슬라이스

**RECOMMEND: implement m123_axis2_unresolved_official_boost**
- **대상 파일**: `core/agent_loop.py`
- **구현 내용**:
    1. `_build_entity_second_pass_queries`: `unresolved_slots`가 존재할 경우, 슬롯별 쿼리 외에 `{query} 공식 홈페이지` 또는 `{query} official website`와 같은 엔티티 레벨 공식 사이트 탐색 쿼리 1종을 추가.
    2. `agent_loop.py` (Investigation Loop): 2차/3차 조사 단계에서 `unresolved_slots`가 비어있지 않다면 `_select_ranked_web_sources` 호출 시 `max_items`를 기존 3에서 5로 확대 적용.
- **검증**: `tests/test_smoke.py`에 `UNRESOLVED` 슬롯 잔존 시 쿼리 다양화 및 소스 선택 개수 상향 여부를 확인하는 테스트 케이스 추가.

## 절차
1. `core/agent_loop.py`의 `_build_entity_second_pass_queries` 함수 수정 (쿼리 추가 로직).
2. `core/agent_loop.py`의 조사 루프부 수정 (`max_items` 동적 할당).
3. `tests/test_smoke.py` 회귀 테스트 추가 및 158+N개 테스트 PASS 확인.
4. `docs/MILESTONES.md` 및 `docs/TASK_BACKLOG.md`에 M123 Axis 2 완료 기록 및 다음 축 정의.
