## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-ordered-label-exact-text-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-preview-card-ordered-label-exact-text-smoke-tightening.md`의 test-only smoke tightening 주장이 현재 tree와 rerun 결과 기준으로 truthful한지 다시 검수하고, preview-card family 안에서 다음 exact current-risk reduction 한 슬라이스를 정하기 위해서입니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다. `e2e/tests/web-smoke.spec.mjs`의 ordered-label assertions는 search-plus-summary / search-only 각각의 response detail / transcript 네 surface에서 모두 `toHaveText("1. budget-plan.md")` / `toHaveText("2. memo.md")`로 강화되어 있습니다.
- `rg -n "toContainText\\(\"1\\. budget-plan\\.md\"\\)|toContainText\\(\"2\\. memo\\.md\"\\)|search-preview-name.*toContainText" e2e/tests/web-smoke.spec.mjs`는 0건이었고, `rg -n "search-preview-name.*toContainText|toHaveText\\(\\\"1\\. budget-plan\\.md\\\"\\)|toHaveText\\(\\\"2\\. memo\\.md\\\"\\)|toContainText\\(\\\"1\\. budget-plan\\.md\\\"\\)|toContainText\\(\\\"2\\. memo\\.md\\\"\\)" e2e/tests/web-smoke.spec.mjs`는 8건이었습니다. ordered-label exact visible text smoke tightening은 현재 tree에 실제로 반영되어 있습니다.
- `app/static/app.js`의 response detail / transcript 렌더링은 여전히 `nameEl.textContent = (idx + 1) + ". " + fileName;`를 사용하므로, exact text assertion으로 잠근 `/work` 판단은 current shipped UI와 일치합니다.
- latest `/work`의 `make e2e-test` 통과 주장도 rerun 기준으로 truthful했습니다. 이번 검증에서 `make e2e-test`를 다시 실행했고 `17 passed (2.4m)`로 종료되었습니다.
- current target test file는 현재 `git diff -- e2e/tests/web-smoke.spec.mjs` 기준으로 clean합니다. 검수 관점에서는 latest `/work`에서 주장한 test tightening이 이미 current tree에 흡수된 상태이며, 그 주장과 모순되지는 않습니다.
- same-day latest `/verify`였던 `verify/4/3/2026-04-03-document-search-preview-card-ordered-label-current-contract-docs-truth-sync-verification.md`는 사실관계 자체는 맞지만, 거기서 제안한 next slice는 latest `/work`가 실제로 닫았으므로 handoff로서는 stale입니다.
- 다음 exact slice는 `document-search preview-card match-badge exact-text smoke tightening`으로 갱신했습니다. current smoke는 preview-card match badge를 네 surface에서 모두 `toContainText("파일명 일치")` / `toContainText("내용 일치")`로만 확인하지만, current shipped UI는 `matchLabel = sr.matched_on === "filename" ? "파일명 일치" : "내용 일치"`로 exact visible text를 렌더링합니다. 같은 family의 가장 작은 current-risk reduction은 이 badge assertions를 exact text로 잠그는 것입니다.

## 검증
- `sed -n '1,260p' work/4/3/2026-04-03-document-search-preview-card-ordered-label-exact-text-smoke-tightening.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-preview-card-ordered-label-current-contract-docs-truth-sync-verification.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `sed -n '196,292p' e2e/tests/web-smoke.spec.mjs`
- `rg -n "search-preview-name.*toContainText|toHaveText\\(\\\"1\\. budget-plan\\.md\\\"\\)|toHaveText\\(\\\"2\\. memo\\.md\\\"\\)|toContainText\\(\\\"1\\. budget-plan\\.md\\\"\\)|toContainText\\(\\\"2\\. memo\\.md\\\"\\)" e2e/tests/web-smoke.spec.mjs`
- `rg -n "toContainText\\(\\\"1\\. budget-plan\\.md\\\"\\)|toContainText\\(\\\"2\\. memo\\.md\\\"\\)|search-preview-name.*toContainText" e2e/tests/web-smoke.spec.mjs`
- `rg -n "toContainText\\(\\\"파일명 일치\\\"\\)|toContainText\\(\\\"내용 일치\\\"\\)|toHaveText\\(\\\"파일명 일치\\\"\\)|toHaveText\\(\\\"내용 일치\\\"\\)" e2e/tests/web-smoke.spec.mjs`
- `sed -n '1008,1022p' app/static/app.js`
- `sed -n '1188,1202p' app/static/app.js`
- `rg -n 'matchLabel = sr\\.matched_on === "filename" \\? "파일명 일치" : "내용 일치"' app/static/app.js`
- `make e2e-test` — 17 passed (2.4m)
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. test-only smoke-tightening 라운드였고 server 로직 변경이 없기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `.pipeline/*`, watcher, operator 문서, `AGENTS.md` 계열 dirty 변경을 정리하거나 되돌리면 안 됩니다.
- preview-card ordered-label exact-text smoke tightening은 now aligned이지만, preview-card match badge smoke는 아직 exact visible text까지 잠겨 있지 않습니다.
- snippet text는 current contract상 exact string이 아니라 content presence에 더 가깝기 때문에, 다음 same-family current-risk reduction은 snippet exactness가 아니라 match badge exactness가 더 좁고 truthful합니다.
