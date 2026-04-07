# history-card entity-card click-reload actual-search browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 1849)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

history-card entity-card click-reload actual-search initial combined browser anchor의 title이 generic wording(`actual-search source path가 context box에 유지됩니다`)만 남아 있어, body에서 이미 검증하는 source-path(`namu.wiki`, `ko.wikipedia.org`)와 exact-field(`WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`)를 title에서 직접 드러내지 못했습니다. dual-probe family에서 이미 적용된 동일 패턴을 actual-search family에도 적용합니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 1849 | `…actual-search source path가 context box에 유지됩니다` | `…actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 actual-search" --reporter=line` → 1 passed (8.7s)

## 남은 리스크

- actual-search follow-up (`e2e/tests/web-smoke.spec.mjs:2828`)과 second-follow-up (`e2e/tests/web-smoke.spec.mjs:2949`)도 아직 generic wording이며, 다음 adjacent current-risk reduction 대상입니다.
