# 2026-04-20 progress summary G2 followup

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- seq 441/444에서 client hint는 `support_plurality`와 `trust_tier`를 이미 읽고 있었지만, `claim_coverage_progress_summary`를 만드는 server helper는 여전히 그 내부 신호를 반영하지 않아 focus STRONG mixed-trust와 non-focus WEAK multi-source 요약 문장이 실제 데이터보다 둔하게 남아 있었습니다.
- 이번 라운드는 handoff가 좁힌 G2-followup 범위대로 `_build_claim_coverage_progress_summary` 내부 두 surface만 고쳤습니다. STRONG non-focus mixed-trust와 focus steady STRONG은 일부러 defer해 summary helper shape를 더 크게 넓히지 않았습니다.

## 핵심 변경
- `core/agent_loop.py::_build_claim_coverage_progress_summary`는 `current_trust_tier_map`를 새로 만들고, `unresolved_slots`를 `(slot, label, status, support_plurality, trust_tier)` 5-tuple로 확장했습니다. focus-slot improved-to-STRONG branch에서는 `current_trust_tier_map.get(focus_slot) == "mixed"`일 때만 `"보강되었으나 공식/위키/데이터 소스가 약합니다."` 문구를 반환합니다.
- 같은 helper 안에 `_claim_coverage_non_focus_summary_label`를 추가했고, non-focus summary comprehension 두 곳에서 WEAK + `support_plurality == "multiple"`일 때만 `label` token을 `"여러 출처 확인"`으로 바꾸도록 했습니다. overall sentence template `"재조사했지만 아직 {unresolved_summary} 상태입니다."`는 그대로 유지했습니다.
- STRONG non-focus mixed-trust는 이번 라운드에서 DEFERRED입니다. 새 `mixed_trust_slots` collection은 만들지 않았고, `unresolved_slots` guard도 그대로 `{CONFLICT, WEAK, MISSING}`만 유지했습니다.
- focus-slot steady STRONG case도 그대로입니다. improved loop에서만 mixed-trust variant를 넣었고, rank change가 없는 STRONG focus slot은 이번 라운드에서 새 분기를 추가하지 않았습니다.
- `tests/test_smoke.py`에는 `test_build_claim_coverage_progress_summary_surfaces_mixed_trust_focus_strong_and_non_focus_weak_multi_source`를 `test_build_claim_coverage_progress_summary_focus_slot_weak_multi_source_emits_multi_source_wording` 바로 다음에 추가했습니다. 한 테스트에서 mixed-trust focus STRONG improvement, trusted focus STRONG improvement, non-focus WEAK multi-source token swap 세 fixture를 함께 고정했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444 shipped surface는 의도적으로 수정하지 않았습니다. serializer, client branches, Playwright scenarios, legend text도 이번 라운드에서는 손대지 않았습니다. 이번 slice는 server-only입니다.

## 검증
- `rg -n "current_trust_tier_map|_claim_coverage_non_focus_summary_label" core/ tests/`
  - 결과: helper definition 1건, `current_trust_tier_map` 생성 1건, `unresolved_slots.append`의 trust read 1건, focus STRONG mixed-trust read 1건, helper call site 2건이 hit했습니다.
  - handoff 설명과 달리 이 grep pattern 자체는 tuple unpack line을 직접 매치하지 않아 5-tuple unpack line들은 여기 잡히지 않았습니다.
- `rg -n "보강되었으나 공식/위키/데이터 소스가 약합니다|여러 출처 확인" core/ tests/`
  - 결과: `core/agent_loop.py`의 mixed-trust focus STRONG sentence 1건, helper literal `"여러 출처 확인"` 1건, 새 `tests/test_smoke.py` regression의 `"개발 여러 출처 확인"` assertion 1건이 hit했습니다.
- `rg -n "교차 확인 기준을 충족했습니다" core/ tests/`
  - 결과: 기존 trusted-STRONG focus sentence(`core/agent_loop.py`) 1건, 새 Fixture B assertion 1건, 새 Fixture A negative assertion 1건이 hit했습니다. 기존 core sentence hit는 유지됐고 count는 줄지 않았습니다.
- `rg -n "unresolved_slots" core/agent_loop.py`
  - 결과: 이번 helper 바깥의 기존 `unresolved_slots` 이름 사용도 함께 hit됐습니다.
  - 이번 수정과 직접 관련된 hit는 annotation 1건, append 1건, focus unresolved unpack 1건, two comprehension unpack 2건, `if unresolved_slots` guard 2건입니다. 수정 대상 구간의 tuple은 모두 5-tuple로 맞춰졌습니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 9 tests in 0.017s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 25 tests in 0.053s`, `OK`
  - handoff baseline 24에서 25로 늘었습니다. 새 test name에 `claim_coverage`가 들어 있어 `-k coverage` subset에도 매칭되기 때문입니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.000s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.051s`, `OK`
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.071s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `node --check app/static/app.js`, Playwright, `make e2e-test`, full `tests.test_web_app`는 이번 라운드가 server-only이고 browser helper/contract를 넓히지 않아 실행하지 않았습니다.

## 남은 리스크
- STRONG non-focus mixed-trust는 non-focus summary에서 여전히 silent합니다. 이후 별도 arbitration에서 `mixed_trust_slots`를 도입할지, 아니면 `unresolved_slots` semantics를 넓힐지 더 안전한 쪽을 다시 골라야 합니다.
- focus-slot steady STRONG mixed-trust(no rank change)도 summary에서는 여전히 silent합니다.
- unrelated full `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 계속 0입니다. 이번 라운드는 server-only라 docs drift를 추가하지 않았습니다.
- dirty worktree의 다른 파일들은 이번 라운드에서 건드리지 않았습니다.
