# history-card latest-update click-reload mixed-source response-origin exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 1222, 1449)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

history-card latest-update mixed-source click-reload family의 initial/follow-up response-origin title 2개가 generic wording(`response origin badge와 answer-mode badge가 유지/drift`)만 남아 있어, body에서 이미 검증하는 exact-field(`WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 1222 | `…response origin badge와 answer-mode badge가 유지됩니다` | `…WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다` |
| line 1449 | `…follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…follow-up 질문에서 WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- line 1222 → 1 passed (8.2s)
- line 1449 → 1 passed (8.1s)

## 남은 리스크

- latest-update mixed-source click-reload response-origin family(2 anchors)는 이번 라운드로 닫혔습니다.
- latest-update click-reload family 전체(mixed-source source-path/response-origin, single-source, news-only)가 모두 닫혔습니다.
- 다른 family(zero-strong-slot, crimson, latest-update single-source/news-only response-origin 등)의 동일 패턴은 별도 라운드 대상입니다.
