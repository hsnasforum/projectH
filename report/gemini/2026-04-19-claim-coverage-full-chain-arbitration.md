# 2026-04-19 Claim Coverage Summary CONFLICT arbitration

## 중재 배경
- seq 373 (`Claim Coverage Summary CONFLICT — full browser-visible chain`) 구현 도중 `BLOCK_REASON_CODE: storage_summary_missing_conflict`로 인한 `implement_blocked` 발생.
- `storage/web_search_store.py::_summarize_claim_coverage`가 `{"strong", "weak", "missing"}` 3개 키만 하드코딩하고 있어, `CoverageStatus.CONFLICT` ("conflict") 상태가 집계에서 누락됨을 확인.
- 이에 따라 serializer 및 프론트엔드 수정만으로는 히스토리 목록에서 CONFLICT 카운터가 항상 `0`으로 표시되는 "불완전한 체인" 문제가 발생함.

## 결정 및 권고
- **RECOMMEND: implement Claim Coverage Summary CONFLICT — storage + serializer + browser full chain (widened scope)**
- **결정 이유**:
    - `GEMINI.md`의 우선순위에 따라 "user-visible improvement" (히스토리에서 정확한 상충 정보 확인)를 위해 풀 체인 구현이 필요함.
    - storage 레이어의 수정 사항(`counts` 딕셔너리에 한 키 추가)이 매우 작고 명확하여, 기존 seq 373 범위에 포함시켜도 단일 implement 라운드로 소화 가능한 "coherent slice"에 해당함.
    - 불완전한 상태로 ship한 뒤 후속 라운드에서 메우는 것보다, 처음부터 storage를 포함해 browser-visible한 결과를 내는 것이 risk reduction 측면에서 유리함.

## 상세 가이드 (Option A 기반)
- **수정 대상 파일**:
    - `storage/web_search_store.py`
    - `app/serializers.py`
    - `app/static/app.js`
    - `tests/test_web_app.py`
    - `e2e/tests/web-smoke.spec.mjs`
- **범위 제한**:
    - `storage/web_search_store.py`: `_summarize_claim_coverage`의 `counts` 초기값에 `"conflict": 0` 추가.
    - `app/serializers.py`: `_serialize_web_search_history` 등에서 `conflict` 키 처리.
    - `app/static/app.js`: `formatClaimCoverageCountSummary` 등에서 `정보 상충 N` 렌더링.
    - `tests/test_web_app.py`: `claim_coverage_summary` 딕셔너리 형태 검증에 `conflict` 키 추가 및 단언문 보강.
    - `e2e/tests/web-smoke.spec.mjs`: Playwright fixture 및 assertions에 `conflict` 필드 반영 및 시나리오 추가.
- **검증 명령**:
    - `python3 -m unittest tests.test_web_app`
    - `python3 -m py_compile storage/web_search_store.py app/serializers.py`
    - `cd e2e && npx playwright test tests/web-smoke.spec.mjs --reporter=line`
    - `git diff --check`
