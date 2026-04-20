# 2026-04-19 client CoverageStatus CONFLICT 노출 verification

## 변경 파일
- `verify/4/19/2026-04-19-client-coverage-status-conflict-exposure-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-client-coverage-status-conflict-exposure.md`)의 3-file 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`fact-strength-bar-conflict-segment-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 378 (`Client CoverageStatus.CONFLICT Exposure — close live-session summary gap, retire bar fallback`)은 seq 376에서 생긴 dead branch(`summarizeClaimCoverageCounts`의 `C.CoverageStatus.CONFLICT`가 `undefined`)를 없애고, seq 377이 `renderFactStrengthBar` 안에 둔 raw fallback을 제거해 contract 기반 CONFLICT 카운트가 모든 소비자에게 truthful하게 전달되도록 닫는 슬라이스였습니다.
- 이번 `/work`가 `app/static/contracts.js::CoverageStatus`에 `CONFLICT: "conflict"` 노출, `renderFactStrengthBar` fallback 제거, live-session `formatClaimCoverageSummary` 경로의 CONFLICT Playwright 시나리오 추가를 주장했으므로, 각 변경이 현재 tree에 truthful하게 반영됐고 `summarizeClaimCoverageCounts` / `formatClaimCoverageCountSummary` / `formatClaimCoverageSummary` / serializer / storage / core가 untouched로 남았는지 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`fact-strength-bar-conflict-segment-verification`)는 seq 377 bar segment round 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `app/static/contracts.js:26` `CoverageStatus`가 이제 `Object.freeze({ STRONG: "strong", CONFLICT: "conflict", WEAK: "weak", MISSING: "missing" })`로 `STRONG / CONFLICT / WEAK / MISSING` 순서로 노출됩니다. `"conflict"` string value가 Python `CoverageStatus.CONFLICT.value`와 동일하므로 payload 비교가 정상화됩니다.
  - `app/static/app.js:2246-2257` `summarizeClaimCoverageCounts`의 body는 seq 376 상태 그대로이지만, `C.CoverageStatus.CONFLICT`가 이제 정의된 덕에 `else if (status === C.CoverageStatus.CONFLICT) counts.conflict += 1;` 분기가 dead branch에서 실제 분기로 바뀝니다.
  - `app/static/app.js:2259-2265` `renderFactStrengthBar`에서 seq 377이 넣었던 `const items = …` 재-materialization과 `if (counts.conflict === 0 && items.length > 0) { counts.conflict = items.reduce(…) }` fallback이 제거됐습니다. bar는 이제 `summarizeClaimCoverageCounts()`가 돌려주는 `counts`만 사용하고, `total = counts.strong + counts.conflict + counts.weak + counts.missing`는 그대로 유지됩니다. 그 아래 네 badge group(`strong`, `conflict`, `weak`, `missing`) 렌더링도 seq 377 상태 그대로입니다.
  - `e2e/tests/web-smoke.spec.mjs:1797` `live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다` 시나리오가 추가됐습니다. seq 377이 추가한 `fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다` 시나리오는 이전 위치에 그대로 남아 있습니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `app/static/app.js`의 `summarizeClaimCoverageCounts` 함수 body, `formatClaimCoverageCountSummary`, `formatClaimCoverageSummary`는 이번 라운드에서 수정되지 않았습니다.
  - `app/serializers.py`, `storage/web_search_store.py`, `core/contracts.py`, `core/web_claims.py`, `core/agent_loop.py`는 이번 라운드에서 수정되지 않았습니다.
  - `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`는 이번 라운드에서 수정되지 않았습니다. `/work`가 "즉시 수정이 필요한 문장은 바로 보이지 않았다"고 기록한 상태를 유지합니다.
- 이번 라운드로 CONFLICT family 전 surface 일관성이 현재 tree에서 실제로 닫혔습니다.
  - contract: `core/contracts.py` CoverageStatus.CONFLICT + `app/static/contracts.js` CoverageStatus.CONFLICT
  - server aggregation: `core/web_claims.py` conflict emission + `core/agent_loop.py` label/rank/unresolved/probe 분기
  - storage: `storage/web_search_store.py::_summarize_claim_coverage` 4-key counts
  - serializer: `app/serializers.py:282-287` 4-key claim_coverage_summary
  - browser history-card summary: `formatClaimCoverageCountSummary` 4-segment join
  - browser in-answer bar: `renderFactStrengthBar` 4-badge with CSS class
  - browser live-session summary: `formatClaimCoverageSummary → summarizeClaimCoverageCounts → formatClaimCoverageCountSummary` 4-segment join (이전 dead branch가 이번에 정상화)
  - Playwright lock: history-card 시나리오(seq 376), bar 시나리오(seq 377), live-session 시나리오(seq 378)
  - 문서: `docs/PRODUCT_SPEC.md:269`, `docs/ARCHITECTURE.md:222`만 4-key sentence로 동기화됨 (seq 376)
- focused rerun은 `/work`가 이미 수행했습니다.
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다" --reporter=line` → `1 passed (5.3s)` (fallback 제거 후에도 통과)
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다" --reporter=line` → `1 passed (4.5s)`
  - `git diff --check -- app/static/contracts.js app/static/app.js e2e/tests/web-smoke.spec.mjs` → 출력 없음, 통과
- 이번 verify에서 추가로 확인한 검증
  - `git diff --check -- app/static/contracts.js app/static/app.js e2e/tests/web-smoke.spec.mjs` → 출력 없음, exit `0` (독립적으로 재실행).
  - Playwright full 재실행은 이번 라운드가 shared helper의 body를 바꾸지 않았고, dead branch가 live branch가 된 것과 local fallback 한 줄 삭제가 유일한 의미 있는 변화이므로 규약상 생략합니다.

## 검증
- 직접 코드 대조
  - 대상: `app/static/contracts.js:26`, `app/static/app.js:2246-2265`, `e2e/tests/web-smoke.spec.mjs:1797`, `app/static/app.js:2321-2324` (`formatClaimCoverageSummary`), `app/static/app.js:1081` 및 `:2464` (live-session `formatClaimCoverageSummary` 사용처).
  - 결과: `/work`가 설명한 3개 파일 변경이 현재 tree와 일치하고, fallback 제거 뒤에도 `renderFactStrengthBar`가 `summarizeClaimCoverageCounts` 결과만으로 CONFLICT badge를 내는 경로가 truthful하며, live-session surface의 CONFLICT summary가 실제로 렌더링 경로를 열어 두었음을 확인했습니다.
- `git diff --check -- app/static/contracts.js app/static/app.js e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright full 스위트: 이번 라운드가 shared helper(`summarizeClaimCoverageCounts`/`formatClaimCoverageCountSummary`/`formatClaimCoverageSummary`)의 body를 바꾸지 않았고 dead branch resolution + local fallback 제거 + 신규 isolated scenario 1개만 변화이므로, `/work`가 돌린 두 isolated scenario 통과로 narrowest 규약이 충족됩니다. `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준에 맞습니다.
  - 전체 `python3 -m unittest tests.test_web_app`: seq 376/seq 377 verify에서 이미 이번 family와 무관한 기존 실패(37 errors) 분리 기록이 있고, 이번 라운드는 Python 경로를 전혀 건드리지 않았습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- CONFLICT same-family current-risk는 이번 라운드로 관찰 가능한 모든 browser surface에서 사실상 닫혔습니다. 다음 슬라이스 후보는 current-risk가 아니라 polish / 새 axis 쪽으로 이동합니다.
  - (polish-1) `core/agent_loop.py`의 focus_slot CONFLICT wording은 이미 `"재조사했지만 … 아직 정보 상충 상태입니다."`처럼 label lookup으로 CONFLICT를 포함합니다. CONFLICT 전용 설명 강화(예: "두 출처가 서로 어긋난 상태로 남아 있습니다") 같은 폴리싱은 가능하지만, wording design choice라 bounded slice로 좁히는 데 여전히 low-confidence가 남습니다.
  - (polish-2) reinvestigation trigger threshold / probe retry count 등을 CONFLICT 전용으로 미세 조정하는 방향은 동작 변화와 회귀 위험이 있어 사전에 명시된 합의가 필요합니다.
  - (docs) `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/ACCEPTANCE_CRITERIA.md`는 이번 family 라운드 동안 건드리지 않았습니다. CONFLICT family shipped 상태를 반영하는 즉시 수정 필요 문장이 있는지 audit 없이 수정은 risky이며, 같은 날 docs-only 반복 guard에는 아직 해당하지 않지만 다음 라운드가 docs-only 여러 파일 번들이 되면 guard 경로에 근접합니다.
  - (new axis) `source role labeling/weighting`, `official/news/wiki/community weighting`, `strong vs weak vs unresolved separation`(CONFLICT 이후 잔여 축) 중 하나는 새 axis로 Milestone 4를 이어 받을 수 있습니다. 어느 쪽이 가장 truthful bounded slice인지는 별도 판단이 필요합니다.
- 같은 날 same-family docs-only guard는 아직 적용 대상이 아닙니다(라운드 전체가 implementation 위주). 다만 다음 라운드를 docs로 고를 경우 bounded bundle로 잡아야 docs-only 반복이 3회 미만에서 끝납니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family(`LocalOnlyHTTPServer PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist`)는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
- broader `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` failure도 선행 verify에서 이미 별도 truth-sync 라운드 몫으로 남겨진 상태이며 이번 라운드와 무관합니다.
