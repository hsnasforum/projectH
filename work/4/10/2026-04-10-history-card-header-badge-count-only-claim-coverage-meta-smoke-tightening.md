# history-card header-badge count-only claim-coverage meta smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다` 시나리오에 card5(investigation, non-empty `claim_coverage_summary` + empty `claim_coverage_progress_summary`) fixture 한 건과 count-only `.meta` 어서션을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-header-badge-empty-progress-summary-smoke-negatives.md`) 와 그 `/verify` 는 empty progress-summary hidden path (card2/3/4) 를 잠갔지만, 남은 current-risk는 혼합 count-only 경로였음: `claim_coverage_summary` 만 있고 `claim_coverage_progress_summary` 가 비었을 때 history-card `.meta` 가 단일 `사실 검증 …` count 라인만 렌더링하고 stray ` · ` separator 나 progress-text leak 없이 유지되는지 기존 스모크에 고정되어 있지 않았음
- `app/static/app.js:2954-2971` 렌더러는 investigation (`entity_card`/`latest_update`) 카드에서는 answer-mode label 을 skip 하고, `claim_coverage_summary` 가 있으면 `사실 검증 <포맷 카운트>` 한 줄만 push 한 뒤 `detailLines.join(" · ")` 로 `.meta` 를 구성하므로, empty progress + non-empty summary 케이스는 `.meta` 가 정확히 한 줄, 단일 카운트 카테고리일 때 `·` artifact 없이 나타나야 함
- 기존 card1~4 fixture 만으로는 이 혼합 경로가 scenario 내부에서 관찰되지 않았음 (card1 만 non-empty progress, card2~4 는 모두 empty summary + empty progress)
- 이 슬라이스는 런타임/도큐먼트 변경 없이 동일 isolated scenario 안에서 fixture 한 건과 count-only `.meta` negative 어서션만 추가해 이미 shipped 된 renderer 경로를 잠그는 범위임

## 핵심 변경
1. **card5 fixture 추가** (`e2e/tests/web-smoke.spec.mjs`)
   - `answer_mode: "latest_update"` (investigation → answer-mode label line skip)
   - `verification_label: "공식 단일 출처"`, `source_roles: ["공식 기반"]`
   - `claim_coverage_summary: { strong: 2 }` — 단일 카테고리만 채워 `formatClaimCoverageCountSummary` 결과가 `교차 확인 2` 로 고정되고 count-line 자체에 `·` artifact 가 섞이지 않도록 함
   - `claim_coverage_progress_summary` 는 undefined — `(item.claim_coverage_progress_summary || "").trim()` 경로에서 empty 로 떨어져 detailLines 에 push 되지 않음
2. **cards count 어서션 갱신**
   - `await expect(cards).toHaveCount(4)` → `await expect(cards).toHaveCount(5)`
3. **card5 count-only `.meta` 어서션 추가**
   - `await expect(card5Meta).toHaveCount(1)` — detailMeta 가 정확히 하나 렌더링
   - `await expect(card5Meta).toHaveText("사실 검증 교차 확인 2")` — count-only line 의 정확한 문자열 잠금
   - `await expect(card5Meta).not.toContainText("·")` — 단일 카테고리/단일 detailLine 에서는 `·` separator 가 전혀 섞여서는 안 됨
   - `await expect(card5Meta).not.toContainText("출생일: 단일 출처")` — card1 progress-summary 텍스트 누출 없음
   - `await expect(card5Meta).not.toContainText("최신 확인")` — investigation 카드이므로 answer-mode label (`최신 확인`) 이 meta 에 섞이지 않아야 함
   - `expect(card5MetaText.length).toBeGreaterThan(0)` — blank meta 가 아님
   - `expect(card5MetaText.startsWith("·")).toBe(false)` 및 `endsWith("·")` 는 `false` — separator-only / leading-or-trailing separator 회귀 방지
- 재사용 원칙: 기존 scenario 내부의 `cards = historyBox.locator(".history-item")`, `.meta` 셀렉터, 기존 `renderSearchHistory` 호출 경로만 재사용했고 새 selector/helper/fixture 파일을 만들지 않았음. `formatClaimCoverageCountSummary` 의 출력 포맷(`교차 확인 N`)도 기존 런타임 코드를 그대로 사용함

## 검증
이번 라운드 실행:
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed (5.5s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 isolated scenario 한 개 안에 fixture 하나/assertions 몇 줄만 추가함
- `tests.test_web_app` 등 unit suite — 런타임/라우트/도큐먼트 미변경
- 다른 history-card family scenario — 이번 변경은 해당 isolated scenario 안에서만 동작함

## 남은 리스크
- 이번 어서션은 `formatClaimCoverageCountSummary` 가 strong-only 입력에 대해 `교차 확인 N` 문자열을 낸다는 점에 의존함. 해당 포맷(`app/static/app.js:2225-2232`) 문구가 향후 바뀌면 이 스모크가 먼저 깨짐 — 다만 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- `not.toContainText("·")` 는 count-category 가 하나뿐인 fixture(`{ strong: 2 }`) 에 특수화되어 있음. fixture 를 다중 카테고리(`strong`+`weak` 등) 로 바꾸면 count-line 자체에 `·` 가 포함되므로 이 어서션은 그대로 재사용 불가 — fixture 를 유지하는 한 안전함
- `not.toContainText("최신 확인")` 은 answer-mode label 이 investigation 카드에서 meta 에 섞이지 않음을 관찰하지만, 만약 향후 `latest_update` 라벨 문구가 `사실 검증` 과 겹치는 다른 문자열로 바뀌면 어서션을 같이 검토해야 함
- 반대 방향(`claim_coverage_summary` 비어 있고 `claim_coverage_progress_summary` non-empty) investigation 카드 혼합 경로는 이미 card1(non-empty progress) 과 card4(둘 다 비어 있음) 에서 각각 다른 축으로 잠겨 있으므로 이번 슬라이스에서는 다루지 않음
