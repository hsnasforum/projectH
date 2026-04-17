# 2026-04-17 sqlite-browser-history-card-natural-reload-core-parity

## 변경 파일

- 없음 (제품 코드, sqlite Playwright config, test body 모두 무변경. 문서 4종 `README.md` / `docs/ACCEPTANCE_CRITERIA.md` / `docs/MILESTONES.md` / `docs/TASK_BACKLOG.md`는 이번 라운드 시작 시점부터 이미 dirty worktree에 자연어 reload reload-only 10건(70~79) 반영분이 staged-uncommitted 상태로 들어와 있었고, handoff dirty-worktree 지침("Work with the current tree as-is. Do not revert unrelated hunks.")에 따라 그대로 유지함.)

## 사용 skill

- work-log-closeout

## 변경 이유

직전 라운드(`/work` + `/verify` `2026-04-17-sqlite-browser-history-card-click-reload-second-followup-parity*`)가 sqlite browser gate를 click-reload 두 번째 follow-up까지 닫은 뒤, 같은 history-card family의 남은 current-risk는 `방금 검색한 결과 다시 보여줘` 자연어 reload reload-only 경로에서 answer-mode continuity, source-path/provenance retention, noisy-source exclusion, empty-meta no-leak이 sqlite backend와 JSON-default 사이에서 drift하지 않는지였습니다. handoff seq 246은 이 natural-reload reload-only core bundle 10건(entity-card zero-strong-slot / 붉은사막 noisy exclusion / 붉은사막 source path / dual-probe source path / dual-probe response-origin / latest-update mixed·single·news-only / latest-update noisy community / store-seeded empty-meta no-leak)을 한 번에 같은 sqlite Playwright config로 닫으라고 지정했고, 10개 시나리오는 모두 `e2e/tests/web-smoke.spec.mjs`에 이미 존재하므로 이번 라운드는 sqlite backend 실측 + 4개 inventory 문서 truth-sync(69 → 79)만 수행했습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인** (테스트 본문, sqlite config, 제품 코드 모두 무변경):
   - `history-card latest-update 자연어 reload noisy community 보조 커뮤니티 brunch 미노출 기사 교차 확인 보조 기사 hankyung mk 유지됩니다`
   - `history-card entity-card store-seeded actual-search 자연어 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다`
   - `entity-card zero-strong-slot 방금 검색한 결과 다시 보여줘 자연어 reload에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 유지됩니다`
   - `entity-card 붉은사막 검색 결과 자연어 reload에서 WEB badge, 설명 카드, noisy single-source claim(출시일/2025/blog.example.com) 미노출, 설명형 다중 출처 합의, 백과 기반 유지, namu.wiki/ko.wikipedia.org/blog.example.com provenance 유지됩니다`
   - `entity-card 붉은사막 자연어 reload에서 source path(namu.wiki, ko.wikipedia.org, blog.example.com provenance)가 context box에 유지됩니다`
   - `entity-card dual-probe 자연어 reload에서 source path(pearlabyss.com/200, pearlabyss.com/300)가 context box에 유지됩니다`
   - `entity-card dual-probe 자연어 reload에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다`
   - `latest-update mixed-source 자연어 reload에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
   - `latest-update single-source 자연어 reload에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다`
   - `latest-update news-only 자연어 reload에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다`

2. **docs truth-sync 상태 확인 (이번 라운드 제로-편집)**: 라운드 시작 시점부터 `README.md` sqlite browser gate 번호 목록에는 70~79번으로 자연어 reload reload-only 10건이, `docs/ACCEPTANCE_CRITERIA.md` sqlite backend gate scenarios block(1550~1559)에는 같은 10건 short-hand 라인이, `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 sqlite browser baseline 문장 끝에는 `history-card natural-reload reload-only contract` 항목이 click-reload second-follow-up contract 다음 단계로 이미 추가되어 있었고, 현재 worktree 기준으로 inventory가 69 → 79로 정확히 확장됩니다. 이번 라운드 추가 문서 편집 없이 `git diff --check`만 재확인했고 whitespace 문제 없음.

3. **제품 코드 / sqlite config / 테스트 본문 무변경**: history-card 렌더링 semantics, 저장 record shape, answer-mode composition, source-role policy, sqlite Playwright config(`e2e/playwright.sqlite.config.mjs`), `e2e/tests/web-smoke.spec.mjs` 모두 손대지 않았고, JSON-default Playwright path에도 영향 없음. click-reload second-follow-up sqlite gate truth는 그대로 유지됨.

## 검증

10개 exact scenario를 각각 `-g "<exact title>"`로 sqlite Playwright config에서 실행 (broader regex로 대체하지 않음, regex 특수문자는 백슬래시로 escape):

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update 자연어 reload noisy community 보조 커뮤니티 brunch 미노출 기사 교차 확인 보조 기사 hankyung mk 유지됩니다" --reporter=line  # 1 passed (4.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card store-seeded actual-search 자연어 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card zero-strong-slot 방금 검색한 결과 다시 보여줘 자연어 reload에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\.wiki/ko\.wikipedia\.org가 유지됩니다" --reporter=line  # 1 passed (4.5s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload에서 WEB badge, 설명 카드, noisy single-source claim\(출시일/2025/blog\.example\.com\) 미노출, 설명형 다중 출처 합의, 백과 기반 유지, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance 유지됩니다" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 자연어 reload에서 source path\(namu\.wiki, ko\.wikipedia\.org, blog\.example\.com provenance\)가 context box에 유지됩니다" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card dual-probe 자연어 reload에서 source path\(pearlabyss\.com/200, pearlabyss\.com/300\)가 context box에 유지됩니다" --reporter=line  # 1 passed (4.6s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card dual-probe 자연어 reload에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다" --reporter=line  # 1 passed (4.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update mixed-source 자연어 reload에서 source path\(store\.steampowered\.com, yna\.co\.kr\) \+ WEB badge, 최신 확인, 공식\+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다" --reporter=line  # 1 passed (5.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update single-source 자연어 reload에서 source path\(example\.com/seoul-weather\) \+ WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다" --reporter=line  # 1 passed (6.5s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update news-only 자연어 reload에서 기사 source path\(hankyung\.com, mk\.co\.kr\) \+ WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다" --reporter=line  # 1 passed (4.7s)
git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, JSON-default Playwright suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 sqlite Playwright config / 테스트 본문 / 제품 코드를 전혀 건드리지 않은 sqlite-only 실측 + 기 반영된 문서 truth-sync 검수 라운드였고, handoff가 요구한 10개 focused rerun(자연어 reload reload-only core)을 모두 개별 실행으로 통과시켰기 때문에 broad browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- sqlite browser gate는 이번 라운드로 총 79건까지 확장됐습니다. 같은 family의 추가 current-risk(자연어 reload follow-up / 두 번째 follow-up 체인, click-reload 후 plain composer follow-up, zero-strong-slot follow-up 분기, dual-probe 자연어 reload 후 두 번째 follow-up mixed count-summary meta 등)는 이번 슬라이스 scope 밖이라 sqlite backend로 아직 확인되지 않았습니다.
- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책은 이전 라운드와 동일합니다. sqlite/JSON Playwright config 동시 실행은 여전히 같은 `data/web-search/` 경로를 공유하므로 순차 실행 한정으로 안전합니다.
- 이번 라운드는 sqlite backend 실측만 했고 JSON-default path는 재실행하지 않았습니다. 자연어 reload reload-only family는 JSON-default smoke에서 이미 shipped 계약이라 회귀가 발생할 사유는 없지만, 다음 라운드 release-check가 필요한 경우 함께 재실행이 필요합니다.
- 문서 diff에는 이전 click-reload follow-up / second-follow-up 라운드에서 넘어온 48~69번 항목도 여전히 staged-uncommitted로 섞여 있습니다. 이번 `/work` scope가 아니라 commit/push 시 한꺼번에 정리될 예정이며, 이번 라운드는 dirty-worktree 지침에 따라 손대지 않았습니다.
