# history-card latest-update click-reload mixed-source browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 2079, 3274, 3398)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

history-card latest-update mixed-source click-reload family의 initial/follow-up/second-follow-up title 3개가 generic wording만 남아 있어, body에서 이미 검증하는 exact source-path(`store.steampowered.com`, `yna.co.kr`)와 exact-field(`WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 2079 | `…mixed-source source path가 context box에 유지됩니다` | `…mixed-source source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다` |
| line 3274 | `…follow-up 질문에서 source path가 context box에 유지됩니다` | `…follow-up 질문에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다` |
| line 3398 | `…두 번째 follow-up 질문에서 source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…두 번째 follow-up 질문에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- initial → 1 passed (8.2s)
- follow-up → 1 passed (7.7s)
- second-follow-up → 1 passed (7.6s)

## 남은 리스크

- latest-update mixed-source click-reload family(initial, follow-up, second-follow-up)는 이번 라운드로 모두 닫혔습니다.
- 다른 family(latest-update single-source/news-only, zero-strong-slot, crimson 등)의 동일 패턴은 별도 라운드 대상입니다.
