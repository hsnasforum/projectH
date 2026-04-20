# 2026-04-19 response body conflict header

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py
- docs/ACCEPTANCE_CRITERIA.md
- docs/PRODUCT_SPEC.md

## 사용 skill
- doc-sync: response-body `[정보 상충]` emitted header 계약이 구현과 맞도록 handoff가 지정한 두 문서를 같은 라운드에서 동기화했습니다.
- release-check: handoff가 요구한 `tests.test_smoke` 중심 검증, `py_compile`, `git diff --check`, grep 확인을 실제 실행 기준으로 정리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서로 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- claim-coverage surface와 history/meta 쪽에는 이미 `정보 상충` 상태가 살아 있었지만, entity-card response body는 여전히 `확인된 사실` / `단일 출처 정보` / `확인되지 않은 항목` 3개 헤더만 직접 배출하고 있었습니다.
- 이번 handoff 목표는 `_select_entity_fact_card_claims`가 conflict 후보를 별도 bucket으로 돌려주고, 실제 응답 본문이 strong과 weak 사이에 `상충하는 정보 [정보 상충]:` 헤더를 emitted contract로 노출하도록 맞추는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py:4148-4218`의 `_select_entity_fact_card_claims`는 이제 `(primary_claims, conflict_claims, weak_claims, supplemental_claims, unresolved_slots)` 5-tuple을 반환합니다. `CoverageStatus.CONFLICT` 슬롯은 trusted role일 때 `conflict_selected`로 분리되고, unresolved 계산에서도 covered slot로 취급됩니다.
- `core/agent_loop.py:4695-4762`의 실제 entity-card response builder인 `_build_entity_web_summary`는 이제 `conflict_claims`가 있을 때 strong section 뒤, weak section 앞에 `상충하는 정보 [정보 상충]:` 헤더를 넣고 `정보 상충, {role_label}, 확정 금지` qualifier로 본문 bullet을 씁니다. handoff 이름은 `_build_entity_card_response`였지만 현재 코드의 실제 owner 함수명은 `_build_entity_web_summary`였습니다.
- `_select_entity_fact_card_claims` callsite 3곳 중 response builder는 5개 모두 받고, claim-coverage panel 계산 경로 2곳은 `primary_claims, _, weak_claims, _, _`로 맞춰 tuple shape만 동기화했습니다. 대상은 `core/agent_loop.py:4696`, `core/agent_loop.py:6236`, `core/agent_loop.py:6510`입니다.
- `tests/test_smoke.py:1038-1131`에 `test_coverage_entity_card_response_emits_conflict_section_header_when_conflict_slot_present`를 추가했습니다. CONFLICT fixture에서 header emitted 여부, strong < conflict < weak 순서, identifiable conflict value 노출을 확인하고, no-conflict fixture에서는 header 미노출을 같이 잠갔습니다.
- `rg -n "_select_entity_fact_card_claims\\(" tests/test_smoke.py` 기준으로 smoke test 안에는 이 helper의 old 4-tuple 직접 unpack assertion이 없어서 추가 조정은 없었습니다. 기존 3-section response-body assertion도 no-conflict fixture 두세 군데만 있었고, 새 conflict header 추가로 깨지는 기존 assertion은 없었습니다.
- 문서는 `docs/ACCEPTANCE_CRITERIA.md:49`, `docs/PRODUCT_SPEC.md:347`, `docs/PRODUCT_SPEC.md:370`만 수정해 response-body emitted header/tag enumeration을 4-tag 기준으로 맞췄습니다.
- handoff 금지 범위는 그대로 유지했습니다. `core/agent_loop.py:5763-5776` regex legacy canonicalization, `core/agent_loop.py:5924-5939` alternate response builder, `core/web_claims.py`, `storage/web_search_store.py`, browser files, `tests/test_web_app.py`, `e2e`, `_ROLE_PRIORITY`, `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/project-brief.md`는 수정하지 않았습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 17 tests in 0.064s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.001s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
  - 결과: 출력 없음, 통과
- `rg -n "_select_entity_fact_card_claims\\(|확인된 사실 \\[교차 확인\\]|상충하는 정보 \\[정보 상충\\]|단일 출처 정보 \\[단일 출처\\]|확인되지 않은 항목 \\[미확인\\]" tests/test_smoke.py`
  - 결과: 새 conflict header regression 1건과 기존 no-conflict response-body assertion만 확인됐고, old tuple-unpack smoke assertion hit는 없었습니다.
- `rg -n 'verified-vs-uncertain explanation|Response-body section headers|\\[교차 확인\\].*\\[단일 출처\\].*\\[미확인\\]|확인된 사실 \\[교차 확인\\]|상충하는 정보 \\[정보 상충\\]|단일 출처 정보 \\[단일 출처\\]|확인되지 않은 항목 \\[미확인\\]' docs`
  - 결과: 이번 라운드 target line 외에 response-body emitted header/tag enumeration이 3-tag로 남은 docs hit는 보이지 않았습니다.
- Playwright, `python3 -m unittest tests.test_web_app`, `make e2e-test`는 실행하지 않았습니다. 이번 slice는 Python response-body emission과 smoke regression, 문서 2개만 바꾸며 browser helper나 browser flow contract를 건드리지 않았습니다.

## 남은 리스크
- conflict claim은 이제 response body 본문에 별도 헤더로 노출되지만, `근거 출처:` source-line helper는 여전히 `primary_claims`, `weak_claims`, `supplemental_claims`만 직접 수집합니다. 현재는 fallback selected source와 strong/weak refs로 기본 출처 surface가 유지되지만, conflict bullet과 source-line의 1:1 대응을 더 분명히 하려면 별도 narrow slice가 필요합니다.
- claim-coverage panel 계산 경로는 handoff 지시대로 conflict bucket을 별도 surface로 넘기지 않았습니다. 현재 panel/status-summary contract는 유지되지만, conflict slot의 `rendered_as` 개선이나 richer panel wording은 이후 별도 slice로 남습니다.
- browser-visible contract는 smoke level에서만 확인했습니다. response-body header가 실제 transcript/history card UX에서 추가 copy or layout drift 없이 읽히는지는 별도 browser rerun이 있어야 완전히 닫힙니다.
