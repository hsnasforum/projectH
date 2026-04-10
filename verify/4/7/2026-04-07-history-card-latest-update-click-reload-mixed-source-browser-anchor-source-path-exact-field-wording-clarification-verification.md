# history-card latest-update click-reload mixed-source browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-history-card-latest-update-click-reload-mixed-source-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card latest-update mixed-source click-reload family의 initial/follow-up/second-follow-up title 3개가 exact source-path와 exact field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 entity-card actual-search click-reload second-follow-up truth-sync를 이미 닫았으므로, 이번 검증 후에는 mixed-source family가 실제로 닫혔는지 확인하고, latest-update click-reload family 안에서 다음 exact slice를 하나로 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:2079`, `e2e/tests/web-smoke.spec.mjs:3274`, `e2e/tests/web-smoke.spec.mjs:3398`에는 `/work`가 주장한 mixed-source title wording이 실제로 반영돼 있었고, 모두 `store.steampowered.com`, `yna.co.kr`, `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`을 직접 드러냅니다.
- mixed-source body/docs truth도 current tree와 맞았습니다. body는 initial `e2e/tests/web-smoke.spec.mjs:2166`, `e2e/tests/web-smoke.spec.mjs:2170`, `e2e/tests/web-smoke.spec.mjs:2171`, `e2e/tests/web-smoke.spec.mjs:2176`, `e2e/tests/web-smoke.spec.mjs:2178`, `e2e/tests/web-smoke.spec.mjs:2179`, `e2e/tests/web-smoke.spec.mjs:2180`, follow-up `e2e/tests/web-smoke.spec.mjs:3361`, `e2e/tests/web-smoke.spec.mjs:3377`, `e2e/tests/web-smoke.spec.mjs:3378`, `e2e/tests/web-smoke.spec.mjs:3383`, `e2e/tests/web-smoke.spec.mjs:3385`, `e2e/tests/web-smoke.spec.mjs:3386`, `e2e/tests/web-smoke.spec.mjs:3387`, second-follow-up `e2e/tests/web-smoke.spec.mjs:3446`, `e2e/tests/web-smoke.spec.mjs:3450`, `e2e/tests/web-smoke.spec.mjs:3452`, `e2e/tests/web-smoke.spec.mjs:3453`, `e2e/tests/web-smoke.spec.mjs:3454`, `e2e/tests/web-smoke.spec.mjs:3457`, `e2e/tests/web-smoke.spec.mjs:3458`에서 same truth를 직접 검증합니다. docs `README.md:136`, `README.md:144`, `README.md:168`, `docs/MILESTONES.md:54`, `docs/MILESTONES.md:62`, `docs/MILESTONES.md:86`, `docs/ACCEPTANCE_CRITERIA.md:1345`, `docs/ACCEPTANCE_CRITERIA.md:1353`, `docs/ACCEPTANCE_CRITERIA.md:1377`, `docs/TASK_BACKLOG.md:43`, `docs/TASK_BACKLOG.md:51`, `docs/TASK_BACKLOG.md:75`도 current tree와 정렬돼 있습니다.
- focused rerun 3건은 current tree에서 모두 재현됐습니다. initial은 `1 passed (7.6s)`, follow-up은 `1 passed (7.5s)`, second-follow-up은 `1 passed (8.2s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- history-card latest-update mixed-source click-reload wording family는 이번 라운드 기준으로 닫혔습니다. initial `e2e/tests/web-smoke.spec.mjs:2079`, follow-up `e2e/tests/web-smoke.spec.mjs:3274`, second-follow-up `e2e/tests/web-smoke.spec.mjs:3398`이 모두 docs/body truth와 정렬됐습니다.
- 다음 Claude 슬라이스는 `history-card latest-update click-reload single-source browser-anchor source-path-exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:2500`, `e2e/tests/web-smoke.spec.mjs:2592`, `e2e/tests/web-smoke.spec.mjs:3463`, `e2e/tests/web-smoke.spec.mjs:5270`의 single-source click-reload title 4개가 아직 generic wording이고, same body는 이미 initial `e2e/tests/web-smoke.spec.mjs:2577`, `e2e/tests/web-smoke.spec.mjs:2581`, follow-up `e2e/tests/web-smoke.spec.mjs:2686`, `e2e/tests/web-smoke.spec.mjs:2690`, `e2e/tests/web-smoke.spec.mjs:2693`, `e2e/tests/web-smoke.spec.mjs:2694`, `e2e/tests/web-smoke.spec.mjs:3540`, `e2e/tests/web-smoke.spec.mjs:3556`, second-follow-up `e2e/tests/web-smoke.spec.mjs:5316`, `e2e/tests/web-smoke.spec.mjs:5320`, `e2e/tests/web-smoke.spec.mjs:5322`, `e2e/tests/web-smoke.spec.mjs:5323`, `e2e/tests/web-smoke.spec.mjs:5326`에서 `example.com/seoul-weather`, `WEB`, `최신 확인`, `단일 출처 참고`, `보조 출처`를 직접 검증합니다. docs `README.md:140`, `README.md:141`, `README.md:145`, `README.md:169`, `docs/MILESTONES.md:58`, `docs/MILESTONES.md:59`, `docs/MILESTONES.md:63`, `docs/MILESTONES.md:87`, `docs/ACCEPTANCE_CRITERIA.md:1349`, `docs/ACCEPTANCE_CRITERIA.md:1350`, `docs/ACCEPTANCE_CRITERIA.md:1354`, `docs/ACCEPTANCE_CRITERIA.md:1378`, `docs/TASK_BACKLOG.md:47`, `docs/TASK_BACKLOG.md:48`, `docs/TASK_BACKLOG.md:52`, `docs/TASK_BACKLOG.md:76`도 이미 same truth를 고정합니다. single-source family는 cautionary `단일 출처 참고`/`보조 출처` continuity를 다루므로, news-only wording보다 current-risk reduction 우선순위가 약간 더 높습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-latest-update-click-reload-mixed-source-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-second-follow-up-browser-anchor-source-path-exact-field-truth-sync-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2079,2181p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3274,3460p'`
- `nl -ba README.md | sed -n '136,168p'`
- `nl -ba docs/MILESTONES.md | sed -n '54,86p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1345,1377p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '43,75p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | rg 'history-card latest-update|latest-update mixed-source|latest-update single-source|latest-update news-only'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2191,2605p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3463,3605p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5270,5355p'`
- `nl -ba README.md | sed -n '137,146p'`
- `nl -ba docs/MILESTONES.md | sed -n '55,64p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1346,1355p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '44,53p'`
- `rg -n 'single-source.*두 번째 follow-up|single-source.*second-follow-up|news-only.*두 번째 follow-up|news-only.*second-follow-up' README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2592,2725p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5331,5415p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1222,1465p'`
- `rg -n 'history-card latest-update 다시 불러오기 후 response origin badge와 answer-mode badge|history-card latest-update 다시 불러오기 후 follow-up 질문에서 response origin badge와 answer-mode badge' README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 mixed-source" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update mixed-source 다시 불러오기 후 follow-up" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update mixed-source 다시 불러오기 후 두 번째 follow-up" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- history-card latest-update single-source click-reload family의 title 4개(`e2e/tests/web-smoke.spec.mjs:2500`, `e2e/tests/web-smoke.spec.mjs:2592`, `e2e/tests/web-smoke.spec.mjs:3463`, `e2e/tests/web-smoke.spec.mjs:5270`)는 아직 generic wording입니다. 다음 라운드에서 `example.com/seoul-weather`, `WEB`, `최신 확인`, `단일 출처 참고`, `보조 출처`를 title에 직접 반영하는 편이 가장 작은 current-risk reduction입니다.
- news-only click-reload family, latest-update natural-reload family, noisy-community/noisy-single-source family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
