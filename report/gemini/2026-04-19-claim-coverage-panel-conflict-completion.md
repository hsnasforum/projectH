# 2026-04-19 Claim-coverage panel CONFLICT surface completion arbitration

## 중재 배경
- seq 408~411을 통해 응답 본문 헤더와 `근거 출처:` 영역까지 `CONFLICT` ("정보 상충") 가시성이 확보됨.
- 그러나 사이드바의 `claim-coverage panel`은 여전히 `conflict_claims` 버킷을 버리고 (`_`로 처리) 상충 슬롯을 "미확인" 또는 "본문 미반영"과 유사하게 취급하고 있음.
- 이는 사용자가 패널에서 각 슬롯의 상태를 확인할 때 응답 본문의 "상충 정보"와 패널의 상태 정보 간의 괴리를 느끼게 하는 마지막 정합성 공백임.

## 결정 및 권고
- **RECOMMEND: implement Claim-coverage panel conflict surface — panel-side rendered_as / wording polish (Option A)**
- **결정 이유**:
    - "Priority 2: same-family user-visible improvement" 원칙에 따라 CONFLICT family의 UI 가시성을 최종적으로 완결함.
    - 패널의 각 슬롯이 응답 본문에 어떻게 반영되었는지 (`rendered_as`)를 보여주는 계약에 "상충 정보 반영" 상태를 추가하여 시스템 전체의 신뢰도를 높임.
    - `core/agent_loop.py`의 `_build_entity_claim_coverage_items`가 이미 존재하는 `_claim_coverage_status_label`을 활용하도록 개선하여 하드코딩된 한글 문자열 중복을 제거함.

## 상세 가이드 (Option A 기반)
- **수정 대상 파일**:
    - `core/agent_loop.py`
    - `app/static/app.js`
    - `tests/test_smoke.py`
- **범위 제한**:
    - `core/agent_loop.py`:
        1. `_build_entity_claim_coverage_items` 시그니처에 `conflict_claims: list[ClaimRecord]` 추가 및 `conflict_slots` 집합 정의.
        2. `status_label` 결정 시 `self._claim_coverage_status_label(status)` 도우미 함수를 사용하도록 수정.
        3. `slot in conflict_slots`인 경우 `rendered_as = "conflict"`로 설정.
        4. `_select_entity_fact_card_claims` 호출부(6236, 6510행 등)에서 `conflict_claims`를 캡처하여 전달.
    - `app/static/app.js`:
        1. `formatClaimRenderedAs` 함수에 `normalized === "conflict"` 분기 추가 및 `"상충 정보 반영"` 반환.
    - `tests/test_smoke.py`: 패널 데이터(`claim_coverage` 페이로드) 내의 CONFLICT 슬롯이 올바른 `status_label` ("정보 상충")과 `rendered_as` ("conflict") 값을 가지는지 확인하는 regression test 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_smoke -k coverage`
    - `python3 -m py_compile core/agent_loop.py`
    - `git diff --check`
