# 2026-04-17 sqlite-browser-history-card-click-reload-followup-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- work-log-closeout

## 변경 이유

이전 `/work`(`2026-04-17-sqlite-browser-history-card-reload-core-parity.md`) + `/verify`가 sqlite browser gate를 reload-only / click-reload core 단계까지 닫았고, 같은 family의 남은 current-risk는 click-reload 직후 첫 follow-up 질문에서 origin badge, 설명 카드/최신 확인 라벨, 출처 합의 라벨, source path/provenance, noisy-source 미노출, store-seeded empty-meta no-leak이 sqlite backend에서도 JSON-default와 동일하게 유지되는지였습니다. handoff seq 244는 이 first-follow-up 12개 시나리오를 같은 sqlite Playwright config로 재실행하라고 지정했습니다. 12개 시나리오는 모두 spec에 이미 존재하므로 이번 라운드는 `e2e/playwright.sqlite.config.mjs` 또는 `e2e/tests/web-smoke.spec.mjs` 본문은 손대지 않고 sqlite backend 실측 + 4개 inventory 문서 sync만 진행했습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인** (테스트 본문, sqlite config, 제품 코드 모두 무변경):
   - `history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다`
   - `history-card latest-update 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 drift하지 않습니다`
   - `history-card latest-update noisy community source가 다시 불러오기 후 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`
   - `history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`
   - `history-card entity-card store-seeded actual-search 다시 불러오기 후 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다`
   - `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다`
   - `history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다`
   - `history-card latest-update mixed-source 다시 불러오기 후 follow-up 질문에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
   - `history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 drift하지 않습니다`
   - `history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 drift하지 않습니다`
   - `history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다`
   - `history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다`

2. **docs sync**: sqlite browser gate inventory 4개 문서에 first-follow-up 12건을 추가해 총 47 → 59건으로 맞춤. `README.md`는 번호 목록 48~59에 12개 시나리오 full title을 그대로 추가, `docs/ACCEPTANCE_CRITERIA.md`는 sqlite backend gate scenarios 목록 끝에 12개 short-hand 라인 추가, `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 sqlite browser baseline 문장에는 "history-card click-reload first-follow-up contract" 항목을 reload-only contract 뒤에 명시.

3. **제품 코드 / sqlite config / 테스트 본문 무변경**: history-card 렌더링 semantics, 저장 record shape, answer-mode composition, source-role policy, sqlite Playwright config(`e2e/playwright.sqlite.config.mjs`), `e2e/tests/web-smoke.spec.mjs` 모두 손대지 않았고, JSON-default Playwright path에도 영향 없음.

## 검증

12개 exact scenario를 각각 `-g "<exact title>"`로 sqlite Playwright config에서 실행 (broader regex로 대체하지 않음, regex 특수문자는 백슬래시로 escape):

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다" --reporter=line  # 1 passed (4.6s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 공식\+기사 교차 확인, 보조 기사 · 공식 기반이 drift하지 않습니다" --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update noisy community source가 다시 불러오기 후 follow-up에서도 보조 커뮤니티/brunch 미노출 \+ 기사 교차 확인, 보조 기사, hankyung\.com · mk\.co\.kr 유지됩니다" --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 다시 불러오기 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card store-seeded actual-search 다시 불러오기 후 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다" --reporter=line  # 1 passed (4.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path\(namu\.wiki, ko\.wikipedia\.org\) \+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path\(pearlabyss\.com/200, pearlabyss\.com/300\) \+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다" --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update mixed-source 다시 불러오기 후 follow-up 질문에서 source path\(store\.steampowered\.com, yna\.co\.kr\) \+ WEB badge, 최신 확인, 공식\+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다" --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 drift하지 않습니다" --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 drift하지 않습니다" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 source path\(example\.com/seoul-weather\) \+ WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다" --reporter=line  # 1 passed (4.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 기사 source path\(hankyung\.com, mk\.co\.kr\) \+ WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다" --reporter=line  # 1 passed (4.0s)
git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, JSON-default Playwright suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 sqlite Playwright config / 테스트 본문 / 제품 코드를 전혀 건드리지 않은 sqlite-only 실측 + 문서 sync 라운드였고, handoff가 요구한 12개 focused rerun을 모두 개별 실행으로 통과시켰기 때문에 broad browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- sqlite browser gate는 이번 라운드로 총 59건까지 확장됐습니다. 같은 family의 추가 current-risk(두 번째 follow-up, zero-strong-slot follow-up, 자연어 reload, click-reload 후 plain composer follow-up, dual-probe mixed count-summary follow-up 등)는 이번 슬라이스 scope 밖이라 sqlite backend로 아직 확인되지 않았습니다.
- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책은 이전 라운드와 동일합니다. sqlite/JSON Playwright config 동시 실행은 여전히 같은 `data/web-search/` 경로를 공유하므로 순차 실행 한정으로 안전합니다.
- 이번 라운드는 sqlite backend 실측만 했고 JSON-default path는 재실행하지 않았습니다. 첫 follow-up family는 JSON-default smoke에서 이미 shipped 계약이라 회귀가 발생할 사유는 없지만, 다음 라운드 release-check가 필요한 경우 함께 재실행이 필요합니다.
