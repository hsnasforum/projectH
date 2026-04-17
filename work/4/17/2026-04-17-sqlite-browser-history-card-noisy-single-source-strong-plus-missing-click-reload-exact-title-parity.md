# 2026-04-17 sqlite-browser-history-card-noisy-single-source-strong-plus-missing-click-reload-exact-title-parity

## 변경 파일

- 없음 (코드/문서 무변경, sqlite Playwright 4개 exact-title 실측만 수행)

## 사용 skill

- work-log-closeout

## 변경 이유

seq 255 handoff는 직전 seq 254가 이미 닫힌 `sqlite-browser-history-card-actual-search-strong-plus-missing-exact-title-parity`를 재지시한 stale/`already_implemented` triage였기 때문에, 같은 family 안에서 아직 sqlite로 exact-title 단위 재확인이 이루어지지 않은 다음 current-risk, 즉 noisy single-source strong-plus-missing continuity across click reload (initial-render / reload-only / first follow-up / second follow-up) 4개 번들을 sqlite backend에서도 동일하게 통과하는지 잠그도록 지정했습니다. 이번 라운드는 `app/static/app.js`, `e2e/tests/web-smoke.spec.mjs`, sqlite config, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 어느 파일에도 편집 없이 4개 exact title을 개별 실행해 현재 트리에서 통과함을 확인했고, handoff가 "if the current dirty docs already match the verified four-title bundle, leave docs unchanged and say so in `/work`"라고 명시한 조건에 따라 docs는 손대지 않았습니다.

## 핵심 변경

1. **sqlite Playwright 4개 exact-title 실측 통과 확인** (제품 코드, Playwright 본문, sqlite config, `app/static/app.js` 모두 무변경):
   - `history-card entity-card noisy single-source initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:3542`) → 1 passed (5.0s)
   - `history-card entity-card 다시 불러오기 후 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:3654`) → 1 passed (4.8s)
   - `history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:10859`) → 1 passed (4.0s)
   - `history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:10962`) → 1 passed (4.7s)

2. **docs 교정 없음 — current dirty tree가 이미 4-title 번들과 정합함**:
   - `README.md` sqlite gate 목록의 #31 (noisy single-source initial-render strong-plus-missing count-summary meta, exact title #1), #41 (noisy single-source 다시 불러오기 reload-only 본문/origin detail 미노출 + provenance, exact title #2), #51 (noisy single-source 다시 불러오기 후 first follow-up 미노출 + provenance, exact title #3), #69 (noisy single-source 다시 불러오기 후 second follow-up 미노출 + provenance, exact title #4) 네 항목이 이미 character-exact Playwright title 그대로 dirty 확장 안에 들어 있습니다.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite backend gate 블록(lines 1511, 1521, 1531, 1549)에 이번 네 계약이 각각 short-hand 라인으로 이미 등록돼 있어(noisy single-source initial-render strong-plus-missing count-summary meta, 다시 불러오기 reload-only noisy single-source 미노출 + provenance, 다시 불러오기 후 first/second follow-up noisy single-source 미노출 + provenance) 추가 편집 없이 실측 결과와 정합합니다.
   - `docs/MILESTONES.md`(lines 65, 111, 137–139)와 `docs/TASK_BACKLOG.md`(items 28, 80, 81, 87, 113–115)에도 noisy single-source `다시 불러오기` initial-render / click-reload / follow-up / second-follow-up 계약이 이미 나열돼 있어, handoff가 명시한 "docs-only 라운드 금지" 및 "이미 정합하면 그대로 두기" 규칙에 따라 강제 편집하지 않았습니다.

3. **Scope 준수**:
   - `app/static/app.js`의 pre-existing sendRequest promise-queue dirty hunk (seq 250 수정본), `core/agent_loop.py`, `storage/*`, `controller/*`, `pipeline_runtime/*`, `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`는 이번 라운드에 건드리지 않았습니다.
   - handoff scope limits ("no docs-only round", "no new synthetic test titles", "no helper-wide refactor", "no natural-reload noisy bundle in the same round", "no controller/runtime/server/storage work")에 따라 natural-reload noisy follow-up, actual-search, dual-probe, latest-update mixed-source/single-source/news-only 등 unrelated sqlite 계약은 이번 라운드 범위가 아닙니다.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card noisy single-source initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다" --reporter=line  # 1 passed (5.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 noisy single-source claim\(출시일/2025/blog\.example\.com\)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (4.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 다시 불러오기 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (4.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 다시 불러오기 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (4.7s)
git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean (exit 0)
```

- handoff가 "if product code changes, rerun the matching JSON-default titles before closing docs"라고 요구하는데, 이번 라운드는 제품 코드/Playwright 본문/sqlite config/`app/static/app.js` 모두 무변경이라 JSON-default Playwright 재실행은 건너뛰었습니다. 네 exact title은 JSON-default smoke에서 이미 shipped 계약이라 이번 라운드에 회귀 유발 사유가 없습니다.
- `make e2e-test`, sqlite/JSON browser full suite, `python3 -m unittest -v tests.test_web_app`은 이번 bounded scope(동일 family 내 sqlite noisy single-source 4개 click-reload exact title 재확인)에 대비해 과해 실행하지 않았습니다. 각 시나리오 독립 rerun이 모두 한 번에 통과했고, shared helper나 product code diff가 없었습니다.
- handoff가 명시한 대로 `(`, `)`, `.`를 `\(`, `\)`, `\.`로 escape한 `-g` 패턴을 썼고, 실제 test title 자체는 변경하지 않았습니다.

## 남은 리스크

- seq 255는 seq 254가 이미 닫힌 actual-search exact-title parity 슬라이스를 재지시한 stale handoff였다는 점을 base로 "다음 same-family current-risk = noisy single-source click-reload 4-title parity"를 잠근 라운드입니다. 다음 슬라이스는 같은 family의 남은 current-risk(예: natural-reload noisy single-source reload-only/follow-up/second-follow-up parity, 또는 다른 quality axis)로 넘어가는 편이 맞습니다. 이번 라운드는 handoff scope limits에 따라 natural-reload noisy 번들은 열지 않았습니다.
- 이번 라운드에서 sqlite noisy single-source click-reload 4-title 번들은 통과가 확인됐지만, handoff가 명시한 "no docs-only round" 조건에 따라 나머지 sqlite 확장 목록(`README.md` #48 이후 일부 noisy community, dual-probe, latest-update mixed-source/single-source/news-only, zero-strong-slot 등) 중 sqlite에서 아직 실측으로 잠기지 않은 계약은 별도 슬라이스에서 Codex가 우선순위를 결정할 대상입니다.
- seq 250의 `sendRequest` promise-queue 변경, seq 248의 `_reuse_web_search_record` prepend 변경, 이전 라운드의 click-reload composer plain follow-up 기록은 이전 라운드 그대로 유지되며 이번 라운드에 다시 열지 않았습니다. 이번 sqlite 실측 네 건 모두 해당 수정본 위에서 통과했습니다.
- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책은 이전 라운드와 동일합니다. sqlite Playwright config만 순차 실행했고 JSON-default config와 섞어 돌리지 않았기 때문에 `data/web-search/` 공유 경로로 인한 cross-test 간섭은 없었습니다.
- 이번 라운드는 sqlite 실측만 했고 JSON-default 재실행은 생략했으므로, 다음 release-check에서 필요하다면 같은 네 exact title을 JSON-default config로도 한 번 더 돌려 회귀 없음을 재확인해야 합니다.
