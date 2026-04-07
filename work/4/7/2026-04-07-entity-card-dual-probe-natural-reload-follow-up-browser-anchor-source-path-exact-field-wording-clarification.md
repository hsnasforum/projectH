# entity-card dual-probe natural-reload follow-up browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 4606, 4735)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

entity-card dual-probe natural-reload follow-up browser anchor 2개의 title이 generic wording만 남아 있어, body에서 이미 검증하는 exact truth(source-path URL, exact-field badge/label)를 title에서 직접 드러내지 못했습니다. initial anchor는 이전 라운드에서 이미 clarify되었으므로, 동일 패턴을 follow-up pair에도 적용합니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 4606 | `…follow-up에서 source path가 context box에 유지됩니다` | `…follow-up에서 source path(pearlabyss.com/200, pearlabyss.com/300)가 context box에 유지됩니다` |
| line 4735 | `…follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다` | `…follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up" --reporter=line` → 2 passed (14.6s)

## 남은 리스크

- second-follow-up combined anchor (`e2e/tests/web-smoke.spec.mjs:4798`)도 아직 generic wording이며, 다음 adjacent current-risk reduction 대상입니다.
- initial/follow-up/second-follow-up 외 다른 family(crimson, click-reload, zero-strong-slot, latest-update)의 동일 패턴 wording은 이번 라운드 범위 밖입니다.
