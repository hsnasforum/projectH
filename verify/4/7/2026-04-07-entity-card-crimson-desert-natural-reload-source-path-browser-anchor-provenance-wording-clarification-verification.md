# entity-card crimson-desert natural-reload source-path browser-anchor provenance wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-source-path-browser-anchor-provenance-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card 붉은사막 natural-reload source-path-only browser anchor title/session naming이 provenance plurality truth를 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 code change, exact rerun, 그리고 family closure 서술이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`가 exact-field browser anchor를 already 닫았으므로, 이번에는 source-path-only anchor까지 닫혔는지와 다음 same-family current-risk가 어디에 남는지 좁혀야 했습니다.

## 핵심 변경
- latest `/work`는 부분만 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:4314`, `e2e/tests/web-smoke.spec.mjs:4315`의 source-path-only title/session naming 보정은 current tree와 일치했고, same test body `e2e/tests/web-smoke.spec.mjs:4360`, `e2e/tests/web-smoke.spec.mjs:4361`, `e2e/tests/web-smoke.spec.mjs:4362`, `e2e/tests/web-smoke.spec.mjs:4363`가 검사하는 `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance plurality truth와도 맞았습니다.
- `/work`가 적은 exact rerun도 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload에서 source path" --reporter=line`은 `1 passed (7.4s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- 다만 `/work`의 `붉은사막 natural-reload family browser anchor wording clarification 전체 완료`는 과장입니다. root docs와 service anchors인 `README.md:157`, `README.md:159`, `README.md:165`, `docs/MILESTONES.md:75`, `docs/MILESTONES.md:77`, `docs/MILESTONES.md:85`, `docs/ACCEPTANCE_CRITERIA.md:1366`, `docs/ACCEPTANCE_CRITERIA.md:1368`, `docs/ACCEPTANCE_CRITERIA.md:1376`, `docs/TASK_BACKLOG.md:64`, `docs/TASK_BACKLOG.md:66`, `docs/TASK_BACKLOG.md:74`, `tests/test_web_app.py:16507`, `tests/test_web_app.py:16577`, `tests/test_web_app.py:16582`는 actual-search natural-reload follow-up/second-follow-up에서 source-path plurality와 response-origin continuity를 직접 적습니다.
- 반면 browser anchors `e2e/tests/web-smoke.spec.mjs:4870`, `e2e/tests/web-smoke.spec.mjs:4990`, `e2e/tests/web-smoke.spec.mjs:5045`와 session naming `e2e/tests/web-smoke.spec.mjs:4871`, `e2e/tests/web-smoke.spec.mjs:4991`, `e2e/tests/web-smoke.spec.mjs:5046`은 still generic wording만 남기지만, same bodies `e2e/tests/web-smoke.spec.mjs:4977`, `e2e/tests/web-smoke.spec.mjs:4978`, `e2e/tests/web-smoke.spec.mjs:5033`, `e2e/tests/web-smoke.spec.mjs:5039`, `e2e/tests/web-smoke.spec.mjs:5040`, `e2e/tests/web-smoke.spec.mjs:5091`, `e2e/tests/web-smoke.spec.mjs:5097`, `e2e/tests/web-smoke.spec.mjs:5098`, `e2e/tests/web-smoke.spec.mjs:5100`, `e2e/tests/web-smoke.spec.mjs:5101`, `e2e/tests/web-smoke.spec.mjs:5102`는 already exact source-path + response-origin truth를 직접 검사합니다.
- 다음 Claude 슬라이스는 `entity-card crimson-desert actual-search natural-reload follow-up-second-follow-up browser-anchor source-path-response-origin wording clarification`으로 고정했습니다. runtime/assertion logic을 건드리지 않고 actual-search natural-reload follow-up/second-follow-up browser anchors의 title/session naming만 docs/body truth에 맞추는 test-only wording clarification이 same-family smallest current-risk reduction입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-source-path-browser-anchor-provenance-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-browser-anchor-noisy-exclusion-provenance-wording-clarification-verification.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4310,4370p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4866,5106p'`
- `nl -ba README.md | sed -n '156,166p'`
- `nl -ba docs/MILESTONES.md | sed -n '74,86p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1365,1378p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '63,75p'`
- `nl -ba tests/test_web_app.py | sed -n '16486,16588p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload에서 source path" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 narrow browser-anchor verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 entity-card 붉은사막 actual-search natural-reload follow-up/second-follow-up browser anchor wording weakness입니다. `e2e/tests/web-smoke.spec.mjs:4870`, `e2e/tests/web-smoke.spec.mjs:4990`, `e2e/tests/web-smoke.spec.mjs:5045`의 generic title/session naming이 body가 이미 검사하는 `namu.wiki`, `ko.wikipedia.org` source-path plurality와 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` continuity를 직접 드러내지 않습니다.
- 다음 라운드는 `e2e/tests/web-smoke.spec.mjs` actual-search natural-reload follow-up/second-follow-up browser anchors만 다루는 test-only wording clarification으로 충분합니다. exact-field/source-path-only initial anchors, noisy-exclusion anchors, click-reload family, docs, service tests는 범위 밖입니다.
