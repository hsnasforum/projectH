# 2026-04-20 claim coverage internal trust support fields

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 실행한 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- Milestone 4 Option E2b-α handoff는 `_build_entity_claim_coverage_items`의 기존 `status_label` 4-literal set과 기존 key shape를 유지한 채, 이후 UI가 opt-in으로 읽을 수 있는 내부 신호만 additive하게 늘리도록 지시했습니다.
- 이번 라운드는 browser-visible surface를 건드리지 않고 coverage item마다 `trust_tier`와 `support_plurality`를 추가해, E2 strong-badge edge를 새 `status_label` literal 없이 future UI가 해석할 수 있는 기반만 마련하는 것이 목적이었습니다.

## 핵심 변경
- `core/agent_loop.py::_build_entity_claim_coverage_items`는 이제 모든 coverage-item dict 끝에 `trust_tier`, `support_plurality`를 additive하게 append합니다. 기존 key 이름, key 순서, `status_label` literal set(`교차 확인` / `정보 상충` / `단일 출처` / `미확인`), `status`, `rendered_as`, `support_count`, `candidate_count`는 바꾸지 않았습니다.
- MISSING branch에도 `"trust_tier": ""`, `"support_plurality": ""`를 끝에 추가해 item shape를 uniform하게 맞췄습니다.
- STRONG 항목의 `trust_tier` trusted-role set은 정확히 `{SourceRole.OFFICIAL, SourceRole.DATABASE, SourceRole.WIKI}`로 두어 seq 420 tier-4 parity를 유지했습니다. `support_plurality`는 `primary_claim.support_count >= 2`를 기준으로 계산하며 `candidate_count`는 사용하지 않았습니다.
- `tests/test_smoke.py`에는 `test_build_entity_claim_coverage_items_emits_trust_tier_and_support_plurality_internal_fields`를 coverage cluster에 추가했습니다. 기존 `test_coverage_entity_card_claim_coverage_payload_marks_conflict_slot_with_conflict_rendered_as` 바로 뒤에 두고, STRONG trusted / STRONG mixed / WEAK multiple / WEAK single과 MISSING key presence까지 한 번에 고정했습니다.
- seq 408/411/414/417/420/423/427/430 shipped surface는 의도적으로 수정하지 않았습니다. `_annotate_claim_coverage_progress`, `_claim_coverage_status_label`, client `buildFocusSlotExplanation`, `app/static/app.js:2518` legend text, Playwright scenarios, docs도 건드리지 않았습니다. β / γ surface coordination은 α 범위 밖이라 이번 라운드에 제외했습니다.
- 이번 구현은 advice 437 기준 Milestone 4 refinement를 닫는 α slice입니다. 다음 권장 축은 G(axis rotation)지만, 그 선택은 이후 arbitration 라운드 몫입니다.

## 검증
- `rg -n "trust_tier|support_plurality" core/ app/ tests/ e2e/ docs/`
  - 결과: `core/agent_loop.py`의 MISSING branch 기본값 2건, STRONG/WEAK derivation 6건, main append 2건, `tests/test_smoke.py`의 새 회귀/어서션만 hit했습니다. `app/`, `e2e/`, `docs/` hit는 없었습니다.
- `rg -n "_build_entity_claim_coverage_items" core/ tests/`
  - 결과: `core/agent_loop.py` helper definition 1건과 existing call site 2건, `tests/test_smoke.py`의 기존 regression call 1건, 새 test definition 1건, 새 regression call 1건만 hit했습니다. helper가 server-internal이라는 전제와 맞게 예상 범위를 벗어난 hit는 없었습니다.
- `rg -n "SourceRole\.(OFFICIAL|DATABASE|WIKI)" core/agent_loop.py`
  - 결과: 기존 OFFICIAL guard들, 기존 role-weight/priority map들, 새 trusted-role set literal(`SourceRole.OFFICIAL`, `SourceRole.DATABASE`, `SourceRole.WIKI`)만 hit했습니다. set literal은 handoff가 고정한 exact trio 그대로입니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 22 tests in 0.074s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 7 tests in 0.019s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.086s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `npx playwright test`, `make e2e-test`, `python3 -m unittest tests.test_web_app`는 이번 α slice가 browser-visible contract를 바꾸지 않아 실행하지 않았습니다.

## 남은 리스크
- 현재 downstream UI consumer는 `trust_tier`나 `support_plurality`를 읽지 않습니다. 이번 라운드는 future opt-in field만 추가했으며, client legend / hint / Playwright 변화는 α 범위 밖이라 landed change가 없습니다.
- Milestone 4의 남은 sub-candidate E2(entity-card strong-badge downgrade edge)는 α signalling path에 흡수되었습니다. 이후 UI가 `trust_tier == "mixed"`를 읽으면 새 `status_label` literal 없이도 해당 edge를 표현할 수 있습니다.
- unrelated full `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 이전과 동일하게 0이며, 이번 server-only additive change 때문에 별도 docs-only follow-up은 트리거되지 않았습니다.
