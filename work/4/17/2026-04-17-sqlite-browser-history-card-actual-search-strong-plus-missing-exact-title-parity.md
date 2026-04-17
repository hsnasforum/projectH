# 2026-04-17 sqlite-browser-history-card-actual-search-strong-plus-missing-exact-title-parity

## 변경 파일

- 없음 (코드/문서 무변경, sqlite Playwright 7개 실측만 수행)

## 사용 skill

- work-log-closeout

## 변경 이유

seq 252는 현재 `e2e/tests/web-smoke.spec.mjs`에 실제로 존재하지 않는 여섯 개의 count-summary 요약 bullet을 마치 exact `test("...")` title인 것처럼 쓴 synthetic 문구를 만들어 block된 슬라이스였습니다. handoff seq 253은 같은 family의 남은 current-risk(= sqlite actual-search strong-plus-missing continuity across click reload + natural reload)를, 현재 트리에 실제로 존재하는 일곱 개의 exact Playwright title로만 고정해서 sqlite backend에서도 동일하게 통과하는지를 재확인하도록 지정했습니다. 이번 라운드는 제품 코드, Playwright 본문, sqlite config, `app/static/app.js` 모두 무변경으로 일곱 개 sqlite 시나리오를 개별 실행해 현재 트리에서 이미 통과함을 확인했습니다. docs 쪽은 handoff가 명시한 대로 "old 105 → 111 wording을 강제하지 말고 현재 tree 번호/문구를 그대로 쓴다", "sqlite actual-search block만 affected 범위다", "unrelated dirty hunk는 건드리지 않는다" 규칙을 따라 별도 수정이 필요 없음을 확인했습니다. 일곱 개 actual-search exact title은 이미 `README.md` sqlite gate 목록의 #42, #53, #62, #74, #89, #90, #91 자리에 기존 dirty 확장 안에서 truthfully 나열되어 있어, 추가 doc 편집 없이 verified 7-title 번들과 그대로 정합합니다.

## 핵심 변경

1. **sqlite Playwright 7개 exact-title 실측 통과 확인** (제품 코드, Playwright 본문, sqlite config, `app/static/app.js` 모두 무변경):
   - `history-card entity-card 다시 불러오기 후 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:4016`) → 1 passed (3.7s)
   - `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:6059`) → 1 passed (3.7s)
   - `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:6191`) → 1 passed (4.3s)
   - `entity-card 붉은사막 자연어 reload에서 source path(namu.wiki, ko.wikipedia.org, blog.example.com provenance)가 context box에 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:8357`) → 1 passed (3.5s)
   - `entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지됩니다` (`e2e/tests/web-smoke.spec.mjs:9098`) → 1 passed (4.1s)
   - `entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다` (`e2e/tests/web-smoke.spec.mjs:9228`) → 1 passed (4.1s)
   - `entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지되고 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다` (`e2e/tests/web-smoke.spec.mjs:9313`) → 1 passed (4.3s)

2. **docs 교정 없음 — current dirty tree가 이미 7-title 번들과 정합함**:
   - `README.md` sqlite gate 목록의 #42 (click reload actual-search source path, `e2e/tests/web-smoke.spec.mjs:4016`와 일치), #53 (follow-up actual-search source path, `:6059`), #62 (두 번째 follow-up actual-search source path, `:6191`), #74 (붉은사막 자연어 reload source path/provenance, `:8357`), #89 (붉은사막 actual-search 자연어 reload 후 follow-up source path, `:9098`), #90 (같은 reload 후 follow-up WEB drift, `:9228`), #91 (같은 reload 후 두 번째 follow-up source+WEB, `:9313`) 모두 현재 dirty 확장 안에 그대로 들어 있고 실측 Playwright title과 character-exact로 일치합니다.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite backend gate scenarios 블록에는 이번에 실측한 일곱 계약이 각각 short-hand 라인으로 이미 등록돼 있어(actual-search source path retention, 붉은사막 자연어 reload provenance retention, 자연어 reload follow-up/두 번째 follow-up source+WEB retention 등) 추가 편집 없이 실측 결과와 정합합니다.
   - `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 sqlite browser baseline 문장은 이미 "history-card click-reload first-follow-up contract", "second-follow-up contract", "natural-reload reload-only contract", "natural-reload follow-up / second-follow-up chain contract" 형태로 상위 계약 번들을 포함하고 있고, 이번 일곱 exact title이 그 상위 계약의 실 증거 하위 집합입니다. handoff가 명시한 "Do not force the old 105 → 111 wording" 규칙에 따라 강제 재번호/수식어 이동은 하지 않았습니다.

3. **Scope 준수**:
   - `app/static/app.js`의 pre-existing sendRequest promise-queue dirty hunk (seq 250 수정본), `core/agent_loop.py`, `storage/*`, `controller/*`, `pipeline_runtime/*`, `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`는 이번 라운드에 건드리지 않았습니다.
   - handoff가 명시한 "Leave unrelated dirty hunks alone"에 따라 `README.md`/`docs/ACCEPTANCE_CRITERIA.md`/`docs/MILESTONES.md`/`docs/TASK_BACKLOG.md`의 non-actual-search 확장 부분 (예: noisy community, dual-probe, latest-update mixed-source/single-source/news-only 등)은 이번 라운드 범위가 아니라 그대로 유지했습니다.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 actual-search source path\(namu.wiki, ko.wikipedia.org\) \+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다" --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path\(namu.wiki, ko.wikipedia.org\) \+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다" --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path\(namu.wiki, ko.wikipedia.org\) \+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다" --reporter=line  # 1 passed (4.3s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 자연어 reload에서 source path\(namu.wiki, ko.wikipedia.org, blog.example.com provenance\)가 context box에 유지됩니다" --reporter=line  # 1 passed (3.5s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path\(namu.wiki, ko.wikipedia.org\)가 context box에 유지됩니다" --reporter=line  # 1 passed (4.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다" --reporter=line  # 1 passed (4.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up에서 source path\(namu.wiki, ko.wikipedia.org\)가 context box에 유지되고 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다" --reporter=line  # 1 passed (4.3s)
git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean (exit 0)
```

- handoff가 "code changes 발생 시에만 JSON-default 재실행"을 요구하는데, 이번 라운드는 제품 코드/Playwright 본문/sqlite config/`app/static/app.js` 모두 무변경이라 JSON-default Playwright 재실행은 건너뛰었습니다. 같은 일곱 title은 JSON-default smoke에서 이미 shipped 계약이라 이번 라운드에 회귀 유발 사유가 없습니다.
- `make e2e-test`, sqlite/JSON browser full suite, `python3 -m unittest -v tests.test_web_app`은 이번 bounded scope(동일 family 내 sqlite actual-search 7개 exact title 재확인)에 대비해 과해 실행하지 않았습니다. 각 시나리오 독립 rerun이 모두 한 번에 통과했고, shared helper나 product code diff가 없었습니다.
- 초회 `-g`에 unescaped `+`를 쓰면 Playwright regex quantifier로 해석돼 "No tests found"가 떴습니다. `\(`, `\)`, `\+`로 escape 한 뒤 일곱 개 모두 정상 매치/통과했습니다. 실제 test title 자체는 변경하지 않았습니다.

## 남은 리스크

- 이번 라운드에서 sqlite actual-search 7-title 번들은 통과가 확인됐지만, handoff가 명시한 "docs-only round 금지" 조건을 따라 dirty 확장 자체의 broader sqlite runtime 실측은 수행하지 않았습니다. `README.md` 목록 #48 이후 비-actual-search 행 (noisy community, dual-probe, latest-update mixed-source/single-source/news-only, zero-strong-slot 등) 중 sqlite에서 아직 실측으로 잠기지 않은 계약이 있는지는 별도 슬라이스에서 Codex가 우선순위를 결정할 대상입니다.
- seq 252의 synthetic six-bullet wording은 그 자체로는 현재 tree에 남아 있지 않지만, 과거 docs-only 라운드에서 "105 → 111" 같은 counted-expansion 가정이 재등장하지 않도록 다음 슬라이스도 exact Playwright title 단위로 묶어 실측해야 합니다.
- seq 250의 `sendRequest` promise-queue 변경, seq 248의 `_reuse_web_search_record` prepend 변경, seq 251/252의 click-reload composer plain follow-up 기록은 이전 라운드 그대로 유지되며 이번 라운드에 다시 열지 않았습니다. 이번 sqlite 실측 일곱 건 모두 해당 수정본 위에서 통과했습니다.
- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책은 이전 라운드와 동일합니다. sqlite/JSON Playwright config를 동시에 돌리지 않고 순차 실행했기 때문에 `data/web-search/` 공유 경로로 인한 cross-test 간섭은 없었습니다.
- 이번 라운드는 sqlite 실측만 했고 JSON-default 재실행은 생략했으므로, 다음 release-check에서 필요하다면 같은 일곱 title을 JSON-default config로도 한 번 더 돌려 회귀 없음을 재확인해야 합니다.
