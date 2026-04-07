# latest-update mixed-source natural-reload browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 5395, 5573, 5638)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

latest-update mixed-source natural-reload family의 initial/follow-up/second-follow-up title 3개가 generic wording(`source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다`)만 남아 있어, body에서 이미 검증하는 exact source-path(`store.steampowered.com`, `yna.co.kr`)와 exact-field(`WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 5395 | `…source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다` |
| line 5573 | `…follow-up에서 source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…follow-up에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다` |
| line 5638 | `…두 번째 follow-up에서 source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…두 번째 follow-up에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update mixed-source 자연어 reload" --reporter=line` → 3 passed (20.2s)

## 남은 리스크

- latest-update mixed-source natural-reload family(3 anchors)는 이번 라운드로 모두 닫혔습니다.
- 다른 natural-reload family(single-source, news-only)와 다른 answer-mode family(zero-strong-slot, crimson 등)의 동일 패턴은 별도 라운드 대상입니다.
