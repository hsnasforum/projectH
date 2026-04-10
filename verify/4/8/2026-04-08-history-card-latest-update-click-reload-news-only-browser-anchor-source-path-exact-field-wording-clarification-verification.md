# history-card latest-update click-reload news-only browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-latest-update-click-reload-news-only-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card latest-update news-only click-reload family의 initial source-path, follow-up response-origin, follow-up source-path, second-follow-up combined title 4개가 exact source-path와 exact field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- 오늘 same-day latest `/verify`는 single-source verification까지였으므로, 그 다음 family인 news-only wording round를 실제로 닫고 같은 click-reload family 안에서 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:2397`, `e2e/tests/web-smoke.spec.mjs:2705`, `e2e/tests/web-smoke.spec.mjs:3567`, `e2e/tests/web-smoke.spec.mjs:5331`에는 `/work`가 주장한 news-only title wording이 실제로 반영돼 있었고, 모두 `hankyung.com`, `mk.co.kr`, `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`를 직접 드러냅니다.
- news-only body/docs truth도 current tree와 맞았습니다. body는 initial source-path continuity `e2e/tests/web-smoke.spec.mjs:2484`, `e2e/tests/web-smoke.spec.mjs:2488`, `e2e/tests/web-smoke.spec.mjs:2489`, follow-up response-origin continuity `e2e/tests/web-smoke.spec.mjs:2809`, `e2e/tests/web-smoke.spec.mjs:2810`, `e2e/tests/web-smoke.spec.mjs:2813`, `e2e/tests/web-smoke.spec.mjs:2816`, `e2e/tests/web-smoke.spec.mjs:2817`, follow-up source-path continuity `e2e/tests/web-smoke.spec.mjs:3654`, `e2e/tests/web-smoke.spec.mjs:3670`, `e2e/tests/web-smoke.spec.mjs:3671`, second-follow-up combined continuity `e2e/tests/web-smoke.spec.mjs:5379`, `e2e/tests/web-smoke.spec.mjs:5380`, `e2e/tests/web-smoke.spec.mjs:5383`, `e2e/tests/web-smoke.spec.mjs:5385`, `e2e/tests/web-smoke.spec.mjs:5386`, `e2e/tests/web-smoke.spec.mjs:5389`, `e2e/tests/web-smoke.spec.mjs:5390`에서 same truth를 직접 검증합니다. docs `README.md:138`, `README.md:139`, `README.md:142`, `README.md:146`, `README.md:170`, `docs/MILESTONES.md:56`, `docs/MILESTONES.md:57`, `docs/MILESTONES.md:60`, `docs/MILESTONES.md:64`, `docs/MILESTONES.md:88`, `docs/ACCEPTANCE_CRITERIA.md:1347`, `docs/ACCEPTANCE_CRITERIA.md:1348`, `docs/ACCEPTANCE_CRITERIA.md:1351`, `docs/ACCEPTANCE_CRITERIA.md:1355`, `docs/ACCEPTANCE_CRITERIA.md:1379`, `docs/TASK_BACKLOG.md:45`, `docs/TASK_BACKLOG.md:46`, `docs/TASK_BACKLOG.md:49`, `docs/TASK_BACKLOG.md:53`, `docs/TASK_BACKLOG.md:77`도 current tree와 정렬돼 있습니다.
- focused rerun 3건은 current tree에서 모두 재현됐습니다. initial은 `1 passed (16.2s)`, follow-up 묶음은 `2 passed (22.7s)`, second-follow-up은 `1 passed (17.1s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- history-card latest-update news-only click-reload wording family는 이번 라운드 기준으로 닫혔습니다. verification label continuity `e2e/tests/web-smoke.spec.mjs:2289`, initial source-path `e2e/tests/web-smoke.spec.mjs:2397`, follow-up response-origin `e2e/tests/web-smoke.spec.mjs:2705`, follow-up source-path `e2e/tests/web-smoke.spec.mjs:3567`, second-follow-up combined continuity `e2e/tests/web-smoke.spec.mjs:5331`이 모두 docs/body truth와 정렬됐습니다.
- 다음 Claude 슬라이스는 `history-card latest-update click-reload mixed-source browser-anchor response-origin-exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:1222`, `e2e/tests/web-smoke.spec.mjs:1449`의 mixed-source response-origin title 2개만 아직 generic wording이고, same body는 initial `e2e/tests/web-smoke.spec.mjs:1309`, `e2e/tests/web-smoke.spec.mjs:1310`, `e2e/tests/web-smoke.spec.mjs:1315`, `e2e/tests/web-smoke.spec.mjs:1319`, `e2e/tests/web-smoke.spec.mjs:1320`, `e2e/tests/web-smoke.spec.mjs:1321`, follow-up `e2e/tests/web-smoke.spec.mjs:1553`, `e2e/tests/web-smoke.spec.mjs:1554`, `e2e/tests/web-smoke.spec.mjs:1557`, `e2e/tests/web-smoke.spec.mjs:1560`, `e2e/tests/web-smoke.spec.mjs:1561`, `e2e/tests/web-smoke.spec.mjs:1562`에서 `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`을 직접 검증합니다. docs `README.md:130`, `README.md:132`, `docs/MILESTONES.md:48`, `docs/MILESTONES.md:50`, `docs/ACCEPTANCE_CRITERIA.md:1339`, `docs/ACCEPTANCE_CRITERIA.md:1341`, `docs/TASK_BACKLOG.md:37`, `docs/TASK_BACKLOG.md:39`도 이미 same truth를 고정합니다. news-only까지 닫은 뒤 남는 same-family current-risk reduction으로는 이 2-title response-origin wording 정렬이 가장 작고 자연스럽습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-latest-update-click-reload-news-only-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-latest-update-click-reload-single-source-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2289,2492p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2705,2820p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3567,3680p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5331,5395p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1218,1330p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1445,1585p'`
- `nl -ba README.md | sed -n '128,146p'`
- `nl -ba README.md | sed -n '138,171p'`
- `nl -ba docs/MILESTONES.md | sed -n '46,58p'`
- `nl -ba docs/MILESTONES.md | sed -n '56,88p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1337,1349p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1347,1379p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '35,47p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '45,77p'`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update news-only 다시 불러오기 후 기사 source path" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update news-only 다시 불러오기 후 follow-up" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update news-only 다시 불러오기 후 두 번째 follow-up" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- history-card latest-update mixed-source click-reload response-origin title 2개(`e2e/tests/web-smoke.spec.mjs:1222`, `e2e/tests/web-smoke.spec.mjs:1449`)는 아직 generic wording입니다. 다음 라운드에서 `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`을 title에 직접 반영하는 편이 가장 작은 same-family current-risk reduction입니다.
- latest-update natural-reload family, zero-strong-slot family, crimson/noisy-source family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
