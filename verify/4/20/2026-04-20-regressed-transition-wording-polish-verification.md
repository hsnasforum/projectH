# 2026-04-20 regressed transition wording polish verification

## 변경 파일
- `verify/4/20/2026-04-20-regressed-transition-wording-polish-verification.md`

## 사용 skill
- `round-handoff`: seq 430 `/work`(`work/4/20/2026-04-20-regressed-transition-wording-polish.md`)의 Milestone 4 Option E3 주장을 `core/agent_loop.py`, `app/static/app.js`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_smoke.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(progress_summary / claims / coverage / reinvestigation smoke family + `py_compile` + `node --check` + isolated Playwright)을 직접 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 430 `.pipeline/claude_handoff.md`(Gemini 429 advice E3 기반)가 구현되어 새 `/work` 노트가 제출되었습니다. 이 라운드의 목표는 focus-slot `regressed` 문구를 서버·클라이언트 양쪽에서 `WEAK → MISSING`과 `교차 확인 → 단일 출처` 두 전이에 대해 구체적으로 분기하고, 기존 generic `약해졌습니다` fallback은 remaining downgrade용으로 보존하는 것이었습니다. Playwright regressed scenario 문자열도 lockstep으로 업데이트되었습니다.

## 핵심 변경
- `core/agent_loop.py:4467-4488` `_build_claim_coverage_progress_summary` regressed-focus loop
  - 루프 헤더가 `for slot, previous_label, current_label, prev_status, cur_status in regressed_slots:` 로 `_cur_status` → `cur_status` 리네임 확인(`:4467`).
  - `STRONG` 분기(`:4475-4479`) 다음에 새 `if prev_status == CoverageStatus.WEAK and cur_status == CoverageStatus.MISSING:` 절(`:4480-4484`) 삽입 확인. emit 문자열은 `"재조사 결과 {slot}{focus_particle} 정보를 더 이상 찾을 수 없어 {current_label}{directional} 조정되었습니다."` 로 handoff와 자구 일치.
  - 기존 generic `약해졌습니다` fallback(`:4485-4488`)은 remaining downgrade(`CONFLICT → WEAK`, `CONFLICT → MISSING` 등)용으로 그대로 유지.
- `app/static/app.js:2441-2448` `buildFocusSlotExplanation` regressed branch
  - `if (prev === "교차 확인" && curr === "단일 출처")` → `"→ 재조사 결과: 교차 확인 기준을 더 이상 충족하지 않아 단일 출처로 조정되었습니다."` (`:2442-2444`).
  - `if (curr === "미확인")` → `"→ 재조사 결과: 정보를 더 이상 찾을 수 없어 미확인으로 조정되었습니다."` (`:2445-2447`).
  - fallback(`:2448`)은 기존 `` `→ 재조사 결과: ${prev} → ${curr}${particle} 약해졌습니다. 추가 교차 검증이 권장됩니다.` `` 그대로. improved/fallback 나머지 가지(`:2438-2440`, `:2450-2459`)는 미수정 확인.
- `e2e/tests/web-smoke.spec.mjs:1770-1783`
  - Fixture(`:1775-1777`)는 변경 없음. assertion이 `"재조사 결과"` + `"교차 확인 기준을 더 이상 충족하지 않아 단일 출처로 조정되었습니다"` 두 줄로 좁혀졌고, 이전의 `"교차 확인 → 단일 출처로 약해졌습니다"` + `"추가 교차 검증이 권장됩니다"` 라인은 제거됐습니다. 다른 시나리오(특히 seq 417 CONFLICT end-to-end `:1855-1907`)는 미수정.
- `tests/test_smoke.py:2976-2994` 새 회귀 `test_build_claim_coverage_progress_summary_focus_slot_weak_to_missing_says_information_no_longer_found` 확인.
  - 단일 슬롯 fixture(`이용 형태` `weak → missing`, query=`"붉은사막 공식 플랫폼 검색해봐"`)로 `_build_claim_coverage_progress_summary`를 호출하고, `assertEqual(summary, "재조사 결과 이용 형태는 정보를 더 이상 찾을 수 없어 미확인으로 조정되었습니다.")` 로 전체 문자열 고정. 추가로 `assertNotIn("약해졌습니다", summary)`, `assertNotIn("교차 확인 기준", summary)` 두 guard 포함. handoff가 요구한 per-substring `assertIn` guard들은 전체 문자열 `assertEqual`에 흡수되어 기능적으로 동등(오히려 더 엄격)합니다.
  - 배치 위치는 `test_build_claim_coverage_progress_summary_focus_slot_strong_to_weak_drops_generic_weaken_wording`(`:2938-2974`) 직후, `test_build_claim_coverage_progress_summary_focus_slot_weak_to_strong_reflects_trusted_agreement`(`:2996-3024`) 직전으로, handoff의 "WEAK→STRONG 직후·CONFLICT-unresolved 직전" 지시와는 다르게 WEAK→STRONG 바로 앞에 놓였습니다. 기능적·semantic 영향은 없고 adjacent downgrade/upgrade 테스트 묶음이 유지되나, handoff 자구와의 placement drift는 `남은 리스크`에 기록합니다.
- `_annotate_claim_coverage_progress`(`core/agent_loop.py:4279-4339`)와 `_build_entity_claim_source_lines::support_refs.sort`(`:4557`)는 의도적으로 미수정. `core/web_claims.py`, `app/serializers.py`, `storage/`, 다른 `app/static/*`, docs, agent-config 파일도 이번 라운드에서 수정되지 않았습니다.
- handoff가 금지한 shipped surface는 보존됐습니다: seq 385/400/405 focus-slot 템플릿, seq 408 5-tuple + response-body header, seq 411 source-line + role_priority sync, seq 414 `_build_entity_claim_coverage_items` + `rendered_as=conflict`, seq 417 Playwright CONFLICT 시나리오, seq 420 `_ROLE_PRIORITY` positions, seq 423 reinvestigation overall cap, seq 427 sort-key 6-tuple.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `430` — 이미 shipped 됐고 새로운 `/work`로 consumed.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `428` — seq 429 advice로 이미 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `429` — seq 430 handoff로 이미 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — seq 423/427/430 shipping으로 자연 해제 상태 유지. 남은 real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조
  - `core/agent_loop.py:4467-4488` 서버 신규 WEAK→MISSING 분기와 loop 변수 rename 확인.
  - `app/static/app.js:2441-2448` 클라이언트 3-way 분기 확인.
  - `e2e/tests/web-smoke.spec.mjs:1770-1783` Playwright assertion 업데이트 확인.
  - `tests/test_smoke.py:2976-2994` 새 회귀 구조·문자열 확인.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 7 tests in 0.015s`, `OK`. 기존 6건(`test_build_claim_coverage_progress_summary_focus_slot_strong_to_weak_*`, `_weak_to_strong_*`, `_conflict_stays_unresolved`, `_unresolved_wording_branches_by_status`, `test_annotate_claim_coverage_progress_focus_slot_strong_boundary_labels_are_specific`, legacy progress summary canonicalization 관련 1건) + 신규 1건.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`. seq 427 baseline 유지.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 21 tests in 0.060s`, `OK`. handoff 기대값은 20건이었지만 현 작업 트리 실제 매칭은 21건으로, `/work` 노트의 수치와 일치합니다. failure/flipped assertion 없음.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.056s`, `OK`. seq 423 baseline 유지.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `node --check app/static/app.js`
  - 결과: 출력 없음, 통과.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다" --reporter=line`
  - 결과: `1 passed (5.7s)`. browser-visible 새 문자열 실렌더 확인.
- `git diff --check -- core/agent_loop.py app/static/app.js e2e/tests/web-smoke.spec.mjs tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `make e2e-test`, `python3 -m unittest tests.test_web_app`는 이번 slice 범위 밖이라 돌리지 않았습니다. 이번 라운드는 하나의 focus-slot regressed scenario 문구만 바꿨고 shared browser helper / selector / 위젯 계약은 건드리지 않았습니다.

## 남은 리스크
- **테스트 배치 drift (기능 무영향)**: handoff seq 430은 새 회귀를 `test_...weak_to_strong_reflects_trusted_agreement`(끝 `:3004`) 직후, `test_...conflict_stays_unresolved`(시작 `:3006`) 직전에 놓도록 지시했습니다. 실제 배치는 `test_...strong_to_weak_drops_generic_weaken_wording`(끝 `:2974`) 직후, `test_...weak_to_strong_reflects_trusted_agreement` 직전(`:2976-2994`)입니다. 테스트 실행·어서션·실제 동작 모두 동일하고 adjacent downgrade/upgrade 묶음은 유지되지만, 자구 placement는 handoff와 다릅니다. 다음 라운드에서 관련 테스트 영역을 건드릴 때 재조정 고려 가능.
- **Milestone 4 남은 sub-candidate E2**(entity-card strong-badge downgrade edge)는 여전히 별도 라운드 몫입니다. E2는 single file + `:line` + symbol + 경계가 단독으로 pinned 되어 있지 않아(`_claim_coverage_status_label` vs `_build_entity_claim_coverage_items` 두 후보 site + 현재 shipped fixture에서 관찰 가능 여부 불확실) slice_ambiguity 성격이라, 다음 control은 `.pipeline/gemini_request.md`(seq 431)로 arbitration을 먼저 여는 편이 rule에 맞습니다. E1 + E3 소비 이후 Milestone 4가 사실상 마지막 E 후보까지 좁혀져 있고, E2가 현재 fixture에서 실제로 관찰 가능한지에 대한 증거가 약하면 Gemini가 E2 대신 "Milestone 4 close + 새 축 제안" 쪽으로 안내할 수도 있습니다.
- **docs grep 결과**: old regressed wording(`약해졌습니다`, `추가 교차 검증이 권장됩니다`, 새 specific 문구들)을 literal로 언급한 docs 문장은 찾지 못했습니다. 오늘(2026-04-20) docs-only round count는 계속 0.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` 실패는 이번 slice 밖이며 별도 truth-sync 라운드 몫입니다.
- seq 424 `.pipeline/operator_request.md`(dispatcher_state_truth_sync)는 seq 423/427/430 shipping으로 자연 해제 상태 유지. real operator-only decision / approval blocker / 안전 정지 / Gemini 부재 어느 조건에도 해당하지 않습니다.
