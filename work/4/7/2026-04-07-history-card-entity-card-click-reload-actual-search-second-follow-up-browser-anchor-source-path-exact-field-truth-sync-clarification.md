# history-card entity-card click-reload actual-search second-follow-up browser-anchor source-path+exact-field truth-sync clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 2950, 3063)

## 사용 skill

- 없음 (test-only truth-sync + wording clarification)

## 변경 이유

history-card entity-card click-reload actual-search second-follow-up combined browser anchor에 두 가지 gap이 있었습니다:
1. Post-second-follow-up에서 `originBadge` WEB 재확인이 빠져 있어, second-follow-up 뒤 badge drift 여부를 직접 검증하지 못했습니다.
2. Title이 generic wording만 남아 있어, body에서 이미 검증하는 exact truth를 title에서 드러내지 못했습니다.

## 핵심 변경

| 위치 | 변경 내용 |
|---|---|
| line 2950 | title → `…actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다` |
| line 3063 | post-second-follow-up `await expect(originBadge).toHaveText("WEB")` assertion 추가 |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search" --reporter=line` → 1 passed (8.7s)

## 남은 리스크

- click-reload actual-search browser-anchor wording family(initial, follow-up, second-follow-up)는 이번 라운드로 모두 닫혔습니다.
- click-reload dual-probe family도 이전 라운드에서 모두 닫혔습니다.
- natural-reload dual-probe family도 이전 라운드에서 모두 닫혔습니다.
- 다른 family(crimson, zero-strong-slot, latest-update)의 동일 패턴은 별도 라운드 대상입니다.
