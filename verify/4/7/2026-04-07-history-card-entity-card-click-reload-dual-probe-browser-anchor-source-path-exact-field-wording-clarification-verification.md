# history-card entity-card click-reload dual-probe browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-click-reload-dual-probe-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card click-reload dual-probe initial combined browser-anchor title이 source-path plurality와 exact response-origin field를 제목에서 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 wording change와 claimed rerun이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 natural-reload dual-probe family를 이미 닫았으므로, 이번 검증 후에는 같은 click-reload dual-probe family에서 남은 다음 exact slice를 하나로 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:1959`는 `source path(pearlabyss.com/200, pearlabyss.com/300)`, `WEB badge`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반 · 백과 기반`을 제목에 직접 드러내고 있습니다.
- initial click-reload dual-probe body/docs truth도 current tree와 맞습니다. body `e2e/tests/web-smoke.spec.mjs:2058`, `e2e/tests/web-smoke.spec.mjs:2059`, `e2e/tests/web-smoke.spec.mjs:2064`, `e2e/tests/web-smoke.spec.mjs:2066`, `e2e/tests/web-smoke.spec.mjs:2067`, `e2e/tests/web-smoke.spec.mjs:2068`은 `README.md:135`, `docs/MILESTONES.md:53`, `docs/ACCEPTANCE_CRITERIA.md:1344`, `docs/TASK_BACKLOG.md:42`와 정렬돼 있습니다.
- rerun 결과도 `/work`의 pass claim과 맞았습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe" --reporter=line`은 `1 passed (7.6s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다. 검증 시점의 `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty였습니다.
- 다음 Claude 슬라이스는 `history-card entity-card click-reload dual-probe follow-up browser-anchor source-path-exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:3140` follow-up title은 아직 generic wording이지만, same body `e2e/tests/web-smoke.spec.mjs:3251`, `e2e/tests/web-smoke.spec.mjs:3252`, `e2e/tests/web-smoke.spec.mjs:3257`, `e2e/tests/web-smoke.spec.mjs:3259`, `e2e/tests/web-smoke.spec.mjs:3260`, `e2e/tests/web-smoke.spec.mjs:3261`와 docs `README.md:143`, `docs/MILESTONES.md:61`, `docs/ACCEPTANCE_CRITERIA.md:1352`, `docs/TASK_BACKLOG.md:50`는 exact source-path + exact-field truth를 이미 직접 가리킵니다.

## 검증
- `sed -n '1,220p' work/4/7/2026-04-07-history-card-entity-card-click-reload-dual-probe-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,220p' verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-second-follow-up-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1954,2072p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3070,3264p'`
- `nl -ba README.md | sed -n '135,164p'`
- `nl -ba docs/MILESTONES.md | sed -n '53,84p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1344,1375p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '42,73p'`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- history-card dual-probe click-reload follow-up title `e2e/tests/web-smoke.spec.mjs:3140`과 second-follow-up title `e2e/tests/web-smoke.spec.mjs:3072`는 아직 generic wording입니다. 다음 라운드에서는 same-family flow order에 맞춰 follow-up title부터 닫는 편이 가장 작은 adjacent current-risk reduction입니다.
- latest-update, zero-strong-slot, actual-search family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
