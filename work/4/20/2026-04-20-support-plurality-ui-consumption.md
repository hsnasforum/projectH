# 2026-04-20 support_plurality UI consumption

## 변경 파일
- core/agent_loop.py
- app/serializers.py
- app/static/app.js
- tests/test_smoke.py
- tests/test_web_app.py
- e2e/tests/web-smoke.spec.mjs

## 사용 skill
- e2e-smoke-triage: browser-visible claim-coverage hint 변경이라 isolated Playwright 시나리오만 추가하고 그 범위로 재실행을 고정했습니다.
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- `support_plurality == "multiple"`인 WEAK 슬롯이 UI에서 계속 `1개 출처만 확인됨` 또는 focus `단일 출처 상태`처럼 읽혀, 실제 다중 출처 약한 근거와 단일 출처 약한 근거를 구분하지 못하는 copy mismatch가 남아 있었습니다.
- seq 438이 server-internal field로만 추가한 `support_plurality`를 이번 라운드에서 opt-in consumer로 연결하되, `trust_tier`, `status_label` 4-literal set, legend, summary-bar chip은 범위 밖으로 유지하는 것이 목표였습니다.

## 핵심 변경
- `core/agent_loop.py::_build_claim_coverage_progress_summary`는 `unresolved_slots`에 `support_plurality`를 함께 실어 focus-slot WEAK branch에서만 `support_plurality == "multiple"`일 때 `아직 여러 출처가 확인되었으나 교차 확인 기준에는 미달합니다.`를 반환하게 바꿨습니다. non-focus unresolved fallback은 기존 `재조사했지만 아직 {slot} {label} 상태입니다.` wording을 그대로 유지했습니다.
- `app/serializers.py::_serialize_claim_coverage`는 기존 key 순서를 유지한 채 끝에 `support_plurality`만 추가로 내보냅니다. `trust_tier`는 이번 라운드에서도 server-internal로 남겼습니다.
- `app/static/app.js::buildFocusSlotExplanation`와 `renderClaimCoverage`는 `item.support_plurality === "multiple"`일 때만 별도 multi-source hint를 출력합니다. single-source fallback 문구는 그대로이고, legend text(`app/static/app.js:2518-2519`), `status_label` 4-literal set, summary-bar label/chip은 수정하지 않았습니다.
- `tests/test_smoke.py`에는 `test_build_claim_coverage_progress_summary_focus_slot_weak_multi_source_emits_multi_source_wording`를 추가해 focus-slot multi-source WEAK server wording을 고정했습니다. optional regression을 추가했으므로 이번 라운드의 `-k progress_summary` count는 7 -> 8로 늘었습니다.
- `tests/test_web_app.py:8594`는 multi-source가 아니라 single-source fixture였습니다. local reproduction에서 `coverage_by_slot["이용 형태"]["support_plurality"] == "single"`과 `claim_coverage_progress_summary == "재조사했지만 이용 형태는 아직 한 가지 출처의 정보로만 확인됩니다."`를 확인했고, handoff 가정과 달리 현재 checkout에서 stale였던 한 줄 assertion만 실제 single-source focus wording으로 truth-sync했습니다. multi-source wording으로 바꾸지는 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`에는 `claim_coverage_multi_source_weak_focus_slot_emits_multi_source_hint`를 same `claim_coverage` focus cluster 안, `claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다` 바로 다음에 추가했습니다.
- seq 408/411/414/417/420/423/427/430/438 shipped surface는 의도적으로 수정하지 않았습니다. `trust_tier` 소비, legend widening, summary-bar chip 변경도 이번 라운드에서 제외했습니다.

## 검증
- `rg -n "아직 한 가지 출처의 정보로만 확인됩니다" core/ tests/`
  - 결과: `core/agent_loop.py` single-source fallback 1건, `tests/test_smoke.py` single-source regression 1건만 hit했습니다. `app/` hit는 없었습니다.
- `rg -n "여러 출처가 확인되었으나 교차 확인 기준에는 미달합니다" core/ app/ tests/ e2e/`
  - 결과: `core/agent_loop.py` multi-source focus server wording 1건, `app/static/app.js` non-focus multi-source hint 1건, `tests/test_smoke.py` optional regression 1건만 hit했습니다.
  - handoff가 별도로 고정한 focus client sentence/Playwright assertion은 `재조사 대상이며 여러 출처가 확인되었으나, 아직 교차 확인 기준에는 미달합니다` literal이어서 위 grep에는 걸리지 않았고, 별도 grep으로 `app/static/app.js`, `e2e/tests/web-smoke.spec.mjs` 1건씩 확인했습니다.
- `rg -n "support_plurality" core/ app/ tests/ e2e/ docs/`
  - 결과: seq 438 기존 derivation/append/MISSING default 및 기존 internal-field regression hit에 더해, 이번 라운드의 `core/agent_loop.py` map/tuple/branch, `app/serializers.py` serializer key, `app/static/app.js` 두 consumer branch, 새 `tests/test_smoke.py` regression, 새 `e2e/tests/web-smoke.spec.mjs` scenario만 hit했습니다. `docs/` hit는 없었습니다.
- `rg -n "1개 출처만 확인됨. 교차 검증이 권장됩니다" app/ e2e/`
  - 결과: `app/static/app.js` single-source fallback 1건, 기존 single-source Playwright positive assertion 1건, 새 multi-source negative assertion 1건이 hit했습니다. multi-source fixture에 대해 이 문구를 positive로 assert하는 hit는 없었습니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 8 tests in 0.021s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 23 tests in 0.087s`, `OK`
  - handoff의 `22` 기대치와 달리 `23`이 된 이유는 이번에 추가한 optional regression test name이 `claim_coverage`를 포함해 `-k coverage` subset에도 매칭되기 때문입니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.077s`, `OK`
- `python3 -m unittest tests.test_web_app.WebAppServiceTests.test_handle_chat_entity_web_search_emits_claim_coverage_progress_summary_for_focused_reinvestigation`
  - 결과: 현재 checkout에는 `WebAppServiceTests` class가 없어 `AttributeError`로 실패했습니다.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: current checkout의 실제 대응 테스트를 재실행했고 `Ran 1 test in 0.052s`, `OK`
- local Python reproduction of the same `tests/test_web_app.py` fixture
  - 결과: `claim_coverage_progress_summary`가 `재조사했지만 이용 형태는 아직 한 가지 출처의 정보로만 확인됩니다.`로 출력됐고, `coverage_by_slot["이용 형태"]["support_plurality"] == "single"`을 확인했습니다.
- `python3 -m py_compile core/agent_loop.py app/serializers.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `node --check app/static/app.js`
  - 결과: 출력 없음, 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim_coverage_multi_source_weak_focus_slot_emits_multi_source_hint" --reporter=line`
  - 결과: `1 passed (5.0s)`
- `git diff --check -- core/agent_loop.py app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs tests/test_smoke.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `trust_tier`는 여전히 client consumer가 없습니다. G1은 이후 라운드 후보로 남아 있습니다.
- non-focus multi-source WEAK는 summary fallback에서 여전히 `단일 출처` 계열 wording으로 묶입니다. 이 텍스트는 현재 4-literal legend와 연결되어 있어 이번 라운드에서는 의도적으로 유지했고, symmetry가 필요하면 후속 slice에서 다시 다뤄야 합니다.
- unrelated full `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 변하지 않았고, 이번 browser-visible copy truth-sync 때문에 별도 docs-only follow-up을 열지는 않았습니다.
- dirty worktree의 `controller/`, `pipeline_runtime/`, `pipeline_gui/`, `storage/`, `docs/`, 과거 `/work` / `/verify` 노트는 이번 라운드에서 건드리지 않았습니다.
