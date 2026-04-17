## 변경 파일
- `verify/4/17/2026-04-17-sqlite-browser-history-card-actual-search-strong-plus-missing-exact-title-parity-verification.md`
- `.pipeline/operator_request.md`

## 사용 skill
- round-handoff

## 변경 이유
- 이번 라운드는 지시된 `/work`인 `work/4/17/2026-04-17-sqlite-browser-history-card-actual-search-strong-plus-missing-exact-title-parity.md`의 핵심 주장, 즉 sqlite exact-title 7개 재실행 통과와 docs 무변경 정합성이 현재 트리에서도 유지되는지 다시 확인하기 위한 verification round입니다.
- 시작 시점의 최신 `/verify`는 `verify/4/17/2026-04-17-sqlite-browser-history-card-click-reload-composer-followup-parity-verification.md`였고, 같은 날 같은 family에는 더 늦은 `/work`인 `work/4/17/2026-04-17-sqlite-browser-history-card-noisy-single-source-strong-plus-missing-click-reload-exact-title-parity.md`도 이미 존재했습니다. 따라서 이번 `/verify`는 지정된 `/work`의 truth는 닫되, 다음 control은 별도 truth-sync blocker를 분리해서 기록해야 합니다.

## 핵심 변경
- 지정된 `/work`의 핵심 주장은 현재 트리 기준으로 맞았습니다. `e2e/tests/web-smoke.spec.mjs`의 actual-search click-reload 3건(`:4016`, `:6059`, `:6191`)과 자연어 reload 4건(`:8357`, `:9098`, `:9228`, `:9313`)을 sqlite config로 다시 실행한 결과 모두 `1 passed`로 통과했습니다.
- docs 무변경 정합성 주장도 맞았습니다. `README.md`의 sqlite gate 항목 `#42`, `#53`, `#62`, `#74`, `#89`, `#90`, `#91`, `docs/ACCEPTANCE_CRITERIA.md`의 sqlite backend 항목 `1522`, `1533`, `1542`, `1554`, `1569`-`1571`, `docs/MILESTONES.md`의 actual-search strong-plus-missing bundle(`131`-`136`), `docs/TASK_BACKLOG.md`의 sqlite browser parity summary(`822`)가 이번 7-title 번들과 모순되지 않았습니다.
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 출력 없이 종료돼 clean 상태였습니다. 이번 `/work`가 적은 "코드/문서 무변경, 실측만 수행" 서술과 현재 dirty tree의 affected 범위 설명도 일치합니다.
- 다만 이 `/work`가 현재 시점의 최신 same-family `/work`는 아닙니다. `stat` 결과 기준으로 actual-search `/work`는 `2026-04-17 14:06:46 +0900`, noisy-single-source click-reload `/work`는 `2026-04-17 14:49:27 +0900`, prompt가 지정한 기존 `/verify`는 `2026-04-17 14:58:55 +0900`입니다. 그래서 다음 control은 새 Claude implement handoff가 아니라, 더 늦은 `/work`를 먼저 verify해야 한다는 truth-sync stop으로 닫는 편이 맞습니다.

## 검증
- `rg -n "history-card entity-card 다시 불러오기 후 actual-search source path|follow-up 질문에서 actual-search source path|두 번째 follow-up 질문에서 actual-search source path|entity-card 붉은사막 자연어 reload에서 source path|entity-card 붉은사막 actual-search 자연어 reload 후" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `nl -ba README.md | sed -n '312,366p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1518,1574p'`
- `nl -ba docs/MILESTONES.md | sed -n '104,146p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '792,832p'`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 actual-search source path\\(namu.wiki, ko.wikipedia.org\\) \\+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다" --reporter=line` -> `1 passed (3.5s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path\\(namu.wiki, ko.wikipedia.org\\) \\+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다" --reporter=line` -> `1 passed (3.6s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path\\(namu.wiki, ko.wikipedia.org\\) \\+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다" --reporter=line` -> `1 passed (5.1s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 자연어 reload에서 source path\\(namu.wiki, ko.wikipedia.org, blog.example.com provenance\\)가 context box에 유지됩니다" --reporter=line` -> `1 passed (5.0s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path\\(namu.wiki, ko.wikipedia.org\\)가 context box에 유지됩니다" --reporter=line` -> `1 passed (4.2s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다" --reporter=line` -> `1 passed (4.3s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up에서 source path\\(namu.wiki, ko.wikipedia.org\\)가 context box에 유지되고 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다" --reporter=line` -> `1 passed (4.4s)`
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `stat -c '%y %n' work/4/17/2026-04-17-sqlite-browser-history-card-actual-search-strong-plus-missing-exact-title-parity.md verify/4/17/2026-04-17-sqlite-browser-history-card-click-reload-composer-followup-parity-verification.md work/4/17/2026-04-17-sqlite-browser-history-card-noisy-single-source-strong-plus-missing-click-reload-exact-title-parity.md`

## 남은 리스크
- 지정된 actual-search `/work` 자체는 truthful하지만, 같은 날 더 늦은 same-family `/work`가 아직 `/verify`로 닫히지 않았습니다. 따라서 seq 258은 새 Claude implement handoff나 Gemini arbitration이 아니라, `work/4/17/2026-04-17-sqlite-browser-history-card-noisy-single-source-strong-plus-missing-click-reload-exact-title-parity.md`를 먼저 verify해야 한다는 truth-sync stop으로 남겨야 합니다.
- 이번 라운드는 제품 코드와 Playwright 본문을 바꾸지 않았으므로 JSON-default rerun, full sqlite suite, `make e2e-test`, `python3 -m unittest -v tests.test_web_app`은 실행하지 않았습니다. 범위는 actual-search strong-plus-missing 7-title sqlite continuity 재검증과 문서 정합성 대조에 한정했습니다.
- Playwright `-g`는 regex 해석을 사용하므로 `(`, `)`, `+`, `.`가 들어간 exact title은 계속 escape된 패턴으로 실행해야 합니다. 다음 noisy-single-source verify round도 같은 원칙을 유지하는 편이 맞습니다.
