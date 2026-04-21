# 2026-04-20 progress summary G2 deferred A

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- seq 447까지는 server summary가 focus STRONG mixed-trust와 non-focus WEAK multi-source만 반영했고, non-focus STRONG mixed-trust는 계속 silent였습니다.
- 이번 라운드는 Gemini 449 advice의 Option (i)대로 `mixed_trust_slots`를 별도 collection으로 추가해, 기존 `unresolved_slots` 의미를 유지하면서 non-focus summary에만 STRONG mixed-trust를 surfacing하는 좁은 server-only slice를 닫는 것이 목표였습니다.

## 핵심 변경
- `core/agent_loop.py::_claim_coverage_non_focus_summary_label`는 이제 `trust_tier` 인자를 추가로 받고, `status == CoverageStatus.STRONG and trust_tier == "mixed"`일 때 `"교차 확인(출처 약함)"`을 반환합니다. 기존 WEAK + multiple 분기와 default branch는 그대로 유지했습니다.
- `_build_claim_coverage_progress_summary`는 `unresolved_slots`와 나란히 `mixed_trust_slots` collection을 새로 선언하고, `current_status == CoverageStatus.STRONG and current_trust_tier_map.get(slot, "") == "mixed"`일 때만 같은 5-tuple shape로 append합니다. `unresolved_slots` guard는 그대로 `{CONFLICT, WEAK, MISSING}`로 유지했습니다.
- 비포커스 두 summary comprehension은 이제 `unresolved_slots + mixed_trust_slots`를 먼저 합친 뒤 `[:2]` / `[:3]`로 자르고, helper 호출에 `trust_tier`를 같이 넘깁니다. 문장 템플릿 `"재조사 결과 {improved_summary}로 보강되었습니다. 아직 {unresolved_summary} 상태의 슬롯이 남아 있습니다."`와 `"재조사했지만 아직 {unresolved_summary} 상태입니다."`는 그대로 보존했습니다.
- 새 regression `test_build_claim_coverage_progress_summary_surfaces_non_focus_strong_mixed_trust_via_combined_summary`를 `test_build_claim_coverage_progress_summary_surfaces_mixed_trust_focus_strong_and_non_focus_weak_multi_source` 바로 다음에 추가했습니다. bare-unresolved path에서 genuine unresolved slot이 mixed-trust slot보다 먼저 오고, mixed-trust slot이 `"개발 교차 확인(출처 약함)"`으로 surfacing되는지 고정합니다.
- step 6 sanity는 green으로 유지됐습니다. `tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`를 수정 없이 다시 돌렸고 통과했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447 shipped surface는 의도적으로 수정하지 않았습니다. serializer, client branch, Playwright scenario, legend text도 이번 라운드에서는 건드리지 않았고, G2-deferred-B(focus-slot steady STRONG)는 계속 deferred 상태입니다.

## 검증
- `rg -n "_claim_coverage_non_focus_summary_label" core/ tests/`
  - 결과: helper definition 1건, `_build_claim_coverage_progress_summary` 내부 call site 2건이 hit했습니다. test 파일의 직접 hit는 없었습니다.
- `rg -n "mixed_trust_slots" core/ tests/`
  - 결과: declaration 1건, append 1건, `combined_unresolved_slots = unresolved_slots + mixed_trust_slots` 2건이 hit했습니다.
- `rg -n "교차 확인\\(출처 약함\\)" core/ tests/`
  - 결과: helper return literal 1건, 새 regression assertion 2건이 hit했습니다.
- `rg -n "unresolved_slots" core/agent_loop.py`
  - 결과: 이번 target block의 annotation 1건, append 1건, focus unresolved unpack 1건, combined-list 2건과 comprehension unpack 2건이 hit했습니다.
  - 같은 파일 다른 함수의 기존 `unresolved_slots` 사용(`4210`, `4220`, `4795`, `4867`, `4870`)도 함께 hit했습니다.
- `rg -n "if unresolved_slots:" core/agent_loop.py`
  - 결과: target sites D/E에서는 0건으로 정리됐지만, 파일 다른 위치의 기존 `if unresolved_slots:` 1건(`4867`)이 여전히 hit했습니다.
  - handoff 기대치와 달리 완전 0건은 아니었지만, 이번 slice 범위 밖의 기존 코드라 건드리지 않았습니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 10 tests in 0.019s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 26 tests in 0.064s`, `OK`
  - 새 test name에 `claim_coverage_progress_summary`가 포함되어 `-k coverage` subset에도 매칭되면서 25 → 26으로 늘었습니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.069s`, `OK`
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.071s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `node --check app/static/app.js`, Playwright, `make e2e-test`, full `tests.test_web_app`는 이번 라운드가 server-only이고 browser/helper contract를 넓히지 않아 실행하지 않았습니다.

## 남은 리스크
- G2-deferred-B는 아직 열려 있습니다. focus-slot steady STRONG mixed-trust는 summary에서 여전히 silent합니다.
- mixed-only summary는 `"아직 {slot} 교차 확인(출처 약함) 상태입니다"`처럼 약간 어색한 문장을 만들 수 있습니다. 이후 β arbitration에서 필요하면 sentence template 자체를 다시 설계해야 합니다.
- unrelated full `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 계속 0입니다.
- dirty worktree의 다른 파일들은 이번 라운드에서 건드리지 않았습니다.
