# history-card entity-card click-reload actual-search second-follow-up browser-anchor source-path-exact-field truth-sync clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-second-follow-up-browser-anchor-source-path-exact-field-truth-sync-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card click-reload actual-search second-follow-up combined browser-anchor에서 post-second-follow-up `WEB` badge truth-sync와 title exact-field wording이 정리되었다고 보고했습니다. 이번 라운드에서는 그 change와 claimed rerun이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 actual-search follow-up click-reload anchor를 이미 닫았으므로, 이번 검증 후에는 actual-search click-reload family가 실제로 닫혔는지 확인하고, 그 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:2950`에는 `source path(namu.wiki, ko.wikipedia.org)`, `WEB badge`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`을 직접 드러내는 second-follow-up title이 들어가 있고, `e2e/tests/web-smoke.spec.mjs:3063`에는 post-second-follow-up `await expect(originBadge).toHaveText("WEB")` 재확인이 실제로 반영돼 있었습니다.
- second-follow-up actual-search body/docs truth도 current tree와 맞았습니다. same scenario body는 `namu.wiki`, `ko.wikipedia.org`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` continuity를 유지하고 있고, docs `README.md:162`, `docs/MILESTONES.md:82`, `docs/ACCEPTANCE_CRITERIA.md:1373`, `docs/TASK_BACKLOG.md:71`도 같은 exact-field truth를 직접 말합니다.
- rerun 결과도 `/work`의 pass claim과 방향이 맞았습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search" --reporter=line`은 current tree에서 `1 passed (7.7s)`였고, `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- click-reload actual-search wording/truth-sync family는 이번 라운드 기준으로 닫혔습니다. initial `e2e/tests/web-smoke.spec.mjs:1849`, follow-up `e2e/tests/web-smoke.spec.mjs:2828`, second-follow-up `e2e/tests/web-smoke.spec.mjs:2950`이 모두 source-path exact-field truth와 정렬됐습니다.
- 다음 Claude 슬라이스는 `history-card latest-update click-reload mixed-source browser-anchor source-path-exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:2079`, `e2e/tests/web-smoke.spec.mjs:3274`, `e2e/tests/web-smoke.spec.mjs:3398`의 mixed-source click-reload title 3개가 아직 generic wording이고, same bodies는 이미 `e2e/tests/web-smoke.spec.mjs:2166`, `e2e/tests/web-smoke.spec.mjs:2170`, `e2e/tests/web-smoke.spec.mjs:2171`, `e2e/tests/web-smoke.spec.mjs:2176`, `e2e/tests/web-smoke.spec.mjs:2178`, `e2e/tests/web-smoke.spec.mjs:2179`, `e2e/tests/web-smoke.spec.mjs:2180`, `e2e/tests/web-smoke.spec.mjs:3361`, `e2e/tests/web-smoke.spec.mjs:3377`, `e2e/tests/web-smoke.spec.mjs:3378`, `e2e/tests/web-smoke.spec.mjs:3383`, `e2e/tests/web-smoke.spec.mjs:3385`, `e2e/tests/web-smoke.spec.mjs:3386`, `e2e/tests/web-smoke.spec.mjs:3387`, `e2e/tests/web-smoke.spec.mjs:3446`, `e2e/tests/web-smoke.spec.mjs:3450`, `e2e/tests/web-smoke.spec.mjs:3452`, `e2e/tests/web-smoke.spec.mjs:3453`, `e2e/tests/web-smoke.spec.mjs:3454`, `e2e/tests/web-smoke.spec.mjs:3457`, `e2e/tests/web-smoke.spec.mjs:3458`에서 exact source path + exact-field continuity를 직접 검증합니다. docs `README.md:136`, `README.md:144`, `README.md:168`, `docs/MILESTONES.md:54`, `docs/MILESTONES.md:62`, `docs/MILESTONES.md:86`, `docs/ACCEPTANCE_CRITERIA.md:1345`, `docs/ACCEPTANCE_CRITERIA.md:1353`, `docs/ACCEPTANCE_CRITERIA.md:1377`, `docs/TASK_BACKLOG.md:43`, `docs/TASK_BACKLOG.md:51`, `docs/TASK_BACKLOG.md:75`도 이미 exact wording target을 고정하고 있으므로, 다음 라운드는 title wording 3건만 정리하는 것이 가장 작은 coherent slice입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' work/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-second-follow-up-browser-anchor-source-path-exact-field-truth-sync-clarification.md`
- `sed -n '1,220p' verify/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-follow-up-browser-anchor-source-path-exact-field-truth-sync-clarification-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2079,2181p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3274,3415p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3398,3495p'`
- `nl -ba README.md | sed -n '136,142p'`
- `nl -ba docs/MILESTONES.md | sed -n '54,62p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1345,1353p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '43,51p'`
- `rg -n "mixed-source.*follow-up|mixed-source.*두 번째 follow-up|mixed-source.*second-follow-up" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `rg -n "history-card latest-update mixed-source 다시 불러오기 후 follow-up 질문에서 source path|history-card latest-update mixed-source 다시 불러오기 후 두 번째 follow-up 질문에서 source path" e2e/tests/web-smoke.spec.mjs`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor truth-sync verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- history-card latest-update mixed-source click-reload family의 title 3개(`e2e/tests/web-smoke.spec.mjs:2079`, `e2e/tests/web-smoke.spec.mjs:3274`, `e2e/tests/web-smoke.spec.mjs:3398`)는 아직 generic wording입니다. body와 docs가 이미 exact truth를 말하므로 다음 라운드에서 wording만 정리하는 것이 가장 자연스럽습니다.
- latest-update single-source, latest-update news-only, zero-strong-slot, crimson family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
