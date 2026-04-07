# entity-card dual-probe natural-reload second-follow-up browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 4798)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

entity-card dual-probe natural-reload second-follow-up combined browser anchor의 title이 generic wording만 남아 있어, body에서 이미 검증하는 source-path URL(`pearlabyss.com/200`, `pearlabyss.com/300`)과 exact-field(`WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반`, `백과 기반`)을 title에서 직접 드러내지 못했습니다. initial/follow-up anchor는 이전 라운드에서 이미 clarify되었으므로, 동일 패턴을 second-follow-up에도 적용합니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 4798 | `…두 번째 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…두 번째 follow-up에서 source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 두 번째 follow-up" --reporter=line` → 1 passed (8.4s)

## 남은 리스크

- dual-probe natural-reload browser-anchor wording family(initial, follow-up, second-follow-up)는 이번 라운드로 모두 닫혔습니다.
- 다른 family(crimson, click-reload, zero-strong-slot, latest-update)의 동일 패턴 wording은 이번 라운드 범위 밖입니다.
