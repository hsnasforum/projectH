# history-card entity-card zero-strong-slot click-reload initial + follow-up + second-follow-up exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 3682, 3784, 3901)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

zero-strong-slot click-reload family의 initial/follow-up/second-follow-up title 3개가 generic wording만 남아 있어, body에서 이미 검증하는 exact-field(`WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`)와 source-path(`namu.wiki`, `ko.wikipedia.org`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 3682 | `…설명 카드 answer-mode badge와 설명형 단일 출처 verification label이 유지됩니다` | `…WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 유지됩니다` |
| line 3784 | `…follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다` |
| line 3901 | `…두 번째 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "zero-strong-slot.*다시 불러오기 후" --reporter=line` → 3 passed (20.1s)

## 남은 리스크

- zero-strong-slot click-reload family(3 anchors)는 이번 라운드로 닫혔습니다.
- zero-strong-slot natural-reload family와 다른 answer-mode family(crimson, entity-card actual-search natural-reload 등)의 동일 패턴은 별도 라운드 대상입니다.
