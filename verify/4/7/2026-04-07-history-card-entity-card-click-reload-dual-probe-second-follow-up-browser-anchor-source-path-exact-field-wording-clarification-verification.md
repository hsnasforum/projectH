# history-card entity-card click-reload dual-probe second-follow-up browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-click-reload-dual-probe-second-follow-up-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card click-reload dual-probe second-follow-up combined browser-anchor title이 source-path plurality와 exact response-origin field를 제목에서 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 wording change와 claimed rerun이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 click-reload dual-probe follow-up anchor를 이미 닫았으므로, 이번 검증 후에는 dual-probe click-reload family가 실제로 모두 닫혔는지 확인하고 같은 history-card entity-card click-reload wording 축의 다음 exact slice를 하나로 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:3072`는 `source path(pearlabyss.com/200, pearlabyss.com/300)`, `WEB badge`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반 · 백과 기반`을 제목에 직접 드러내고 있습니다.
- second-follow-up click-reload dual-probe body/docs truth도 current tree와 맞습니다. body `e2e/tests/web-smoke.spec.mjs:3122`, `e2e/tests/web-smoke.spec.mjs:3126`, `e2e/tests/web-smoke.spec.mjs:3128`, `e2e/tests/web-smoke.spec.mjs:3129`, `e2e/tests/web-smoke.spec.mjs:3130`, `e2e/tests/web-smoke.spec.mjs:3134`, `e2e/tests/web-smoke.spec.mjs:3135`는 `README.md:163`, `docs/MILESTONES.md:83`, `docs/ACCEPTANCE_CRITERIA.md:1374`, `docs/TASK_BACKLOG.md:72`와 정렬돼 있습니다.
- rerun 결과도 `/work`의 pass claim과 맞았습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe" --reporter=line`은 `1 passed (7.6s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다. 검증 시점의 `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty였습니다.
- click-reload dual-probe browser-anchor wording family(initial, follow-up, second-follow-up)는 이번 라운드 기준으로 닫혔습니다. 다음 Claude 슬라이스는 `history-card entity-card click-reload actual-search browser-anchor source-path-exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:1849` initial actual-search title은 아직 generic wording이지만, same body `e2e/tests/web-smoke.spec.mjs:1939`, `e2e/tests/web-smoke.spec.mjs:1940`, `e2e/tests/web-smoke.spec.mjs:1945`, `e2e/tests/web-smoke.spec.mjs:1947`, `e2e/tests/web-smoke.spec.mjs:1948`와 docs `README.md:160`, `docs/MILESTONES.md:80`, `docs/ACCEPTANCE_CRITERIA.md:1371`, `docs/TASK_BACKLOG.md:69`는 exact source-path + exact-field truth를 이미 직접 가리킵니다.

## 검증
- `sed -n '1,220p' work/4/7/2026-04-07-history-card-entity-card-click-reload-dual-probe-second-follow-up-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,240p' verify/4/7/2026-04-07-history-card-entity-card-click-reload-dual-probe-follow-up-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1849,1958p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2828,3071p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3070,3138p'`
- `nl -ba README.md | sed -n '160,164p'`
- `nl -ba docs/MILESTONES.md | sed -n '80,84p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1375p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '69,73p'`
- `rg -n "test\\(\\\"history-card entity-card .*dual-probe|test\\(\\\"history-card entity-card .*actual-search|test\\(\\\"entity-card .*zero-strong-slot|test\\(\\\"entity-card .*crimson|test\\(\\\"history-card latest-update .*mixed-source|test\\(\\\"history-card latest-update .*single-source|test\\(\\\"history-card latest-update .*news-only" e2e/tests/web-smoke.spec.mjs`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- history-card entity-card click-reload actual-search titles `e2e/tests/web-smoke.spec.mjs:1849`, `e2e/tests/web-smoke.spec.mjs:2828`, `e2e/tests/web-smoke.spec.mjs:2949`는 아직 generic wording입니다. 다음 라운드에서는 same-family flow order에 맞춰 initial title `e2e/tests/web-smoke.spec.mjs:1849`부터 닫는 편이 가장 작은 adjacent current-risk reduction입니다.
- latest-update, zero-strong-slot, crimson family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
