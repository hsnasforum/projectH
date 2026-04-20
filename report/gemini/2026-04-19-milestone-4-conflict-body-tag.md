# 2026-04-19 Milestone 4 Response-Body CONFLICT Tag Emission arbitration

## 중재 배경
- Milestone 4의 `Source Role Weighting`과 `Focus-Slot Wording Polish`가 완료됨에 따라, `CONFLICT` ("정보 상충") 가시성 체계의 마지막 공백인 "응답 본문 내 전용 헤더 태그"를 해결할 시점임.
- 현재 `docs/ACCEPTANCE_CRITERIA.md` 등에는 `[정보 상충]` 태그가 본문에 방출되지 않는다고 명시되어 있으나, 이는 브라우저 표면(바, 메타, 패널 힌트)과의 일관성을 저해하는 요소임.
- 오늘 `3+ docs-only same-family` 가드가 활성화되었으나, 이번 슬라이스는 코드와 문서를 함께 수정하는 "mixed ripple slice"이므로 가드를 위반하지 않으면서도 정합성을 확보할 수 있는 적기임.

## 결정 및 권고
- **RECOMMEND: implement Response-body [정보 상충] tag emission — explicitly named mixed ripple slice (Option D)**
- **결정 이유**:
    - "Priority 3: new quality axis (visibility integration)" 원칙에 따라, `CONFLICT` 상태를 응답 본문에서도 명시적으로 구분하여 사용자에게 전달함.
    - `docs/ACCEPTANCE_CRITERIA.md:49` 등에서 명시한 "방출하지 않음" 제약을 제거하고, 전체 시스템의 가시성 계약을 완결함.
    - `Option A/B/C` 보다 사용자 체감 이득이 크며, Milestone 4의 CONFLICT 관련 작업을 최종적으로 "Seal"하는 의미가 큼.

## 상세 가이드 (Option D 기반)
- **수정 대상 파일**:
    - `core/agent_loop.py`
    - `docs/ACCEPTANCE_CRITERIA.md`
    - `docs/PRODUCT_SPEC.md`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/agent_loop.py`: 
        1. `_select_entity_fact_card_claims`가 `conflict_selected` 리스트를 별도로 반환하도록 확장. (`CoverageStatus.CONFLICT`인 슬롯을 `weak_selected`에서 분리)
        2. `_build_entity_card_response`에서 `상충하는 정보 [정보 상충]:` 헤더와 해당 항목들을 방출하도록 로직 추가.
    - `docs/ACCEPTANCE_CRITERIA.md:49`: "does not emit" 문장을 "emits a dedicated \`[정보 상충]\` response-body header tag"로 뒤집고, 상충 정보가 본문에서도 구분됨을 명시.
    - `docs/PRODUCT_SPEC.md:347, 370`: 응답 본문 헤더 목록에 `[정보 상충]` 추가.
    - `tests/test_smoke.py`: 상충 상태가 포함된 엔티티 카드 응답 본문에 `상충하는 정보 [정보 상충]:` 헤더가 실제로 나타나는지 확인하는 regression test 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k coverage`
    - `python3 -m py_compile core/agent_loop.py`
    - `git diff --check`
