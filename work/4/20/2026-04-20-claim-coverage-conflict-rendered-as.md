# 2026-04-20 claim coverage conflict rendered as

## 변경 파일
- core/agent_loop.py
- app/static/app.js
- tests/test_smoke.py
- docs/ARCHITECTURE.md
- docs/PRODUCT_SPEC.md

## 사용 skill
- doc-sync: `claim_coverage.rendered_as` payload literal이 4개로 넓어져서 handoff가 지정한 `docs/ARCHITECTURE.md:220`, `docs/PRODUCT_SPEC.md:267` 두 문장을 같은 라운드에서 구현과 맞췄습니다.
- release-check: handoff가 요구한 `tests.test_smoke` 중심 검증, `py_compile`, `git diff --check`, 기존 CONFLICT-slot assertion/문서 drift grep를 실제 실행 기준으로 정리했습니다.
- work-log-closeout: 오늘 날짜 `work/4/20/` 경로에 표준 섹션 순서로 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 411까지도 entity-card `claim_coverage` payload는 CONFLICT slot을 panel-side에서 별도 `rendered_as` 값으로 표면화하지 못했고, `_build_entity_claim_coverage_items`의 `status_label`도 CONFLICT를 무시한 채 `"교차 확인"` / `"단일 출처"` / `"미확인"` 하드코딩 일부에 머물러 있었습니다.
- 이번 handoff 목표는 CONFLICT slot이 panel payload에서 `rendered_as = "conflict"`와 `status_label = "정보 상충"`으로 드러나도록 helper와 두 callsite를 연결하고, browser formatter와 문서 2줄까지 같은 라운드에서 동기화하는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py:4222-4276`의 `_build_entity_claim_coverage_items` signature는 이제 `primary_claims`, `conflict_claims`, `weak_claims` 순으로 받습니다. 내부에 `conflict_slots`를 추가했고, `rendered_as` 결정 순서는 `strong -> conflict -> weak -> not_rendered`로 고정했습니다.
- 같은 함수에서 `status_label`은 이제 populated branch와 `primary_claim is None` branch 모두 `self._claim_coverage_status_label(...)`를 사용합니다. 이로써 함수 본문 안의 하드코딩 `"교차 확인"` / `"단일 출처"` / `"미확인"` literal이 사라지고, CONFLICT는 canonical label `"정보 상충"`을 그대로 탑니다.
- `core/agent_loop.py:6246-6255`, `core/agent_loop.py:6521-6530` 두 callsite는 seq 408 5-tuple에서 `conflict_claims`를 unpack해 `_build_entity_claim_coverage_items`로 전달하도록 바뀌었습니다.
- `app/static/app.js:2406-2412`의 `formatClaimRenderedAs`는 이제 `"conflict"`에 대해 `"상충 정보 반영"`을 반환합니다. 기존 `"fact_card"`, `"uncertain"`, `"not_rendered"` 분기는 그대로 유지했습니다.
- 문서는 `docs/ARCHITECTURE.md:220`, `docs/PRODUCT_SPEC.md:267` 두 문장만 수정해 `rendered_as` enumeration을 `fact_card / conflict / uncertain / not_rendered` 4개 literal로 넓혔습니다. 다른 문장은 수정하지 않았습니다.
- 새 회귀는 `tests/test_smoke.py:1206-1281`의 `test_coverage_entity_card_claim_coverage_payload_marks_conflict_slot_with_conflict_rendered_as`이며, seq 408/411 CONFLICT 회귀 바로 아래에 배치했습니다. step 6 grep(`rg -n 'status_label.*단일 출처|정보 상충|rendered_as.*conflict|rendered_as.*uncertain|rendered_as.*not_rendered' tests/test_smoke.py`) 기준으로 기존 CONFLICT-slot silent-bug outcome을 기대하던 assertion은 없어서 기존 test flip은 하지 않았습니다.
- seq 408/411 shipped CONFLICT chain surface, regex canonicalization(`core/agent_loop.py:5763-5776`), alternate builder(`core/agent_loop.py:5924-5939`), `_ROLE_PRIORITY`(server와 seq 411 synced maps 포함), response-body header emission, browser/e2e/test_web_app 파일은 의도적으로 수정하지 않았습니다.

## 검증
- `rg -n 'status_label.*단일 출처|정보 상충|rendered_as.*conflict|rendered_as.*uncertain|rendered_as.*not_rendered' tests/test_smoke.py`
  - 결과: 새 CONFLICT payload regression과 기존 helper label/assertion들만 확인됐고, 기존 CONFLICT-slot을 `"단일 출처"` 또는 non-`"conflict"` rendered_as로 고정한 assertion은 보이지 않았습니다.
- `rg -n 'rendered_as' docs`
  - 결과: enumeration을 직접 적는 root docs hit는 `docs/ARCHITECTURE.md:220`, `docs/PRODUCT_SPEC.md:267` 두 줄뿐이었고, `docs/ACCEPTANCE_CRITERIA.md:48`은 weak/missing subset 설명(`rendered_as = "uncertain"`)이라 3-literal enumeration drift는 아니었습니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 19 tests in 0.064s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.000s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py app/static/app.js tests/test_smoke.py docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md`
  - 결과: 출력 없음, 통과
- Playwright, `python3 -m unittest tests.test_web_app`, `make e2e-test`는 실행하지 않았습니다. 이번 slice는 server-emitted payload data, formatter 문자열 1곳, 문서 2줄만 바꾸며 shared browser helper contract나 browser flow 범위를 넓히지 않았습니다.

## 남은 리스크
- Milestone 4의 남은 후보는 여전히 separate future round로 남아 있습니다. 예를 들면 seq 408 header + seq 411 source-line + 이번 panel `rendered_as` literal을 함께 보는 optional Playwright scenario, COMMUNITY/PORTAL/BLOG weighting, reinvestigation threshold tuning, strong-vs-weak-vs-unresolved 추가 polish가 있습니다.
- 현재 root docs에서 `rendered_as`를 3 literal로 나열한 추가 문장은 grep상 보이지 않았습니다. 이후 다른 문서 drift가 발견되면 오늘(2026-04-20)은 docs-only round count가 0이므로 narrow docs-only follow-up round를 열 수 있습니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family는 이번 slice 밖의 dirty-state 영역으로 그대로 남아 있습니다.
