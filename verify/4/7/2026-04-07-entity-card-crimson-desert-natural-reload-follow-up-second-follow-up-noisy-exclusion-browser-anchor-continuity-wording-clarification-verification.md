# entity-card crimson-desert natural-reload follow-up/second-follow-up noisy-exclusion browser-anchor continuity wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-browser-anchor-continuity-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card 붉은사막 natural-reload follow-up/second-follow-up noisy-exclusion browser anchor title이 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` continuity까지 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 wording change, claimed rerun, 그리고 family closure 서술이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`가 actual-search follow-up/second-follow-up browser anchor wording을 already 닫아 둔 상태였으므로, 이번에는 noisy-exclusion anchors가 실제로 닫혔는지와 같은 crimson natural-reload family 안에 무엇이 한 칸 더 남았는지 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`는 부분만 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:5107`, `e2e/tests/web-smoke.spec.mjs:5186`의 noisy-exclusion follow-up/second-follow-up title wording 보정은 current tree와 일치하고, `/work`가 적은 `session ID 변경 없음`도 `e2e/tests/web-smoke.spec.mjs:5108`, `e2e/tests/web-smoke.spec.mjs:5187` 기준으로 맞았습니다.
- intended crimson-only rerun은 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 .*noisy single-source claim" --reporter=line`은 `2 passed (13.4s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- 다만 `/work`가 적은 broad rerun `npx playwright test -g "noisy single-source claim": 2 passed`는 현재 트리 기준으로 맞지 않습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "noisy single-source claim" --reporter=line`을 다시 돌리면 `e2e/tests/web-smoke.spec.mjs:1701`, `e2e/tests/web-smoke.spec.mjs:4242`, `e2e/tests/web-smoke.spec.mjs:5107`, `e2e/tests/web-smoke.spec.mjs:5186`, `e2e/tests/web-smoke.spec.mjs:6242`, `e2e/tests/web-smoke.spec.mjs:6315`, `e2e/tests/web-smoke.spec.mjs:6391`, `e2e/tests/web-smoke.spec.mjs:6460`까지 총 `8`개가 잡혀 `8 passed (46.2s)`였습니다.
- `/work`의 `붉은사막 natural-reload family 전체 browser anchor wording clarification 완료`도 과장입니다. initial natural-reload exact-field anchor `e2e/tests/web-smoke.spec.mjs:4242`는 still `noisy single-source claim`, `설명형 다중 출처 합의`, `백과 기반`, provenance만 직접 적는데, root docs인 `README.md:152`, `docs/MILESTONES.md:70`, `docs/ACCEPTANCE_CRITERIA.md:1361`, `docs/TASK_BACKLOG.md:59`와 same body `e2e/tests/web-smoke.spec.mjs:4288`, `e2e/tests/web-smoke.spec.mjs:4292`, `e2e/tests/web-smoke.spec.mjs:4294`, `e2e/tests/web-smoke.spec.mjs:4295`는 `WEB` badge와 `설명 카드` answer-mode까지 exact field로 함께 가리킵니다.
- 다음 Claude 슬라이스는 `entity-card crimson-desert natural-reload exact-field browser-anchor web-badge-answer-mode wording clarification`으로 고정했습니다. runtime/assertion logic과 docs를 건드리지 않고 `e2e/tests/web-smoke.spec.mjs:4242` initial natural-reload exact-field anchor title wording만 body/docs truth에 맞추는 test-only clarification이 same-family smallest current-risk reduction입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-browser-anchor-continuity-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-actual-search-natural-reload-follow-up-second-follow-up-browser-anchor-source-path-response-origin-wording-clarification-verification.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4238,4370p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5104,5268p'`
- `nl -ba README.md | sed -n '152,167p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,80p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1360,1371p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,69p'`
- `rg -n "붉은사막.*자연어 reload|noisy single-source claim|blog.example.com provenance|설명 카드|설명형 다중 출처 합의|백과 기반" e2e/tests/web-smoke.spec.mjs README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md | sed -n '1,220p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "noisy single-source claim" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 .*noisy single-source claim" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 entity-card 붉은사막 initial natural-reload exact-field browser anchor wording weakness입니다. `e2e/tests/web-smoke.spec.mjs:4242`의 title이 body와 docs가 이미 검사하는 `WEB` badge와 `설명 카드` answer-mode를 직접 드러내지 않습니다.
- 다음 라운드는 `e2e/tests/web-smoke.spec.mjs:4242` initial natural-reload exact-field browser anchor title wording만 다루는 test-only clarification으로 충분합니다. source-path-only initial anchor, actual-search follow-up/second-follow-up anchors, noisy-exclusion follow-up/second-follow-up anchors, click-reload family, docs, service tests는 범위 밖입니다.
