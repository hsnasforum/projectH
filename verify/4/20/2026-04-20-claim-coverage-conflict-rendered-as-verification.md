# 2026-04-20 claim coverage conflict rendered_as verification

## 변경 파일
- `verify/4/20/2026-04-20-claim-coverage-conflict-rendered-as-verification.md`

## 사용 skill
- `round-handoff`: seq 414 `/work`(`work/4/20/2026-04-20-claim-coverage-conflict-rendered-as.md`)를 직접 code/docs/tests 상태와 대조하고, handoff가 요구한 narrowest 검증을 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 414 `.pipeline/claude_handoff.md` (advice 413 Option A 기반)가 구현되어 `/work` 노트가 새로 제출되었습니다. seq 411 CONFLICT chain 뒤에 남아 있던 panel-side `claim_coverage` 표면을 `rendered_as = "conflict"` + `status_label = "정보 상충"` 로 열고, `app/static/app.js::formatClaimRenderedAs`, `docs/ARCHITECTURE.md:220`, `docs/PRODUCT_SPEC.md:267`, `tests/test_smoke.py` 회귀까지 한 라운드에 묶었다고 주장합니다. 본 verify는 그 주장을 실제 파일과 테스트로 교차 확인합니다.

## 핵심 변경
- `core/agent_loop.py`
  - `_build_entity_claim_coverage_items`(`:4222-4276`)는 이제 `primary_claims` → `conflict_claims` → `weak_claims` 순의 keyword-only signature 이고, `conflict_slots = {claim.slot for claim in conflict_claims}` 이 추가되었습니다.
  - `primary_claim is None` branch(`:4238-4251`)의 `status_label`은 `self._claim_coverage_status_label(CoverageStatus.MISSING)`로 canonicalized, `rendered_as`는 `"not_rendered"` 유지.
  - 본문 populated branch(`:4253-4274`)에서 `rendered_as` 결정이 `strong → conflict → weak → not_rendered` 순으로 강제되고, `status_label`은 `self._claim_coverage_status_label(status)`를 통해 `CoverageStatus` 기반으로 결정됩니다. 기존 하드코딩된 `"교차 확인"` / `"단일 출처"` / `"미확인"` literal은 본 함수 본문에서 제거되었습니다.
  - 두 callsite(`:6246`, `:6521`)가 `primary_claims, conflict_claims, weak_claims, _, _ = self._select_entity_fact_card_claims(...)`로 unpack을 교체했고, 직후의 `_build_entity_claim_coverage_items` 호출에 `conflict_claims=conflict_claims`가 새로 전달됩니다.
- `app/static/app.js`
  - `formatClaimRenderedAs`(`:2406-2413`)에 `if (normalized === "conflict") return "상충 정보 반영";` 분기가 `uncertain` 과 `not_rendered` 사이에 정확히 한 줄 추가되었습니다. 다른 분기는 그대로입니다.
- `docs/ARCHITECTURE.md:220` 과 `docs/PRODUCT_SPEC.md:267` 의 `rendered_as` 괄호 열거가 `fact_card / conflict / uncertain / not_rendered` 4-literal로 확장되었습니다. 문장의 다른 부분은 수정되지 않았고, `docs/ACCEPTANCE_CRITERIA.md:48` 의 `rendered_as = "uncertain"` 단일-literal 설명은 weak/missing subset 정의이므로 drift 대상이 아님을 확인했습니다.
- `tests/test_smoke.py`
  - `test_coverage_entity_card_claim_coverage_payload_marks_conflict_slot_with_conflict_rendered_as`(`:1206-1281`)가 seq 408/411 CONFLICT 회귀 바로 아래에 추가되었습니다. STRONG(`개발`, `교차 확인`, `fact_card`), CONFLICT(`장르/성격`, `정보 상충`, `conflict`), WEAK(`이용 형태`, `단일 출처`, `uncertain`), MISSING(`상태`, `미확인`, `not_rendered`)까지 4개 분기를 모두 고정합니다.
- handoff가 금지한 surface들(seq 408 5-tuple + response-body header, seq 411 source-line/role_priority sync, `core/contracts.py`, `core/web_claims.py`, `storage/web_search_store.py`, `app/serializers.py`, `app/static/contracts.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, 다른 docs 파일)은 이번 라운드에서 수정되지 않았습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 19 tests in 0.064s`, `OK`. 기대대로 기존 18 + 새 regression 1.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.001s`, `OK`. 기존 5개 유지.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/agent_loop.py app/static/app.js tests/test_smoke.py docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md`
  - 결과: 출력 없음, 통과.
- `grep -n 'rendered_as' docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: ARCHITECTURE.md:220 과 PRODUCT_SPEC.md:267 만 4-literal enumeration 으로 갱신되었고, ACCEPTANCE_CRITERIA.md:48 은 weak/missing subset 설명이라 drift 아님.
- Playwright, `python3 -m unittest tests.test_web_app`, `make e2e-test`는 실행하지 않았습니다. 이번 slice는 server-emitted payload 데이터 + 브라우저 formatter 1줄 + docs 2줄만 바꿨고, 공유 브라우저 helper / fixture / contract는 수정하지 않았습니다.

## 남은 리스크
- Milestone 4의 남은 후보는 여전히 별도 라운드 몫입니다:
  - B) seq 408 `상충하는 정보 [정보 상충]:` response-body header + seq 411 conflict `근거 출처:` + 이번 라운드 panel `rendered_as = "conflict"` 을 end-to-end 확인하는 optional Playwright scenario(`e2e/tests/web-smoke.spec.mjs`).
  - C) Source Role Weighting — COMMUNITY/PORTAL/BLOG tiering 한 번의 정확한 numeric permutation (현재 0/0/0 고정, `_ROLE_PRIORITY` + `core/agent_loop.py` 두 mirror map 동시 갱신 필요).
  - D) Reinvestigation threshold / probe retry — `max_queries_for_slot` 상한, probe list 크기, `prefer_probe_first` 문턱 등 단일 상수 한 번.
  - E) Strong vs Weak vs Unresolved Separation further polish — STRONG-tied-with-STRONG tie-break, entity-card strong-badge downgrade edge, 비-CONFLICT 전이 wording.
- `"conflict"` rendered_as 를 소비하는 브라우저 경로는 현재 `formatClaimRenderedAs` + `:2480` 한 곳만 확인되었고, 다른 renderer 가 silent skip 하는지는 별도 audit 후보입니다.
- unrelated `python3 -m unittest tests.test_web_app` 전체 실패 family 및 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` 쪽 dirty-state 실패는 이번 slice 밖이며 별도 truth-sync 라운드 몫입니다.
- 오늘(2026-04-20) docs-only round count 는 여전히 0 입니다. 이번 slice 는 code+docs mixed 이므로 docs-only guard(3-round) 에 영향을 주지 않습니다.
- 다음 control 은 B/C/D/E 중 어느 후보도 code+surface+numeric 경계가 단독으로 pinned 되어 있지 않으므로 slice_ambiguity 성격입니다. operator-only decision, approval blocker, 안전 정지, Gemini 부재 중 어느 조건에도 해당하지 않아 `.pipeline/gemini_request.md` (seq 415) 로 arbitration 을 먼저 여는 편이 rule 에 맞습니다.
