# 2026-04-19 claim coverage summary conflict full chain

## 변경 파일
- storage/web_search_store.py
- app/serializers.py
- app/static/app.js
- tests/test_web_app.py
- e2e/tests/web-smoke.spec.mjs
- docs/PRODUCT_SPEC.md
- docs/ARCHITECTURE.md

## 사용 skill
- release-check: handoff가 요구한 검증을 실제 결과와 함께 정리하고, full `tests.test_web_app` 실패가 이번 슬라이스 범위 밖임을 분리해 기록했습니다.
- work-log-closeout: `/work` closeout 형식과 필수 항목을 저장소 규약에 맞춰 정리했습니다.

## 변경 이유
- 직전 seq 373 handoff는 `app/serializers.py`와 `app/static/app.js`만 넓혀도 CONFLICT count가 브라우저에 보일 것처럼 적혀 있었지만, 실제 history-card count dict는 `storage/web_search_store.py::_summarize_claim_coverage()`가 3키로 집계해 `conflict`를 버리고 있었습니다.
- 이번 라운드는 Gemini advice 375와 seq 376 widened handoff대로 storage 집계부터 serializer, browser summary helper, 테스트/fixture, 최소 문서 문장까지 한 번에 맞춰 trusted conflict가 `정보 상충 N`으로 독립 노출되도록 닫는 것이 목적이었습니다.

## 핵심 변경
- `storage/web_search_store.py::_summarize_claim_coverage()`가 이제 `"conflict"` status도 카운트해 `{"strong","weak","missing","conflict"}` 4키 dict를 만듭니다. 이 stored 4-key dict가 `app/serializers.py`의 `claim_coverage_summary`로 그대로 흘러갑니다.
- `app/serializers.py`가 `CoverageStatus.CONFLICT`를 함께 직렬화하고, `app/static/app.js`의 `summarizeClaimCoverageCounts()` / `formatClaimCoverageCountSummary()`가 `교차 확인 N · 정보 상충 N · 단일 출처 N · 미확인 N` 순서로 렌더링하도록 맞췄습니다.
- 기존 3-part summary 문자열은 `conflict == 0`인 fixture와 실제 경로에서 그대로 유지됩니다. 새 4-part 렌더링은 non-zero `conflict`가 있는 경우에만 나타납니다.
- `tests/test_web_app.py`의 `claim_coverage_summary` 기대 dict shape를 전반적으로 `conflict: 0`까지 넓혔고, storage→serializer non-zero 경로는 `test_web_search_store_list_summaries_includes_claim_coverage_summary` / `test_web_search_history_serializer_includes_claim_coverage_summary`에서 `conflict: 1`로 고정했습니다.
- `e2e/tests/web-smoke.spec.mjs`의 `claim_coverage_summary` fixture dict도 전부 4키 shape로 넓혔습니다. 기존 assertion text는 새 CONFLICT 시나리오를 제외하면 바꾸지 않았고, 새로 `history-card summary가 non-zero conflict count를 정보 상충 segment로 렌더링합니다` 시나리오를 추가했습니다.
- `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`의 `web_search_history.claim_coverage_summary` 설명 문장만 3키에서 4키(`strong / conflict / weak / missing`)로 최소 수정했습니다.

## 검증
- `python3 -m py_compile storage/web_search_store.py app/serializers.py`
  - 결과: 통과
- `git diff --check -- storage/web_search_store.py app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, 통과
- `python3 -m unittest tests.test_web_app`
  - 결과: `FAILED (errors=37)`
  - 이번 슬라이스와 직접 관련 없는 기존 실패로 확인:
    - `LocalOnlyHTTPServer(("127.0.0.1", 0), ...)` 경로의 `PermissionError: [Errno 1] Operation not permitted`
    - SQLite-backed correction/reviewed-memory 경로의 `AttributeError: 'SQLiteSessionStore' object has no attribute '_compact_summary_hint_for_persist'`
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary tests.test_web_app.WebAppServiceTest.test_web_search_history_serializer_includes_claim_coverage_summary`
  - 결과: `Ran 2 tests in 0.016s`, `OK`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs --reporter=line`
  - 결과: `114 passed (17.1m)`

## 남은 리스크
- `renderFactStrengthBar`는 이번 라운드에서 의도적으로 건드리지 않았습니다. in-answer fact strength badge surface는 아직 `conflict`를 별도 segment로 보여주지 않으며, 별도 후속 라운드 후보입니다.
- `core/agent_loop.py`의 focus_slot CONFLICT wording은 이번 라운드에서 그대로입니다. CONFLICT 전용 설명을 더 강하게 다듬는 작업은 아직 남아 있습니다.
- full `python3 -m unittest tests.test_web_app`는 이번 슬라이스와 무관한 기존 sandbox/dirty-state 실패 때문에 녹색으로 닫히지 않았습니다. 현재 라운드의 변경 경로 자체는 focused unit 2건 + Playwright full file + py_compile + diff-check로 재확인했습니다.
