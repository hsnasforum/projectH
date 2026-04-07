# history-card entity-card click-reload initial + follow-up exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 1112, 1332)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

history-card entity-card click-reload initial/follow-up title 2개가 generic wording(`response origin badge와 answer-mode badge가 유지/drift`)만 남아 있었습니다. 이 2건은 `rg -n "response origin badge와 answer-mode badge"` 기준 마지막 remaining generic title이며, body에서 이미 검증하는 exact-field(`WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`)를 title에서 직접 드러내도록 맞췄습니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 1112 | `history-card 다시 불러오기 클릭 후 response origin badge와 answer-mode badge가 유지됩니다` | `history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다` |
| line 1332 | `history-card 다시 불러오기 후 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- line 1112 → 1 passed (8.4s)
- line 1332 → 1 passed (7.7s)

## 남은 리스크

- `response origin badge와 answer-mode badge` generic wording은 이번 라운드로 전체 0건으로 닫혔습니다.
- 다른 answer-mode family(crimson, entity-card actual-search natural-reload 등)의 별도 패턴은 별도 라운드 대상입니다.
