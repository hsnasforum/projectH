# history-card header-badge empty progress-summary smoke negatives

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다` 시나리오에 card2/card3/card4에 대한 empty `claim_coverage_progress_summary` negative assertion 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work`(`2026-04-10-history-card-header-badge-progress-summary-docs-truth-sync.md`)로 root docs는 이미 `claim_coverage_progress_summary` non-empty 가시성 계약을 반영했지만, hidden-empty 계약은 스모크에서 정면으로 잠겨 있지 않았음
- `app/static/app.js:2962-2965`는 `progressSummary = (item.claim_coverage_progress_summary || "").trim()`만 non-empty일 때 `detailLines`에 push하므로, 빈 문자열/whitespace/meta-separator-only 회귀는 아직 관찰 가능한 contract로 고정되지 않았음
- 기존 scenario(`e2e/tests/web-smoke.spec.mjs:1102-1202`)는 card1의 non-empty progress-summary만 검증하고 card2~4의 hidden-empty 경로는 검증하지 않아, 빈 progress-summary가 blank/separator-only meta로 새어 나오는 회귀가 조용히 통과할 수 있었음
- 이 슬라이스는 런타임/도큐먼트 변경 없이 동일 isolated scenario 안에서 negative assertion만 추가해 이미 shipped된 hidden-empty 동작을 잠그는 범위임

## 핵심 변경
1. **card2 (latest_update, 빈 progress summary)**
   - `await expect(card2.locator(".meta")).toHaveCount(0)` — detailMeta가 렌더링되지 않음
   - `await expect(card2).not.toContainText("출생일: 단일 출처")` — card1의 progress-summary 텍스트가 누출되지 않음
2. **card3 (general, 빈 progress summary)**
   - `await expect(card3Meta).toHaveCount(1)` — detailMeta는 answer-mode label 한 줄로만 존재
   - `await expect(card3Meta).not.toContainText("·")` — single-line 이므로 ` · ` separator artifact 없음
   - `await expect(card3Meta).not.toContainText("출생일: 단일 출처")` — card1 progress text 누출 없음
   - `expect(card3MetaText.length).toBeGreaterThan(0)` — blank meta도 아님
3. **card4 (entity_card zero-strong-slot, 빈 progress summary, 빈 claim_coverage_summary)**
   - `await expect(card4.locator(".meta")).toHaveCount(0)` — investigation 카드라도 빈 progress summary면 detailMeta 없음
   - `await expect(card4).not.toContainText("출생일: 단일 출처")` — card1 progress text 누출 없음
- 재사용 원칙: 기존 fixture(cards 1-4)와 기존 selector(`.history-badge-row`, `.history-item`, `.meta`)를 그대로 재사용했으며 새 fixture/셀렉터를 만들지 않았음

## 검증
이번 라운드 실행:
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed (6.9s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract가 넓어지지 않았고 isolated scenario 한 개만 tightening함
- `tests.test_web_app` 등 unit suite — 런타임/라우트/도큐먼트 미변경
- 다른 history-card family scenario — 이번 변경은 해당 isolated scenario 안에서만 동작함

## 남은 리스크
- 이번 negative는 `.meta` CSS class에 의존하므로, 향후 `detailMeta`의 클래스 이름이 바뀌면 이 스모크가 먼저 깨짐. 다만 동일 selector가 기존 positive assertion(card1 `.meta`)에서도 이미 사용 중이므로 drift 범위는 동일함
- `not.toContainText("·")`는 whitespace-insensitive substring match에 의존하므로, 만약 `formatAnswerModeLabel("general")` 라벨 자체가 향후 `·`를 포함하게 바뀌면 이 negative가 잘못 걸릴 수 있음. 현재 라벨 문자열은 `·`를 포함하지 않지만, 라벨 문구 변경 시 이 어서션을 같이 검토해야 함
- blank/separator-only meta 회귀는 이번에 잠겼지만, `claim_coverage_summary`만 채워지고 `claim_coverage_progress_summary`만 빈 혼합 케이스는 fixture에 아직 없음 — 그 혼합 경로는 별도 slice가 필요하면 후속에서 좁게 닫는 편이 맞음
