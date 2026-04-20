# 2026-04-20 regressed transition wording polish

## 변경 파일
- core/agent_loop.py
- app/static/app.js
- e2e/tests/web-smoke.spec.mjs
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 grep, 좁은 `tests.test_smoke` rerun, `py_compile`, `node --check`, isolated Playwright, `git diff --check`를 실제 실행 기준으로 정리했습니다.
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경/검증/남은 리스크를 사실 기준으로 남겼습니다.

## 변경 이유
- claim-coverage focus-slot의 `regressed` 문구는 이미 서버에서 `STRONG → WEAK`를 따로 설명하기 시작했지만, `WEAK → MISSING`은 여전히 generic `약해졌습니다`로 묶여 있었고 브라우저도 모든 downgrade를 같은 문장으로 노출하고 있었습니다.
- 이번 라운드는 non-CONFLICT regressed-transition wording만 다뤄 `교차 확인 → 단일 출처`와 `단일 출처 → 미확인`을 더 구체적으로 보여 주되, 나머지 downgrade의 generic fallback은 그대로 유지하는 것이 목적이었습니다.

## 핵심 변경
- `core/agent_loop.py::_build_claim_coverage_progress_summary`의 regressed-focus loop는 loop header에서 `_cur_status`를 `cur_status`로 바꿨고, `STRONG → WEAK` 절 바로 아래에 `WEAK → MISSING` 전용 분기를 추가했습니다. 이제 `"정보를 더 이상 찾을 수 없어 … 조정되었습니다"`를 emit하고, 기존 `STRONG → WEAK` `"교차 확인 기준을 더 이상 충족하지 않아 … 조정되었습니다"`와 remaining downgrade용 generic `"약해졌습니다"` fallback은 그대로 유지합니다.
- `app/static/app.js::buildFocusSlotExplanation`의 regressed branch는 이제 `prev === "교차 확인" && curr === "단일 출처"`일 때 `"교차 확인 기준을 더 이상 충족하지 않아 단일 출처로 조정되었습니다."`, `curr === "미확인"`일 때 `"정보를 더 이상 찾을 수 없어 미확인으로 조정되었습니다."`를 우선 반환하고, 그 외 regressed transition은 기존 generic fallback을 유지합니다.
- `e2e/tests/web-smoke.spec.mjs:1770-1783`의 regressed scenario는 fixture를 바꾸지 않고 `"교차 확인 기준을 더 이상 충족하지 않아 단일 출처로 조정되었습니다"`만 assert하도록 바꿨습니다. `"추가 교차 검증이 권장됩니다"` positive assertion은 제거했습니다.
- `tests/test_smoke.py:2976-2994`에 `test_build_claim_coverage_progress_summary_focus_slot_weak_to_missing_says_information_no_longer_found`를 추가했습니다. `-k progress_summary` family 안에서 server summary가 `"재조사 결과 이용 형태는 정보를 더 이상 찾을 수 없어 미확인으로 조정되었습니다."`를 정확히 내고, stale `"약해졌습니다"`나 `"교차 확인 기준"` wording으로 섞이지 않는지 고정합니다.
- `_annotate_claim_coverage_progress`는 의도적으로 수정하지 않았습니다. 이 helper의 `progress_label`은 이미 `교차 확인 해제`와 `약해짐`을 구분하고 있고, 이번 라운드는 summary-sentence builder만 바꿨습니다.
- seq 408/411/414/417/420/423/427 shipped surface는 의도적으로 건드리지 않았습니다.

## 검증
- `rg -n '약해졌습니다' core/ app/ tests/ e2e/`
  - 결과: `core/agent_loop.py` generic fallback 1건, `app/static/app.js` generic fallback 1건, `tests/test_smoke.py`의 negative guard 2건과 explanatory docstring 1건만 hit. old regressed wording을 positive assertion으로 고정한 추가 scenario/doc 문장은 없었습니다.
- `rg -n '추가 교차 검증이 권장됩니다' app/ e2e/`
  - 결과: `app/static/app.js` generic fallback 1건과 unresolved weak-state copy 1건, `e2e/tests/web-smoke.spec.mjs:1703`의 unresolved weak-state scenario 1건만 hit. 이번에 바꾼 regressed scenario(`:1770-1783`)에는 더 이상 이 assertion이 남아 있지 않습니다.
- `rg -n '정보를 더 이상 찾을 수 없어|교차 확인 기준을 더 이상 충족하지 않아' core/ app/ tests/ e2e/`
  - 결과: server new clause 1건, client specific literals 2건, 새 smoke regression 1건, updated Playwright assertion 1건만 hit.
- `rg -n '단일 출처로 조정되었습니다|미확인으로 조정되었습니다' app/ e2e/ tests/`
  - 결과: client literals 2건, Playwright assertion 1건, 새 smoke regression 1건만 hit.
- `rg -n '약해졌습니다|추가 교차 검증이 권장됩니다|교차 확인 기준을 더 이상 충족하지 않아|정보를 더 이상 찾을 수 없어' docs/`
  - 결과: hit 없음. old regressed wording을 literal로 적은 docs 문장은 찾지 못했습니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 7 tests in 0.036s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.002s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 21 tests in 0.112s`, `OK`  
    handoff의 seq 423 기대값은 20건이었지만, 현재 dirty tree 기준 실제 실행 수는 21건이었습니다. 실패나 assertion flip은 없었습니다.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.125s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `node --check app/static/app.js`
  - 결과: 출력 없음, 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다" --reporter=line`
  - 결과: `1 passed (7.9s)`
- `git diff --check -- core/agent_loop.py app/static/app.js e2e/tests/web-smoke.spec.mjs tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `python3 -m unittest tests.test_web_app`, `make e2e-test`는 이번 slice 범위 밖이라 실행하지 않았습니다.

## 남은 리스크
- Milestone 4 남은 sub-candidate E2(entity-card strong-badge downgrade edge)는 이후 라운드 후보로 남아 있습니다.
- docs grep에서는 old regressed wording literal hit가 없었습니다. 따라서 오늘(2026-04-20) docs-only round count는 계속 0이고, 별도 docs follow-up은 현재로서는 필요 근거를 찾지 못했습니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 밖에 그대로 남아 있습니다.
