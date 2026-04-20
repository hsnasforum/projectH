# 2026-04-19 fact strength bar conflict segment verification

## 변경 파일
- `verify/4/19/2026-04-19-fact-strength-bar-conflict-segment-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-fact-strength-bar-conflict-segment.md`)의 `renderFactStrengthBar` + CSS + Playwright 시나리오 주장을 현재 tree와 대조하고, 같은 날 선행 verify들(`claim-coverage-summary-conflict-full-chain-verification`, `claim-coverage-summary-conflict-full-chain-implement-blocked-verification`, `agent-loop-conflict-labeling-verification`)을 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 377 (`Fact Strength Bar CONFLICT Segment — in-answer badge parity`)은 history-card summary와 in-answer fact-strength bar 사이의 CONFLICT 표시 gap을 닫는 슬라이스였습니다.
- 이번 `/work`가 3개 파일(`app/static/app.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`)에 대해 bar 4-badge 확장, `.fact-count.conflict` CSS 한 줄, `fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다` Playwright 시나리오 추가를 주장했으므로, 각 변경이 현재 tree에 truthful하게 반영됐고 `summarizeClaimCoverageCounts` / `formatClaimCoverageCountSummary` 등 seq 376에서 닫힌 helper와 serializer/storage가 untouched로 남았는지 고정해야 합니다.
- 또한 `/work`가 `남은 리스크`에 적은 `app/static/contracts.js`의 `CoverageStatus.CONFLICT` 미노출 문제가 단순 메모 수준인지, 아니면 다른 browser surface에서 실제 visible gap을 만드는지 이번 verify에서 같이 확인해야 다음 슬라이스 우선순위를 바로 맞출 수 있습니다.
- 선행 verify(`claim-coverage-summary-conflict-full-chain-verification`)는 storage+serializer+browser full chain round 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `app/static/app.js:2259-2319` `renderFactStrengthBar()`가 이제 `교차 확인 · 정보 상충 · 단일 출처 · 미확인` 순서로 네 개의 badge group을 렌더링합니다. 새 `if (counts.conflict > 0) { ... fact-count conflict ... " 정보 상충" }` 블록이 기존 `counts.strong > 0`과 `counts.weak > 0` 사이에 들어갔고, 기존 세 블록(라인 2278-2287 `strong`, 2298-2307 `weak`, 2308-2317 `missing`)은 구조가 그대로입니다.
  - `app/static/app.js:2268` `total` 계산이 `counts.strong + counts.conflict + counts.weak + counts.missing`로 바뀌어, CONFLICT slot만 있는 응답에서도 bar가 자동으로 숨지 않도록 고정됩니다.
  - `app/static/app.js:2261-2267`에는 `/work`가 명시한 raw `"conflict"` status fallback이 실제로 들어가 있습니다. `counts.conflict === 0 && items.length > 0`일 때 items.reduce로 raw `status === "conflict"` 개수를 재계산해 `counts.conflict`에 채워 넣습니다.
  - `app/static/style.css:602-605`에 `.fact-strength-bar .fact-count.conflict { background: rgba(234, 88, 12, 0.10); color: #c2410c; }` 규칙 하나만 추가됐습니다. 기존 `.strong` / `.weak` / `.missing` 세 규칙(라인 598-601, 606-613)은 값도 순서도 그대로입니다.
  - `e2e/tests/web-smoke.spec.mjs:1758` `fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다` 시나리오가 추가됐습니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `app/static/app.js::summarizeClaimCoverageCounts` (라인 2246-2257)와 `formatClaimCoverageCountSummary` (라인 2309-2317), `formatClaimCoverageSummary` (라인 2321-2324)는 seq 376 상태 그대로입니다.
  - `app/serializers.py`, `storage/web_search_store.py`, `core/agent_loop.py`, `core/contracts.py`, `core/web_claims.py`는 이번 라운드에서 수정되지 않았습니다.
- 다만 `/work`가 `남은 리스크`에 적은 `app/static/contracts.js` 누락은 단순 미래 후보가 아니라 current-risk입니다.
  - `app/static/contracts.js:26`에는 여전히 `CoverageStatus: Object.freeze({ STRONG: "strong", WEAK: "weak", MISSING: "missing" })`만 정의돼 있습니다. `CONFLICT`가 없습니다.
  - `app/static/app.js:2252` `summarizeClaimCoverageCounts()`의 `else if (status === C.CoverageStatus.CONFLICT) counts.conflict += 1;`는 `C.CoverageStatus.CONFLICT`가 `undefined`이므로 어떤 `status`에도 매칭되지 않습니다. 즉 client-aggregated CONFLICT 카운트는 항상 0입니다.
  - `app/static/app.js:1081` `formatClaimCoverageSummary(message.claim_coverage)`와 `app/static/app.js:2464` `formatClaimCoverageSummary(items)`는 바로 `summarizeClaimCoverageCounts` 결과를 `formatClaimCoverageCountSummary`에 넘기기 때문에, 라이브 세션 응답 surface의 `사실 검증 …` 요약 문자열은 실제 `claim_coverage` payload에 `status: "conflict"` 슬롯이 있어도 `정보 상충 N` 세그먼트를 내지 못합니다.
  - 오직 `renderFactStrengthBar`만 이번 라운드에서 `counts.conflict === 0 && items.length > 0` fallback을 덧붙여서 bar 표면에서만 이 gap을 회피했습니다.
  - 즉 in-answer bar / live-session summary / history-card summary 세 surface 중 한 곳(bar)만 CONFLICT를 보여 주고, live-session summary는 여전히 조용히 누락합니다. user-visible inconsistency는 seq 377 전보다 줄었지만 아직 완전히 닫히지 않았습니다.
- 같은 날 same-family docs-only guard 적용 대상 아닙니다. seq 366/369/373(blocked)/376/377 모두 implement round입니다.
- focused rerun은 `/work`가 이미 수행했습니다.
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다" --reporter=line` → `1 passed (5.7s)` (2회 선행 실패 후 수정한 최종 결과)
  - `git diff --check -- app/static/app.js app/static/style.css e2e/tests/web-smoke.spec.mjs` → 출력 없음, 통과
- 이번 verify에서 추가로 확인한 검증
  - `git diff --check -- app/static/app.js app/static/style.css e2e/tests/web-smoke.spec.mjs` → 출력 없음, exit `0` (독립적으로 재실행)
  - Playwright full 재실행은 이번 라운드가 shared helper(`summarizeClaimCoverageCounts`/`formatClaimCoverageCountSummary`)를 건드리지 않고 `renderFactStrengthBar`라는 단일 렌더러에만 영향을 준 isolated UI change이므로 규약상 생략합니다.

## 검증
- 직접 코드 대조
  - 대상: `app/static/app.js:2246-2319`, `app/static/style.css:592-613`, `e2e/tests/web-smoke.spec.mjs:1758`, `app/static/contracts.js:26`, 그리고 `app/static/app.js:1081`, `:2464` (live-session `formatClaimCoverageSummary` 사용처).
  - 결과: `/work`가 설명한 3개 파일 변경이 현재 tree와 일치하고, seq 376에서 닫힌 helper/serializer/storage는 그대로이며, `app/static/contracts.js::CoverageStatus`에 `CONFLICT`가 없어 live-session `formatClaimCoverageSummary` path가 여전히 CONFLICT 누락 상태임을 확인했습니다.
- `git diff --check -- app/static/app.js app/static/style.css e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright full 스위트: 이번 라운드가 단일 렌더러 + 한 개 CSS class + 한 개 시나리오 변경이라 shared helper를 건드리지 않았고, `/work`가 이미 isolated scenario rerun(`1 passed`)으로 새 시나리오를 확인했습니다. `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준에 맞습니다.
  - isolated Playwright rerun 자체 재실행: `/work`가 같은 명령으로 최종 `1 passed`를 확인했고 git diff check가 비어 있어, verify 단계에서 같은 scenario를 다시 돌릴 추가 근거가 없습니다.
  - 전체 `python3 -m unittest tests.test_web_app`: seq 376 verify에서 이미 이번 family와 무관한 기존 실패(37 errors, `LocalOnlyHTTPServer PermissionError` / `SQLiteSessionStore._compact_summary_hint_for_persist`) 분리 기록이 있고, 이번 라운드는 Python 경로를 전혀 건드리지 않았습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- `app/static/contracts.js::CoverageStatus`가 여전히 3-key(`STRONG/WEAK/MISSING`)라 `summarizeClaimCoverageCounts`의 `else if (status === C.CoverageStatus.CONFLICT)` 분기가 실질적으로 dead branch입니다. `renderFactStrengthBar`는 이번 라운드의 raw `"conflict"` fallback 덕에 동작하지만, `formatClaimCoverageSummary` 기반 live-session summary(`app/static/app.js:1081`, `:2464`)는 여전히 CONFLICT 슬롯이 있어도 `정보 상충 N` segment를 드러내지 못합니다. 이것이 현재 MVP surface에서 가장 높은 우선순위의 CONFLICT same-family current-risk이며, 다음 슬라이스 후보 1순위입니다.
- `renderFactStrengthBar` 안의 raw `"conflict"` fallback(라인 2261-2267)은 contracts.js 갭을 우회하기 위한 로컬 패치입니다. contracts.js가 정상화되면 이 fallback은 redundant가 되므로 같은 라운드에서 같이 정리하는 편이 coherent합니다.
- `core/agent_loop.py`의 CONFLICT-specific focus_slot wording은 이번 라운드에서도 그대로이며 별도 future round 후보입니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family(`LocalOnlyHTTPServer PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist`)는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
- broader `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` failure도 선행 verify에서 이미 별도 truth-sync 라운드 몫으로 남겨진 상태이며 이번 라운드와 무관합니다.
