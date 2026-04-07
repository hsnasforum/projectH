# history-card entity-card click-reload dual-probe second-follow-up browser-anchor source-path+exact-field wording clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 3072)

## 사용 skill

- 없음 (test-only wording clarification)

## 변경 이유

history-card entity-card click-reload dual-probe second-follow-up combined browser anchor의 title이 generic wording(`dual-probe response origin badge와 answer-mode badge가 drift하지 않습니다`)만 남아 있어, body에서 이미 검증하는 source-path URL과 exact-field를 title에서 직접 드러내지 못했습니다. initial과 follow-up click-reload anchor에서 이미 적용된 동일 패턴을 second-follow-up에도 적용합니다.

## 핵심 변경

| 위치 | before | after |
|---|---|---|
| line 3072 | `…두 번째 follow-up 질문에서 dual-probe response origin badge와 answer-mode badge가 drift하지 않습니다` | `…두 번째 follow-up 질문에서 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다` |

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe" --reporter=line` → 1 passed (8.3s)

## 남은 리스크

- click-reload dual-probe browser-anchor wording family(initial, follow-up, second-follow-up)는 이번 라운드로 모두 닫혔습니다.
- natural-reload dual-probe family도 이전 라운드에서 모두 닫혔습니다.
- 다른 family(crimson, zero-strong-slot, latest-update)의 동일 패턴 wording은 별도 라운드 대상입니다.
