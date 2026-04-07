# history-card latest-update click-reload single-source browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 2500, 2592, 3463, 5270)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

history-card latest-update single-source click-reload family의 initial source-path, follow-up response-origin, follow-up source-path, second-follow-up combined title 4개가 generic wording만 남아 있어, body에서 이미 검증하는 exact source-path(`example.com/seoul-weather`)와 exact-field(`WEB`, `최신 확인`, `단일 출처 참고`, `보조 출처`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 2500 | `…source path가 context box에 유지됩니다` | `…source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다` |
| line 2592 | `…follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…follow-up 질문에서 WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 drift하지 않습니다` |
| line 3463 | `…follow-up 질문에서 source path가 context box에 유지됩니다` | `…follow-up 질문에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다` |
| line 5270 | `…두 번째 follow-up 질문에서 source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…두 번째 follow-up 질문에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- initial → 1 passed (8.0s)
- follow-up (2 tests) → 2 passed (12.9s)
- second-follow-up → 1 passed (7.8s)

## 남은 리스크

- latest-update single-source click-reload family(4 anchors)는 이번 라운드로 모두 닫혔습니다.
- 다른 family(latest-update news-only, zero-strong-slot, crimson 등)의 동일 패턴은 별도 라운드 대상입니다.
