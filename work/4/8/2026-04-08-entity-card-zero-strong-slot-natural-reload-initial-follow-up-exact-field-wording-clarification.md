# entity-card zero-strong-slot natural-reload initial + follow-up exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 4014, 4122)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

zero-strong-slot natural-reload family의 initial/follow-up title 2개가 generic wording(`response origin badge와 answer-mode badge가 유지/drift`)만 남아 있어, body에서 이미 검증하는 exact-field(`WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`)와 source-path(`namu.wiki`, `ko.wikipedia.org`)를 title에서 직접 드러내지 못했습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 4014 | `…자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다` | `…자연어 reload에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 유지됩니다` |
| line 4122 | `…follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "zero-strong-slot.*자연어 reload" --reporter=line` → 2 passed (14.1s)

## 남은 리스크

- zero-strong-slot family 전체(click-reload + natural-reload) 모두 닫혔습니다.
- 다른 answer-mode family(crimson, entity-card actual-search natural-reload 등)의 동일 패턴은 별도 라운드 대상입니다.
