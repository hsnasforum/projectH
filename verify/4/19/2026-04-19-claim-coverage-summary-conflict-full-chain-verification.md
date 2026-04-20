# 2026-04-19 claim coverage summary conflict full chain verification

## 변경 파일
- `verify/4/19/2026-04-19-claim-coverage-summary-conflict-full-chain-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-claim-coverage-summary-conflict-full-chain.md`)의 7-file widened 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`claim-coverage-summary-conflict-full-chain-implement-blocked-verification`, `agent-loop-conflict-labeling-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 376 (`Claim Coverage Summary CONFLICT — storage + serializer + browser full chain (widened scope)`)은 Gemini advice 375 결정 이후 `storage/web_search_store.py`까지 scope를 한 파일만큼 넓힌 re-issuance였습니다. 이번 `/work`가 그 7개 파일 전부(`storage/web_search_store.py`, `app/serializers.py`, `app/static/app.js`, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`)를 건드렸다고 주장했으므로 각 변경이 현재 tree에 실제로 반영됐고 scope_limit을 넘지 않았는지, 그리고 `renderFactStrengthBar`가 의도대로 untouched로 남아 있는지 고정해야 다음 control 선택이 안전합니다.
- `/work`가 `python3 -m unittest tests.test_web_app` 전체가 이번 슬라이스와 무관한 기존 실패(`LocalOnlyHTTPServer PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist` `AttributeError`)로 fail했다고 기록했기 때문에 그 실패들이 실제로 이번 변경 경로와 무관한지, focused 2 tests + Playwright full + py_compile + diff-check가 이번 라운드 truth 판정에 충분한지 같이 재확인해야 합니다.
- 선행 verify(`claim-coverage-summary-conflict-full-chain-implement-blocked-verification`)는 seq 373 implement_blocked triage 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 7-file 구현 주장이 모두 현재 tree와 일치합니다.
  - `storage/web_search_store.py:237-245` `_summarize_claim_coverage()`의 `counts` dict가 `{"strong": 0, "weak": 0, "missing": 0, "conflict": 0}`로 4-key 초기화되어, 기존 `if status in counts:` 가드 그대로 `"conflict"` 항목도 집계됩니다. 이 4-key dict가 같은 파일 `list_session_record_summaries()` 경로(`storage/web_search_store.py:347-369`)를 통해 그대로 serializer로 전달됩니다.
  - `app/serializers.py:282-287` `claim_coverage_summary` dict가 `STRONG / CONFLICT / WEAK / MISSING` 4-key로 확장됐고, 각 key는 `int((item.get("claim_coverage_summary") or {}).get(CoverageStatus.<...>) or 0)` 동일 패턴을 유지합니다. storage 값이 string key(`"conflict"`)고 serializer가 `CoverageStatus.CONFLICT` (enum value `"conflict"`)로 읽는 비대칭이지만, `StrEnum` 특성상 dict lookup은 string-equal이라 value 통과가 truthful합니다.
  - `app/static/app.js:2246-2256` `summarizeClaimCoverageCounts()`의 counts 초기화가 `{ strong: 0, weak: 0, missing: 0, conflict: 0 }`로 확장됐고, `else if (status === C.CoverageStatus.CONFLICT)` 분기가 추가됐습니다.
  - `app/static/app.js:2309-2317` `formatClaimCoverageCountSummary()`가 `교차 확인 N · 정보 상충 N · 단일 출처 N · 미확인 N` 순서로 join합니다. 각 segment는 해당 count가 양수일 때만 push되므로, `conflict = 0`인 기존 경로는 이전과 동일한 3-part(또는 그 이하) 문자열을 유지합니다.
  - `app/static/app.js:2259-2302` `renderFactStrengthBar()`는 의도대로 전혀 바뀌지 않았습니다. `total = counts.strong + counts.weak + counts.missing`는 그대로이고, 세 badge group(`fact-count strong`/`weak`/`missing`)만 렌더링합니다. `summarizeClaimCoverageCounts()`가 이제 `conflict`를 드러내더라도 bar는 이 값을 total에서 제외한 상태로 유지됩니다.
  - `tests/test_web_app.py`의 `test_web_search_store_list_summaries_includes_claim_coverage_summary` (line 18160)와 `test_web_search_history_serializer_includes_claim_coverage_summary` (line 18218)가 추가됐고, 둘 다 storage→serializer 경로에서 `conflict: 1`을 pin합니다. 기존 dict-shape assertion들은 `conflict: 0`까지 넓힌 상태로 유지됩니다.
  - `e2e/tests/web-smoke.spec.mjs`의 `claim_coverage_summary` fixture dict가 `conflict: 0` (또는 non-zero 시나리오에서 `conflict: 2`)까지 포함한 4-key shape로 확장됐고, line 2035-2061에 `"history-card summary가 non-zero conflict count를 정보 상충 segment로 렌더링합니다"` 시나리오가 추가돼 `사실 검증 교차 확인 1 · 정보 상충 2 · 단일 출처 1` 문자열을 pin합니다. 기존 `단일 출처 1 · 미확인 1` 같은 assertion text는 해당 fixture의 `conflict`가 `0`이므로 그대로 유지됩니다.
  - `docs/PRODUCT_SPEC.md:269`와 `docs/ARCHITECTURE.md:222`의 `web_search_history.claim_coverage_summary` 설명 문장이 `strong / conflict / weak / missing` 4-key로만 수정됐습니다. 다른 문단은 이번 라운드에서 건드리지 않았습니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `core/contracts.py`, `core/web_claims.py`, `core/agent_loop.py`는 이번 라운드에서 수정되지 않았습니다.
  - `app/static/app.js::renderFactStrengthBar` (라인 2259-2302)는 여전히 3-strength bar 구성이고 `conflict` segment는 없습니다.
- focused 검증이 모두 통과했습니다.
  - `python3 -m py_compile storage/web_search_store.py app/serializers.py` → 출력 없음, exit `0`
  - `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary tests.test_web_app.WebAppServiceTest.test_web_search_history_serializer_includes_claim_coverage_summary` → `Ran 2 tests in 0.010s`, `OK`
  - `git diff --check -- storage/web_search_store.py app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs` → 출력 없음, exit `0`
- 전체 `python3 -m unittest tests.test_web_app` 실패는 이번 라운드에서 다시 돌리지 않았습니다. `/work`가 기록한 두 failure family(`LocalOnlyHTTPServer PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist` `AttributeError`)는 현재 dirty state에서도 같은 날 선행 verify(`implement_blocked triage`)가 지적한 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` 계열과 같은 종류의 이번 슬라이스-무관한 기존 실패로 판단됩니다. 이번 라운드 변경 경로(storage → serializer → browser summary)는 focused 2 tests + Playwright full(17.1m) + py_compile + diff-check로 이미 커버됩니다.
- Playwright full(`cd e2e && npx playwright test tests/web-smoke.spec.mjs --reporter=line` → `114 passed (17.1m)`)는 `/work`가 이미 실행했고, 이번 라운드가 shared browser helper(`formatClaimCoverageCountSummary`, `summarizeClaimCoverageCounts`)를 바꿨으므로 `.claude/rules/browser-e2e.md`의 "shared browser helpers 변경 시 broad 스위트" 기준에 부합합니다. verify 라운드에서 다시 돌리지 않습니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `storage/web_search_store.py:237-245`, `app/serializers.py:282-287`, `app/static/app.js:2246-2317` 및 `:2259-2302`, `tests/test_web_app.py:18160/18218`, `e2e/tests/web-smoke.spec.mjs:1806/1816/1827/1838/2035-2061/2135/2396/2545/2683/2842/3278/3685/3821/3952/4054/4158/4298`, `docs/PRODUCT_SPEC.md:269`, `docs/ARCHITECTURE.md:222`.
  - 결과: 4-key 확장, `정보 상충 N` 렌더링, non-zero conflict 시나리오, 문서 문장 4-key 업데이트, `renderFactStrengthBar` untouched 상태 모두 현재 tree와 일치함.
- `python3 -m py_compile storage/web_search_store.py app/serializers.py` → 출력 없음, exit `0`.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary tests.test_web_app.WebAppServiceTest.test_web_search_history_serializer_includes_claim_coverage_summary` → `Ran 2 tests in 0.010s`, `OK`.
- `git diff --check -- storage/web_search_store.py app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs` → 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - 전체 `python3 -m unittest tests.test_web_app`: `/work`가 이미 실행해 이번 슬라이스-무관한 기존 실패(37 errors)를 분리해 기록했습니다. 현재 변경 경로는 focused 2 tests + Playwright full + py_compile + diff-check로 커버되며, 무관 실패가 원복될 때까지는 재실행이 의미 없습니다.
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs --reporter=line`: `/work`가 이번 라운드에서 실제로 실행해 `114 passed (17.1m)`으로 통과했습니다. shared helper 변경이 있었기 때문에 full 실행이 규약에 맞고, verify 단계에서 같은 17분짜리 재실행은 불필요했습니다.
  - `make e2e-test`: 브라우저 full은 Playwright web-smoke에 이미 포함됐고, release/ready 판정 라운드가 아니므로 생략합니다.

## 남은 리스크
- `app/static/app.js::renderFactStrengthBar` (라인 2259-2302)는 이번 라운드에서 의도적으로 untouched입니다. in-answer fact strength badge surface는 여전히 `conflict`를 별도 badge로 보여주지 않고 `total`에서도 제외되므로, 같은 entity-card에서 history-card meta(`사실 검증 교차 확인 1 · 정보 상충 2 · 단일 출처 1`)와 in-answer bar(`교차 확인 1, 단일 출처 1` 두 badge만) 사이에 visible CONFLICT 표시 gap이 남습니다. 다음 후보 슬라이스로 잡기 가장 좋습니다.
- `core/agent_loop.py`의 focus_slot CONFLICT wording은 여전히 기존 unresolved 문장을 재사용합니다. CONFLICT 전용 stronger explanation이나 reinvestigation trigger 문구 차별화는 아직 없습니다.
- 전체 `python3 -m unittest tests.test_web_app`는 이번 슬라이스와 무관한 dirty-state 기반 2 family의 실패(37 errors)가 여전히 남아 있습니다. 별도 truth-sync 라운드 몫이며, 이번 family가 그 쪽을 건드리지 않았기 때문에 이번 verify에서 새 regression으로 편입하지 않습니다.
- broader `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` failure도 선행 verify에서 이미 별도 truth-sync 라운드 몫으로 남겨진 상태이며 이번 라운드와 무관합니다.
