# history-card entity-card click-reload dual-probe follow-up browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 3140)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

history-card entity-card click-reload dual-probe follow-up combined browser anchor의 title이 generic wording(`dual-probe source path가 context box에 유지됩니다`)만 남아 있어, body에서 이미 검증하는 source-path URL(`pearlabyss.com/200`, `pearlabyss.com/300`)과 exact-field(`WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반`, `백과 기반`)을 title에서 직접 드러내지 못했습니다. initial click-reload anchor에서 이미 적용된 동일 패턴을 follow-up에도 적용합니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 3140 | `…follow-up 질문에서 dual-probe source path가 context box에 유지됩니다` | `…follow-up 질문에서 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe" --reporter=line` → 1 passed (8.1s)

## 남은 리스크

- history-card dual-probe second-follow-up (`e2e/tests/web-smoke.spec.mjs:3072`)도 아직 generic wording이며, 다음 adjacent current-risk reduction 대상입니다.
