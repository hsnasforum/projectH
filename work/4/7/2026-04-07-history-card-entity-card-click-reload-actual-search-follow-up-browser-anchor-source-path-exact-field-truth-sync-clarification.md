# history-card entity-card click-reload actual-search follow-up browser-anchor source-path+exact-field truth-sync clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 2828, 2933)

## 사용 skill

- 없음 (test-only truth-sync + wording clarification)

## 변경 이유

history-card entity-card click-reload actual-search follow-up combined browser anchor에 두 가지 gap이 있었습니다:
1. Post-follow-up에서 `originBadge` WEB 재확인이 빠져 있어, follow-up 뒤 badge drift 여부를 직접 검증하지 못했습니다.
2. Title이 generic wording(`actual-search source path가 context box에 유지됩니다`)만 남아 있어, body에서 이미 검증하는 exact truth를 title에서 드러내지 못했습니다.

## 핵심 변경

| 위치 | 변경 내용 |
|---|---|
| line 2828 | title → `…actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다` |
| line 2933 | post-follow-up `await expect(originBadge).toHaveText("WEB")` assertion 추가 |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search" --reporter=line` → 1 passed (9.1s)

## 남은 리스크

- actual-search second-follow-up (`e2e/tests/web-smoke.spec.mjs:2949`)도 아직 generic wording이며, 다음 adjacent current-risk reduction 대상입니다.
