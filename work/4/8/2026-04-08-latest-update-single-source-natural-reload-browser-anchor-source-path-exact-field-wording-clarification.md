# latest-update single-source natural-reload browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 5456, 5707, 5768)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

latest-update single-source natural-reload family의 initial/follow-up/second-follow-up title 3개가 generic wording만 남아 있어, body에서 이미 검증하는 exact source-path(`example.com/seoul-weather`)와 exact-field(`WEB`, `최신 확인`, `단일 출처 참고`, `보조 출처`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 5456 | `…source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다` |
| line 5707 | `…follow-up에서 source path가…drift하지 않습니다` | `…follow-up에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다` |
| line 5768 | `…두 번째 follow-up에서 source path가…drift하지 않습니다` | `…두 번째 follow-up에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update single-source 자연어 reload" --reporter=line` → 3 passed (19.6s)

## 남은 리스크

- latest-update single-source natural-reload family(3 anchors)는 이번 라운드로 모두 닫혔습니다.
- 다른 natural-reload family(news-only)와 다른 answer-mode family(zero-strong-slot, crimson 등)의 동일 패턴은 별도 라운드 대상입니다.
