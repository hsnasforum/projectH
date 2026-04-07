# entity-card crimson-desert natural-reload exact-field browser-anchor web-badge-answer-mode wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-browser-anchor-web-badge-answer-mode-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card 붉은사막 initial natural-reload exact-field browser anchor title이 `WEB` badge와 `설명 카드` answer-mode까지 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 wording change, claimed rerun, 그리고 crimson natural-reload family closure 서술이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`가 noisy-exclusion follow-up/second-follow-up browser anchor wording까지 닫아 둔 상태였으므로, 이번에는 initial exact-field anchor까지 닫혔는지 확인하고 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:4242`의 initial natural-reload exact-field browser anchor title 보정은 current tree와 일치하고, `/work`가 적은 `session ID 변경 없음`도 `e2e/tests/web-smoke.spec.mjs:4243` 기준으로 맞았습니다.
- `/work`가 적은 rerun도 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload" --reporter=line`은 `1 passed (7.6s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- crimson natural-reload browser-anchor wording family closure도 현재 트리와 맞습니다. `e2e/tests/web-smoke.spec.mjs:4242`, `e2e/tests/web-smoke.spec.mjs:4314`, `e2e/tests/web-smoke.spec.mjs:4870`, `e2e/tests/web-smoke.spec.mjs:4990`, `e2e/tests/web-smoke.spec.mjs:5045`, `e2e/tests/web-smoke.spec.mjs:5107`, `e2e/tests/web-smoke.spec.mjs:5186`이 각각 root docs `README.md:152`, `README.md:158`, `README.md:157`, `README.md:165`, `README.md:166`, `README.md:167`와 `docs/MILESTONES.md:70`, `docs/MILESTONES.md:76`, `docs/MILESTONES.md:75`, `docs/MILESTONES.md:77`, `docs/MILESTONES.md:78`, `docs/MILESTONES.md:79`, `docs/ACCEPTANCE_CRITERIA.md:1361`, `docs/ACCEPTANCE_CRITERIA.md:1367`, `docs/ACCEPTANCE_CRITERIA.md:1366`, `docs/ACCEPTANCE_CRITERIA.md:1368`, `docs/ACCEPTANCE_CRITERIA.md:1369`, `docs/ACCEPTANCE_CRITERIA.md:1370`, `docs/TASK_BACKLOG.md:59`, `docs/TASK_BACKLOG.md:65`, `docs/TASK_BACKLOG.md:64`, `docs/TASK_BACKLOG.md:66`, `docs/TASK_BACKLOG.md:67`, `docs/TASK_BACKLOG.md:68`가 가리키는 current truth와 맞게 정렬되어 있습니다.
- 다음 Claude 슬라이스는 `entity-card dual-probe natural-reload initial browser-anchor source-path-exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:4368`, `e2e/tests/web-smoke.spec.mjs:4483` 두 initial dual-probe natural-reload anchors는 여전히 generic title만 남기지만, same bodies `e2e/tests/web-smoke.spec.mjs:4471`, `e2e/tests/web-smoke.spec.mjs:4472`, `e2e/tests/web-smoke.spec.mjs:4585`, `e2e/tests/web-smoke.spec.mjs:4590`, `e2e/tests/web-smoke.spec.mjs:4593`, `e2e/tests/web-smoke.spec.mjs:4594`, `e2e/tests/web-smoke.spec.mjs:4595`와 docs `README.md:153`, `README.md:154`, `docs/MILESTONES.md:71`, `docs/MILESTONES.md:72`, `docs/ACCEPTANCE_CRITERIA.md:1362`, `docs/ACCEPTANCE_CRITERIA.md:1363`, `docs/TASK_BACKLOG.md:60`, `docs/TASK_BACKLOG.md:61`은 더 구체적인 URL/exact-field truth를 이미 직접 가리킵니다. 두 test title만 함께 정리하는 한 묶음이 같은 browser-anchor wording 축에서 가장 작고 reviewable한 다음 slice입니다.

## 검증
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-browser-anchor-web-badge-answer-mode-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-browser-anchor-continuity-wording-clarification-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4238,5268p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4368,4600p'`
- `nl -ba README.md | sed -n '152,167p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,80p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1370p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,68p'`
- `rg -n "entity-card 붉은사막 검색 결과 자연어 reload|entity-card 붉은사막 자연어 reload에서 source path|entity-card 붉은사막 actual-search 자연어 reload 후|entity-card 붉은사막 자연어 reload 후 .*noisy single-source claim" e2e/tests/web-smoke.spec.mjs | sed -n '1,120p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload에서" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- crimson natural-reload browser-anchor wording family는 이번 라운드 기준으로 닫혔습니다.
- 다음 adjacent current-risk는 entity-card dual-probe initial natural-reload browser anchors의 generic title wording입니다. `e2e/tests/web-smoke.spec.mjs:4368`, `e2e/tests/web-smoke.spec.mjs:4483`은 still generic title만 남기지만, docs/body는 `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300`, `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반`, `백과 기반`까지 직접 가리킵니다.
