# 2026-04-19 Conflict-aware source-line helper 및 Agent Loop role_priority 동기화 arbitration

## 중재 배경
- seq 408을 통해 응답 본문에 `상충하는 정보 [정보 상충]:` 섹션이 추가되어 상충 슬롯의 가시성이 확보됨.
- 그러나 현재 `근거 출처:` 영역을 생성하는 `_build_entity_claim_source_lines`는 여전히 `conflict_claims` 버킷을 참조하지 않고 있어, 상충 정보의 출처가 하단 출처 목록에서 누락될 수 있는 논리적 간극이 존재함.
- 또한 `core/agent_loop.py` 내부에 하드코딩된 `role_priority` 맵들이 `core/web_claims.py`에서 승격된 최신 우선순위(OFFICIAL: 5, DATABASE: 4 등)와 동기화되지 않은 상태로 발견됨.

## 결정 및 권고
- **RECOMMEND: implement Conflict-aware 근거 출처 source-line helper + Agent Loop role_priority sync (Option A)**
- **결정 이유**:
    - "Priority 2: same-family user-visible improvement" 원칙에 따라 응답 본문 내 가시성 체계를 완결함.
    - 본문에 노출된 상충 슬롯의 구체적 출처가 하단 목록에도 정확히 포함되도록 보장하여 사용자 신뢰도를 높임.
    - 내부 가중치 로직(`role_priority`)의 불일치를 해소하여 출처 정렬 순서의 일관성을 확보함.

## 상세 가이드 (Option A 확장)
- **수정 대상 파일**:
    - `core/agent_loop.py`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/agent_loop.py`:
        1. `_build_entity_claim_source_lines` 시그니처에 `conflict_claims: list[ClaimRecord]` 추가 및 `support_refs` 수집 루프에 포함.
        2. `_build_entity_web_summary` (또는 `_build_entity_card_response`) 호출부 업데이트.
        3. `_entity_claim_sort_key` 및 `_build_entity_claim_source_lines` 내의 하드코딩된 `role_priority`를 `core/web_claims.py`의 `_ROLE_PRIORITY`와 일치하도록 수정 (OFFICIAL: 5, WIKI: 4, DATABASE: 4, DESCRIPTIVE: 3, NEWS: 2).
    - `tests/test_smoke.py`: 상충 슬롯의 출처가 `근거 출처:` 목록에 실제로 나타나는지 확인하는 regression test 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k coverage`
    - `python3 -m py_compile core/agent_loop.py`
    - `git diff --check`
