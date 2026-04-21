# 2026-04-20 trust_tier UI consumption

## 변경 파일
- app/serializers.py
- app/static/app.js
- tests/test_smoke.py
- e2e/tests/web-smoke.spec.mjs

## 사용 skill
- e2e-smoke-triage: claim-coverage panel의 text-only hint 변경이라 isolated Playwright 시나리오 1건만 추가하고 그 범위로 재실행을 고정했습니다.
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- seq 438이 server-internal field로만 추가한 `trust_tier`는 seq 441 이후에도 UI consumer가 없어, STRONG이지만 supporting source가 `{OFFICIAL, DATABASE, WIKI}`와 겹치지 않는 `"mixed"` 케이스가 사용자에게 plain `교차 확인`으로만 보이고 있었습니다.
- 이번 라운드는 G1 범위대로 `trust_tier`를 opt-in pass-through + per-slot text hint로만 노출해 current-risk를 줄이되, `status_label` 4-literal set, legend, summary-bar chip, CSS, server summary copy는 그대로 두는 것이 목표였습니다.

## 핵심 변경
- `app/serializers.py::_serialize_claim_coverage`는 기존 key 순서를 그대로 둔 채 마지막에 `"trust_tier": str(item.get("trust_tier") or "").strip(),`만 추가했습니다. `support_plurality` 다음에 붙었고, 그 앞의 모든 key 이름/순서/표현식은 유지했습니다.
- `app/static/app.js::buildFocusSlotExplanation`의 focus `"교차 확인"` branch와 `renderClaimCoverage`의 non-focus `"교차 확인"` branch는 이제 `item.trust_tier === "mixed"`일 때만 별도 subtle hint를 출력합니다. 색상, chip, badge, legend 변경은 없고 text-only입니다.
- `trust_tier === "trusted"`와 `trust_tier === ""`는 의도적으로 새 힌트를 만들지 않았습니다. 이 둘은 기존 `교차 확인` status label만으로 충분하다고 보고, 이번 라운드는 `"mixed"`만 새 hint 대상으로 남겼습니다.
- Gemini advice의 `"Trusted/Standard/Low"` 표현은 실제 shipped derivation과 맞지 않아 `{trusted, mixed, ""}` 2-value + empty set으로 좁혔고, 새 힌트 대상도 `"mixed"` 하나로만 제한했습니다.
- `tests/test_smoke.py`에는 `test_serialize_claim_coverage_passes_through_trust_tier_for_strong_items`를 추가했습니다. 기존 `_serialize_claim_coverage` 전용 cluster는 `tests/test_smoke.py`에 없어서, seq 438의 `test_build_entity_claim_coverage_items_emits_trust_tier_and_support_plurality_internal_fields` 바로 다음에 배치했습니다.
- `e2e/tests/web-smoke.spec.mjs`에는 `claim_coverage_strong_mixed_trust_tier_non_focus_slot_emits_mixed_trust_hint`를 추가했고, seq 441의 `claim_coverage_multi_source_weak_focus_slot_emits_multi_source_hint` 바로 다음 같은 `claim_coverage` cluster 안에 배치했습니다.
- seq 408/411/414/417/420/423/427/430/438/441 shipped surface는 의도적으로 수정하지 않았습니다. `_build_claim_coverage_progress_summary` server summary copy, legend text, summary-bar chips, CSS, `"trusted"` client branch도 이번 라운드에서 건드리지 않았습니다.

## 검증
- `rg -n "trust_tier" core/ app/ tests/ e2e/ docs/`
  - 결과: `core/agent_loop.py`의 seq 438 derivation/default hit, 기존 internal regression(`tests/test_smoke.py`), 새 serializer key(`app/serializers.py`), 새 focus/non-focus client branch(`app/static/app.js`), 새 serializer regression(`tests/test_smoke.py`), 새 Playwright fixture(`e2e/tests/web-smoke.spec.mjs`)만 hit했습니다. `docs/` hit는 없었습니다.
- `rg -n "교차 확인 기준은 충족하지만 공식/위키/데이터 소스가 약합니다" core/ app/ tests/ e2e/`
  - 결과: `app/static/app.js` non-focus branch 1건, `e2e/tests/web-smoke.spec.mjs` assertion 1건만 hit했습니다.
  - focus branch는 handoff site B가 별도 문구 `"재조사 대상이며 현재 교차 확인 상태이지만, 공식/위키/데이터 소스가 약합니다."`를 고정해 exact phrase grep에는 포함되지 않았습니다.
- `rg -n "SourceRole\.(OFFICIAL|DATABASE|WIKI)" app/`
  - 결과: hit 없음. trusted-role set은 client가 재계산하지 않고 server serializer의 `trust_tier` 문자열만 읽습니다.
- `rg -n "color|badge|chip" app/static/app.js | wc -l`
  - 결과: `50`
  - pre-edit baseline도 `50`이었고, 이번 라운드에서 color/chip/badge element를 추가하지 않았습니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 24 tests in 0.061s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 8 tests in 0.017s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.074s`, `OK`
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.064s`, `OK`
- `python3 -m py_compile app/serializers.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `node --check app/static/app.js`
  - 결과: 출력 없음, 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim_coverage_strong_mixed_trust_tier_non_focus_slot_emits_mixed_trust_hint" --reporter=line`
  - 결과: `1 passed (4.6s)`
- `git diff --check -- app/serializers.py app/static/app.js tests/test_smoke.py e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, 통과
- `make e2e-test`와 전체 `tests.test_web_app`는 shared browser helper를 건드리지 않았고 ready/release 판정 라운드도 아니라서 실행하지 않았습니다.

## 남은 리스크
- server-side summary에는 아직 `trust_tier === "mixed"` 힌트가 없습니다. 이번 라운드는 per-slot client line에만 노출하고 있고, `_build_claim_coverage_progress_summary`까지 넓히면 legend symmetry를 다시 건드리게 되어 별도 arbitration이 맞습니다.
- G2-followup(non-focus multi-source WEAK summary fallback symmetry)은 여전히 남아 있습니다. G5/G6/G7/G8도 이번 라운드에서는 다루지 않았습니다.
- unrelated full `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 계속 0이고, 이번 라운드로 docs-only follow-up이 새로 트리거되지는 않았습니다.
- dirty worktree의 다른 파일들은 이번 라운드에서 건드리지 않았습니다.
