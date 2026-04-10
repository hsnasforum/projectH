# history-card entity-card click-reload actual-search follow-up browser-anchor source-path-exact-field truth-sync clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-follow-up-browser-anchor-source-path-exact-field-truth-sync-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card click-reload actual-search follow-up combined browser-anchor에서 post-follow-up `WEB` badge truth-sync와 title exact-field wording이 정리되었다고 보고했습니다. 이번 라운드에서는 그 change와 claimed rerun이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 actual-search initial click-reload anchor를 이미 닫았으므로, 이번 검증 후에는 same actual-search click-reload family에서 남은 다음 exact slice를 하나로 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:2828`은 `source path(namu.wiki, ko.wikipedia.org)`, `WEB badge`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`을 제목에 직접 드러내고 있습니다.
- follow-up click-reload actual-search body/docs truth도 current tree와 맞습니다. body `e2e/tests/web-smoke.spec.mjs:2929`, `e2e/tests/web-smoke.spec.mjs:2930`, `e2e/tests/web-smoke.spec.mjs:2933`, `e2e/tests/web-smoke.spec.mjs:2935`, `e2e/tests/web-smoke.spec.mjs:2937`, `e2e/tests/web-smoke.spec.mjs:2938`은 `README.md:161`, `docs/MILESTONES.md:81`, `docs/ACCEPTANCE_CRITERIA.md:1372`, `docs/TASK_BACKLOG.md:70`과 정렬돼 있습니다.
- rerun 결과도 `/work`의 pass claim과 맞았습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search" --reporter=line`은 `1 passed (8.1s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다. 검증 시점의 `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty였습니다.
- 다음 Claude 슬라이스는 `history-card entity-card click-reload actual-search second-follow-up browser-anchor source-path-exact-field truth-sync clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:2949` second-follow-up title은 아직 generic wording이고, docs `README.md:162`, `docs/MILESTONES.md:82`, `docs/ACCEPTANCE_CRITERIA.md:1373`, `docs/TASK_BACKLOG.md:71`는 second-follow-up 뒤 `WEB` badge까지 drift prevention을 말하지만 current body는 initial/first-follow-up에서만 `e2e/tests/web-smoke.spec.mjs:3028`, `e2e/tests/web-smoke.spec.mjs:3029`, `e2e/tests/web-smoke.spec.mjs:3043`으로 `originBadge`를 확인하고, second-follow-up 뒤에는 `e2e/tests/web-smoke.spec.mjs:3058`, `e2e/tests/web-smoke.spec.mjs:3059`, `e2e/tests/web-smoke.spec.mjs:3064`, `e2e/tests/web-smoke.spec.mjs:3066`, `e2e/tests/web-smoke.spec.mjs:3067`만 직접 확인합니다. 다음 slice는 이 exact-field gap을 먼저 truth-sync한 뒤 제목 wording을 맞추는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' work/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-follow-up-browser-anchor-source-path-exact-field-truth-sync-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-entity-card-click-reload-actual-search-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,280p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2828,3071p'`
- `nl -ba README.md | sed -n '161,162p'`
- `nl -ba docs/MILESTONES.md | sed -n '81,82p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1372,1373p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '70,71p'`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor truth-sync verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- actual-search second-follow-up title `e2e/tests/web-smoke.spec.mjs:2949`는 아직 generic wording이고, post-second-follow-up `originBadge`를 직접 다시 확인하지 않습니다. 다음 라운드에서는 same-family flow order에 맞춰 second-follow-up truth-sync를 닫는 편이 가장 작은 adjacent current-risk reduction입니다.
- latest-update, zero-strong-slot, crimson family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
