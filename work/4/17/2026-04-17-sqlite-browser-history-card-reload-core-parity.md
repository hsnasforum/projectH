# sqlite-browser-history-card-reload-core-parity

## 변경 파일

- `e2e/playwright.sqlite.config.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

이전 `/work`에서 sqlite browser gate가 총 37건까지 확장됐고, 최신 `/verify`는 자연어 reload / follow-up drift 체인으로 넘어가기 전에 닫을 남은 same-family current-risk가 shipped history-card click-reload / reload-only 계약 10건이라고 판단했습니다. 이 열 개 시나리오는 JSON-default Playwright path에서 이미 shipped된 사용자 가시 계약이고, sqlite backend에서도 동일하게 동작한다는 증거가 그동안 없었습니다. 실행 과정에서 첫 시나리오가 실패했는데, `playwright.sqlite.config.mjs`가 `LOCAL_AI_WEB_SEARCH_HISTORY_DIR`을 임시 디렉터리로 재지정하는 바람에 test가 미리 `data/web-search/{sessionId}/*.json`에 기록해 둔 record를 서버가 찾지 못했고 origin badge가 `SYSTEM`으로 떨어졌습니다. 이 config 격리가 reload 계열에 부족했기 때문에 notes dir와 같은 정책으로 web-search dir override도 제거해 repo 기본값(`data/web-search/`)으로 맞췄습니다. sqlite DB와 corrections dir 격리는 유지합니다.

## 핵심 변경

1. **`e2e/playwright.sqlite.config.mjs`**: `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` override 한 줄과 `webSearchDir` 변수 한 줄을 제거하고 이유를 주석으로 남김. `LOCAL_AI_STORAGE_BACKEND=sqlite`, `LOCAL_AI_SQLITE_DB_PATH`, `LOCAL_AI_CORRECTIONS_DIR`, `LOCAL_AI_NOTES_DIR`(여전히 repo 기본값) 정책은 그대로 유지. 이 변경으로 sqlite browser smoke도 JSON-default smoke와 동일하게 `data/web-search/` 아래에서 record를 공유하고, history-card reload 계열 시나리오가 sqlite backend에서도 동작.

2. **sqlite browser gate 실측 통과 확인** (기존 시나리오 재사용, 테스트 본문 변경 없음):
   - `history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다`
   - `history-card latest-update 다시 불러오기 후 WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
   - `history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`
   - `history-card entity-card 다시 불러오기 후 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`
   - `history-card entity-card 다시 불러오기 후 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다`
   - `history-card entity-card 다시 불러오기 후 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다`
   - `history-card latest-update 다시 불러오기 후 mixed-source source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
   - `history-card latest-update single-source 다시 불러오기 후 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다`
   - `history-card latest-update news-only 다시 불러오기 후 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다`
   - `history-card entity-card store-seeded actual-search 다시 불러오기 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다`

3. **docs sync**: sqlite browser gate inventory 문서 4개에 reload-core 10건을 추가해 총 47건으로 맞춤. `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책도 README / ACCEPTANCE_CRITERIA 노트에 한 줄로 추가.

4. **제품 코드 무변경**: history-card 렌더링 semantics, 저장 record shape, answer-mode composition, source-role policy 모두 손대지 않음. sqlite 전용 reload 플로우 없음.

## 검증

10개 exact scenario를 각각 `-g "<exact title>"`로 실행 (broader regex로 대체하지 않음):

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다" --reporter=line  # 1 passed (4.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update 다시 불러오기 후 WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source ..." --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 noisy single-source claim(출시일/2025/blog.example.com) ..." --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 actual-search source path(namu.wiki, ko.wikipedia.org) ..." --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) ..." --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update 다시 불러오기 후 mixed-source source path(store.steampowered.com, yna.co.kr) ..." --reporter=line  # 1 passed (3.6s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update single-source 다시 불러오기 후 source path(example.com/seoul-weather) ..." --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update news-only 다시 불러오기 후 기사 source path(hankyung.com, mk.co.kr) ..." --reporter=line  # 1 passed (3.6s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card store-seeded actual-search 다시 불러오기 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다" --reporter=line  # 1 passed (3.7s)
git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 opt-in sqlite browser gate inventory 10건을 실측으로 확정하고 1줄짜리 sqlite config 격리 조정을 한 Playwright-only smoke tightening bundle이었고, 최신 handoff가 요구한 focused rerun 10건을 모두 개별 실행으로 확인했기 때문에 full browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` override 제거로 sqlite browser smoke는 이제 JSON-default smoke와 같은 `data/web-search/` 디렉터리를 공유합니다. 서로 다른 Playwright config 간 병렬 실행은 같은 repo 경로를 쓰게 되므로, 현재처럼 config별 개별 실행(순차)에만 안전합니다. 이후 sqlite/JSON smoke를 동시에 돌리는 파이프라인이 생기면 격리 전략을 다시 봐야 합니다 (notes dir과 같은 트레이드오프).
- sqlite browser gate는 이번 라운드로 총 47건까지 확장됐습니다. 자연어 reload 체인, follow-up drift, zero-strong-slot edge, provenance exact-field 계열은 이번 슬라이스 scope 밖이라 아직 sqlite backend로 확인되지 않았습니다.
- reload 계열은 여전히 shipped UI 계약이며, 이번 라운드에서 answer-mode / verification label / source-role / source path / noisy-source 제외 규칙은 서버+UI 렌더링 수준에서 검증됐습니다.
- `stop-reverse-conflict` 시나리오의 "세션 리부팅 직후 1회 산발 timeout" 경향은 이번 라운드에서도 영향이 없었습니다. CI에서 재현되면 이전 라운드 기록대로 Playwright webServer 정리 타이밍을 함께 점검해야 합니다.
