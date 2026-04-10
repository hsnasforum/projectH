# history-card header-badge combined claim-coverage count-plus-progress meta smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다` 시나리오에 card6(investigation, non-empty 다중 카테고리 `claim_coverage_summary` + non-empty `claim_coverage_progress_summary`) fixture 한 건과 count-plus-progress `.meta` 합성 순서 어서션을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-header-badge-count-only-claim-coverage-meta-smoke-tightening.md`) 와 그 `/verify` 는 count-only 경로(card5: non-empty `claim_coverage_summary` + empty `claim_coverage_progress_summary`) 를 잠갔지만, 기존 스모크에는 두 필드가 모두 채워진 혼합 경로가 관찰되지 않았음
- `app/static/app.js:2958-2964` 의 렌더러는 investigation (`entity_card`/`latest_update`) 카드에서 answer-mode label 을 skip 한 뒤 `claim_coverage_summary` 가 있으면 `사실 검증 <포맷 카운트>` 한 줄을 먼저 push 하고, 이어서 `claim_coverage_progress_summary` 를 두 번째 detail line 으로 push 한 다음 `app/static/app.js:2969` 의 `detailLines.join(" · ")` 로 `.meta` 를 구성함 — 따라서 두 필드가 동시에 non-empty 일 때는 count 라인이 먼저, progress 라인이 뒤에 오는 고정된 합성 순서가 있어야 함
- 다중 카테고리 `claim_coverage_summary` (`{ strong: 2, weak: 1 }`) 를 선택하면 `formatClaimCoverageCountSummary` (`app/static/app.js:2225-2232`) 가 `교차 확인 2 · 단일 출처 1` 을 내기 때문에, count 라인 자체가 합법적으로 ` · ` 를 포함하게 되고 스모크는 "join 결과에서 count 라인이 progress 라인보다 앞에 온다" 는 순서까지 함께 잠글 수 있음
- 이 슬라이스는 런타임/도큐먼트 변경 없이 동일 isolated scenario 안에서 fixture 한 건과 합성 순서 어서션만 추가해 이미 shipped 된 renderer 경로의 마지막 미잠금 합성 경로를 고정하는 범위임

## 핵심 변경
1. **card6 fixture 추가** (`e2e/tests/web-smoke.spec.mjs`)
   - `answer_mode: "entity_card"` (investigation → answer-mode label line skip)
   - `verification_label: "공식+기사 교차 확인"`, `source_roles: ["공식 기반"]`
   - `claim_coverage_summary: { strong: 2, weak: 1 }` — 다중 카테고리로 채워 `formatClaimCoverageCountSummary` 결과가 `교차 확인 2 · 단일 출처 1` 이 되도록 하고, count 라인 자체에 ` · ` 가 합법적으로 포함되게 함
   - `claim_coverage_progress_summary: "혼합 지표: 교차 확인과 단일 출처가 함께 관찰되었습니다."` — non-empty 로 두 번째 detailLine 이 push 되게 함
2. **cards count 어서션 갱신**
   - `await expect(cards).toHaveCount(5)` → `await expect(cards).toHaveCount(6)`
3. **card6 count-plus-progress `.meta` 어서션 추가**
   - `await expect(card6Meta).toHaveCount(1)` — detailMeta 가 정확히 하나 렌더링
   - `await expect(card6Meta).toHaveText("사실 검증 교차 확인 2 · 단일 출처 1 · 혼합 지표: 교차 확인과 단일 출처가 함께 관찰되었습니다.")` — count 라인 + progress 라인 합성 결과를 정확한 문자열로 잠금
   - `await expect(card6Meta).not.toContainText("출생일: 단일 출처")` — card1 progress-summary 텍스트 누출 없음
   - `await expect(card6Meta).not.toContainText("설명 카드")` / `not.toContainText("최신 확인")` — investigation 카드이므로 answer-mode label 이 meta 에 섞이지 않아야 함
   - `expect(card6MetaText.length).toBeGreaterThan(0)` — blank meta 가 아님
   - `expect(card6MetaText.startsWith("·")).toBe(false)` 및 `endsWith("·")` 는 `false` — leading/trailing separator artifact 없음
   - `expect(card6MetaText.indexOf("사실 검증 교차 확인 2 · 단일 출처 1")).toBeLessThan(card6MetaText.indexOf("혼합 지표:"))` — count 라인이 progress 라인보다 **앞** 에 오는 합성 순서를 명시적으로 잠금
- 재사용 원칙: 기존 scenario 내부의 `cards = historyBox.locator(".history-item")`, `.meta` 셀렉터, 기존 `renderSearchHistory` 호출 경로만 재사용했고 새 selector/helper/fixture 파일을 만들지 않았음. `formatClaimCoverageCountSummary` 의 출력 포맷(`교차 확인 N` · `단일 출처 N`) 과 `detailLines.join(" · ")` 합성 경로도 기존 런타임 코드를 그대로 사용함

## 검증
이번 라운드 실행:
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed (5.4s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 isolated scenario 한 개 안에 fixture 하나/assertions 몇 줄만 추가함
- `tests.test_web_app` 등 unit suite — 런타임/라우트/도큐먼트 미변경
- 다른 history-card family scenario — 이번 변경은 해당 isolated scenario 안에서만 동작함

## 남은 리스크
- `toHaveText` 는 `formatClaimCoverageCountSummary` 가 `{ strong, weak }` 입력에 대해 정확히 `교차 확인 2 · 단일 출처 1` 문자열을 낸다는 점과 `detailLines.join(" · ")` 의 구분자(` · `) 에 의존함. 해당 포맷(`app/static/app.js:2225-2232`) 이나 join separator 가 바뀌면 이 스모크가 먼저 깨짐 — 다만 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- `card6MetaText.indexOf("사실 검증 교차 확인 2 · 단일 출처 1") < indexOf("혼합 지표:")` 순서 어서션은 count 라인 문자열과 progress 라인 문자열이 동시에 등장한다는 가정에 의존함. 두 문자열 중 하나가 렌더링되지 않으면 `indexOf` 가 `-1` 로 떨어져 어서션은 여전히 실패 방향으로 작동하지만, 실패 메시지는 "순서 오류" 보다는 "누락" 을 가리키게 됨 — 합성 경로 회귀 감지 자체는 유지됨
- card3 `.meta` 의 `not.toContainText("·")` 어서션은 general 카드 single-line 경로에만 특수화되어 있음. 이번 라운드는 해당 어서션을 건드리지 않음
- 반대 방향(`claim_coverage_summary` 단일 카테고리 + non-empty progress) 또는 answer-mode label 이 섞인 non-investigation + both-filled 경로는 이번 슬라이스 범위 밖이며, 런타임 경로상 관찰되지 않음
