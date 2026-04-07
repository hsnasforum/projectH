# history-card latest-update click-reload news-only browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 2397, 2705, 3567, 5331)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

history-card latest-update news-only click-reload family의 initial source-path, follow-up response-origin, follow-up source-path, second-follow-up combined title 4개가 generic wording만 남아 있어, body에서 이미 검증하는 exact source-path(`hankyung.com`, `mk.co.kr`)와 exact-field(`WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 2397 | `…기사 source path가 context box에 유지됩니다` | `…기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다` |
| line 2705 | `…follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…follow-up 질문에서 WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 drift하지 않습니다` |
| line 3567 | `…follow-up 질문에서 기사 source path가 context box에 유지됩니다` | `…follow-up 질문에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다` |
| line 5331 | `…두 번째 follow-up 질문에서 기사 source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…두 번째 follow-up 질문에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- initial → 1 passed (8.1s)
- follow-up (2 tests) → 2 passed (13.1s)
- second-follow-up → 1 passed (7.9s)

## 남은 리스크

- latest-update news-only click-reload family(4 anchors)는 이번 라운드로 모두 닫혔습니다.
- latest-update click-reload family 전체(mixed-source, single-source, news-only)가 모두 닫혔습니다.
- 다른 family(zero-strong-slot, crimson 등)의 동일 패턴은 별도 라운드 대상입니다.
