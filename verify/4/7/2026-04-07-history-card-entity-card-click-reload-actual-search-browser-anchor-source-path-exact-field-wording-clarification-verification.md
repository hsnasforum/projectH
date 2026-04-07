# history-card entity-card click-reload actual-search browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card click-reload actual-search initial combined browser-anchor title이 source-path plurality와 exact response-origin field를 제목에서 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 wording change와 claimed rerun이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 dual-probe click-reload family를 이미 닫았으므로, 이번 검증 후에는 actual-search click-reload family에서 남은 가장 작은 next slice를 하나로 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:1849`는 `source path(namu.wiki, ko.wikipedia.org)`, `WEB badge`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`을 제목에 직접 드러내고 있습니다.
- initial click-reload actual-search body/docs truth도 current tree와 맞습니다. body `e2e/tests/web-smoke.spec.mjs:1939`, `e2e/tests/web-smoke.spec.mjs:1940`, `e2e/tests/web-smoke.spec.mjs:1945`, `e2e/tests/web-smoke.spec.mjs:1947`, `e2e/tests/web-smoke.spec.mjs:1948`은 `README.md:160`, `docs/MILESTONES.md:80`, `docs/ACCEPTANCE_CRITERIA.md:1371`, `docs/TASK_BACKLOG.md:69`와 정렬돼 있습니다.
- rerun 결과도 `/work`의 pass claim과 맞았습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 actual-search" --reporter=line`은 `1 passed (8.9s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다. 검증 시점의 `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty였습니다.
- 다음 Claude 슬라이스는 `history-card entity-card click-reload actual-search follow-up browser-anchor source-path-exact-field truth-sync clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:2828` follow-up title은 아직 generic wording이고, docs `README.md:161`, `docs/MILESTONES.md:81`, `docs/ACCEPTANCE_CRITERIA.md:1372`, `docs/TASK_BACKLOG.md:70`는 follow-up 뒤 `WEB` badge까지 drift prevention을 말하지만 current body는 follow-up 전 `e2e/tests/web-smoke.spec.mjs:2912`, `e2e/tests/web-smoke.spec.mjs:2913`만 `originBadge`를 확인하고, follow-up 뒤에는 `e2e/tests/web-smoke.spec.mjs:2929`, `e2e/tests/web-smoke.spec.mjs:2930`, `e2e/tests/web-smoke.spec.mjs:2935`, `e2e/tests/web-smoke.spec.mjs:2937`, `e2e/tests/web-smoke.spec.mjs:2938`만 직접 확인합니다. 다음 slice는 이 exact-field gap을 먼저 truth-sync한 뒤 제목 wording을 맞추는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' work/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,240p' verify/4/7/2026-04-07-history-card-entity-card-click-reload-dual-probe-second-follow-up-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1849,1958p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2828,3071p'`
- `nl -ba README.md | sed -n '160,162p'`
- `nl -ba docs/MILESTONES.md | sed -n '80,82p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1373p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '69,71p'`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 actual-search" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- actual-search follow-up title `e2e/tests/web-smoke.spec.mjs:2828`와 second-follow-up title `e2e/tests/web-smoke.spec.mjs:2949`는 아직 generic wording입니다. 특히 follow-up은 docs가 `WEB` badge drift prevention을 말하지만 post-follow-up `originBadge`를 직접 다시 확인하지 않아, 다음 라운드에서 follow-up truth-sync를 먼저 닫는 편이 맞습니다.
- latest-update, zero-strong-slot, crimson family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
