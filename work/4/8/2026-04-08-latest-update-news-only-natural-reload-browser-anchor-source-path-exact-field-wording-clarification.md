# latest-update news-only natural-reload browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 5513, 5833, 5897)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

latest-update news-only natural-reload family의 initial/follow-up/second-follow-up title 3개가 generic wording만 남아 있어, body에서 이미 검증하는 exact source-path(`hankyung.com`, `mk.co.kr`)와 exact-field(`WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 5513 | `…기사 source path가…drift하지 않습니다` | `…기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다` |
| line 5833 | `…follow-up에서 기사 source path가…drift하지 않습니다` | `…follow-up에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다` |
| line 5897 | `…두 번째 follow-up에서 기사 source path가…drift하지 않습니다` | `…두 번째 follow-up에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update news-only 자연어 reload" --reporter=line` → 3 passed (22.5s)

## 남은 리스크

- latest-update natural-reload family 전체(mixed-source, single-source, news-only)가 이번 라운드로 모두 닫혔습니다.
- latest-update click-reload family도 이전 라운드에서 모두 닫혔습니다.
- 다른 answer-mode family(zero-strong-slot, crimson, entity-card actual-search natural-reload 등)의 동일 패턴은 별도 라운드 대상입니다.
