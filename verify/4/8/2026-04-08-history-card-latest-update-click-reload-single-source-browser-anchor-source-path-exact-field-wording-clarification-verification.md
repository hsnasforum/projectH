# history-card latest-update click-reload single-source browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-latest-update-click-reload-single-source-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card latest-update single-source click-reload family의 initial source-path, follow-up response-origin, follow-up source-path, second-follow-up combined title 4개가 exact source-path와 exact field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- 오늘 same-day `/verify`는 아직 없었으므로, 이전 verify 흐름을 이어받아 single-source family가 실제로 닫혔는지 확인하고, latest-update click-reload family 안에서 다음 exact slice를 하나로 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:2500`, `e2e/tests/web-smoke.spec.mjs:2592`, `e2e/tests/web-smoke.spec.mjs:3463`, `e2e/tests/web-smoke.spec.mjs:5270`에는 `/work`가 주장한 single-source title wording이 실제로 반영돼 있었고, 모두 `example.com/seoul-weather`, `WEB`, `최신 확인`, `단일 출처 참고`, `보조 출처`를 직접 드러냅니다.
- single-source body/docs truth도 current tree와 맞았습니다. body는 initial `e2e/tests/web-smoke.spec.mjs:2577`, `e2e/tests/web-smoke.spec.mjs:2581`, follow-up response-origin `e2e/tests/web-smoke.spec.mjs:2686`, `e2e/tests/web-smoke.spec.mjs:2690`, `e2e/tests/web-smoke.spec.mjs:2693`, `e2e/tests/web-smoke.spec.mjs:2694`, follow-up source-path `e2e/tests/web-smoke.spec.mjs:3540`, `e2e/tests/web-smoke.spec.mjs:3556`, second-follow-up `e2e/tests/web-smoke.spec.mjs:5316`, `e2e/tests/web-smoke.spec.mjs:5320`, `e2e/tests/web-smoke.spec.mjs:5322`, `e2e/tests/web-smoke.spec.mjs:5323`, `e2e/tests/web-smoke.spec.mjs:5326`에서 same truth를 직접 검증합니다. docs `README.md:140`, `README.md:141`, `README.md:145`, `README.md:169`, `docs/MILESTONES.md:58`, `docs/MILESTONES.md:59`, `docs/MILESTONES.md:63`, `docs/MILESTONES.md:87`, `docs/ACCEPTANCE_CRITERIA.md:1349`, `docs/ACCEPTANCE_CRITERIA.md:1350`, `docs/ACCEPTANCE_CRITERIA.md:1354`, `docs/ACCEPTANCE_CRITERIA.md:1378`, `docs/TASK_BACKLOG.md:47`, `docs/TASK_BACKLOG.md:48`, `docs/TASK_BACKLOG.md:52`, `docs/TASK_BACKLOG.md:76`도 current tree와 정렬돼 있습니다.
- focused rerun 3건은 current tree에서 모두 재현됐습니다. initial은 `1 passed (7.4s)`, follow-up 묶음은 `2 passed (13.0s)`, second-follow-up은 `1 passed (7.6s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- history-card latest-update single-source click-reload wording family는 이번 라운드 기준으로 닫혔습니다. initial `e2e/tests/web-smoke.spec.mjs:2500`, follow-up response-origin `e2e/tests/web-smoke.spec.mjs:2592`, follow-up source-path `e2e/tests/web-smoke.spec.mjs:3463`, second-follow-up `e2e/tests/web-smoke.spec.mjs:5270`이 모두 docs/body truth와 정렬됐습니다.
- 다음 Claude 슬라이스는 `history-card latest-update click-reload news-only browser-anchor source-path-exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:2397`, `e2e/tests/web-smoke.spec.mjs:2705`, `e2e/tests/web-smoke.spec.mjs:3567`, `e2e/tests/web-smoke.spec.mjs:5331`의 news-only click-reload title 4개가 아직 generic wording이고, same body는 initial `e2e/tests/web-smoke.spec.mjs:2484`, `e2e/tests/web-smoke.spec.mjs:2488`, `e2e/tests/web-smoke.spec.mjs:2489`, follow-up response-origin `e2e/tests/web-smoke.spec.mjs:2809`, `e2e/tests/web-smoke.spec.mjs:2810`, `e2e/tests/web-smoke.spec.mjs:2813`, `e2e/tests/web-smoke.spec.mjs:2816`, `e2e/tests/web-smoke.spec.mjs:2817`, follow-up source-path `e2e/tests/web-smoke.spec.mjs:3654`, `e2e/tests/web-smoke.spec.mjs:3670`, `e2e/tests/web-smoke.spec.mjs:3671`, second-follow-up `e2e/tests/web-smoke.spec.mjs:5379`, `e2e/tests/web-smoke.spec.mjs:5380`, `e2e/tests/web-smoke.spec.mjs:5383`, `e2e/tests/web-smoke.spec.mjs:5385`, `e2e/tests/web-smoke.spec.mjs:5386`, `e2e/tests/web-smoke.spec.mjs:5389`, `e2e/tests/web-smoke.spec.mjs:5390`에서 `hankyung.com`, `mk.co.kr`, `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`를 직접 검증합니다. docs `README.md:138`, `README.md:139`, `README.md:142`, `README.md:146`, `README.md:170`, `docs/MILESTONES.md:56`, `docs/MILESTONES.md:57`, `docs/MILESTONES.md:60`, `docs/MILESTONES.md:64`, `docs/MILESTONES.md:88`, `docs/ACCEPTANCE_CRITERIA.md:1347`, `docs/ACCEPTANCE_CRITERIA.md:1348`, `docs/ACCEPTANCE_CRITERIA.md:1351`, `docs/ACCEPTANCE_CRITERIA.md:1355`, `docs/ACCEPTANCE_CRITERIA.md:1379`, `docs/TASK_BACKLOG.md:45`, `docs/TASK_BACKLOG.md:46`, `docs/TASK_BACKLOG.md:49`, `docs/TASK_BACKLOG.md:53`, `docs/TASK_BACKLOG.md:77`도 이미 same truth를 고정합니다. mixed-source와 single-source를 닫은 뒤 남는 same-family current-risk reduction으로는 news-only wording family가 가장 자연스럽습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-latest-update-click-reload-single-source-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-latest-update-click-reload-mixed-source-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2500,2605p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2592,2725p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3463,3567p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5270,5332p'`
- `nl -ba README.md | sed -n '140,145p;169,169p'`
- `nl -ba docs/MILESTONES.md | sed -n '58,63p;87,87p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1349,1354p;1378,1378p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '47,52p;76,76p'`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update single-source 다시 불러오기 후 source path" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update single-source 다시 불러오기 후 follow-up" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update single-source 다시 불러오기 후 두 번째 follow-up" --reporter=line`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2289,2410p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3567,3665p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5331,5405p'`
- `nl -ba README.md | sed -n '138,146p;170,170p'`
- `nl -ba docs/MILESTONES.md | sed -n '56,64p;88,88p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1347,1355p;1379,1379p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '45,53p;77,77p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2705,2825p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3665,3715p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2482,2490p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5379,5390p'`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- history-card latest-update news-only click-reload family의 title 4개(`e2e/tests/web-smoke.spec.mjs:2397`, `e2e/tests/web-smoke.spec.mjs:2705`, `e2e/tests/web-smoke.spec.mjs:3567`, `e2e/tests/web-smoke.spec.mjs:5331`)는 아직 generic wording입니다. 다음 라운드에서 `hankyung.com`, `mk.co.kr`, `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사`를 title에 직접 반영하는 편이 가장 작은 same-family current-risk reduction입니다.
- latest-update natural-reload family, zero-strong-slot family, crimson/noisy-source family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
