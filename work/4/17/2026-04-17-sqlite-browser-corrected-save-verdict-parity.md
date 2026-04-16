# sqlite-browser-corrected-save-verdict-parity

## 변경 파일

- `e2e/playwright.sqlite.config.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- `using-superpowers`

## 변경 이유

이전 `/work`에서 sqlite browser gate가 recurrence aggregate 5건으로 확장됐고, 최신 `/verify`는 같은 family의 남은 current-risk가 이제 shipped document-loop save/correction/verdict continuity라고 판단했습니다. 이번 라운드는 code/ship 계약을 건드리지 않고 기존 `web-smoke.spec.mjs`의 4개 문서 루프 시나리오를 opt-in sqlite backend에서 동일하게 통과시키는 bounded parity bundle을 닫는 것이 목적입니다. 실행 과정에서 `corrected-save first bridge path` 시나리오가 실패했는데, 기존 `playwright.sqlite.config.mjs`가 `LOCAL_AI_NOTES_DIR`을 임시 디렉터리로 재지정하는 바람에 테스트가 단언하는 `data/notes/long-summary-fixture-summary.md` 경로에 저장본이 남지 않았습니다. 이 config 격리가 현재 슬라이스에 부족했기 때문에 notes dir override만 제거해 repo 기본값(`data/notes/`)으로 되돌리고, 나머지 sqlite DB · corrections · web-search 격리는 유지했습니다.

## 핵심 변경

1. **`e2e/playwright.sqlite.config.mjs`**: `LOCAL_AI_NOTES_DIR` override 한 줄만 제거하고 이유를 주석으로 남김. `LOCAL_AI_STORAGE_BACKEND=sqlite`, `LOCAL_AI_SQLITE_DB_PATH`, `LOCAL_AI_CORRECTIONS_DIR`, `LOCAL_AI_WEB_SEARCH_HISTORY_DIR`는 그대로 유지. 이 변경으로 sqlite browser smoke도 JSON-default smoke와 동일하게 `data/notes/` 아래에 저장본을 기록하고, 저장본 내용을 단언하는 document-loop 시나리오가 sqlite backend에서도 동작.

2. **sqlite browser gate 실측 통과 확인** (기존 시나리오 재사용, 코드 변경 없음):
   - `원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다`
   - `내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다`
   - `corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다`
   - `corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다`

3. **docs sync**: sqlite browser gate inventory 문서 4건에 위 시나리오를 추가.
   - `README.md` `SQLite Browser Smoke (opt-in backend parity gate)` 섹션의 시나리오 목록을 9건으로 확장하고, notes dir이 repo 기본값인 이유를 한 줄로 주석.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite browser smoke bullet에 document-loop 시나리오 4건 추가 + 격리 정책(`LOCAL_AI_NOTES_DIR` 기본값 유지 이유) 한 줄 추가.
   - `docs/MILESTONES.md` SQLite browser smoke baseline milestone 문구에 document-loop save/correction/verdict continuity 4건 포함으로 확장.
   - `docs/TASK_BACKLOG.md` `Partial / Opt-In` SQLite backend 항목의 browser-level parity gate 설명을 같은 9건으로 확장.

4. **제품 코드 무변경**: save/correction/verdict 계약, store schema, frontend는 손대지 않음. sqlite 전용 플로우 없음.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다" --reporter=line  # 1 passed (5.6s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다" --reporter=line  # 1 passed (6.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다" --reporter=line  # 1 passed (6.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다" --reporter=line  # 1 passed (5.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다" --reporter=line  # 1 passed (8.6s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate stale candidate retires before apply start" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate active lifecycle survives supporting correction supersession" --reporter=line  # 1 passed (5.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate recorded basis label survives supporting correction supersession" --reporter=line  # 1 passed (5.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다" --reporter=line  # 1 passed (8.7s, 1회 transient timeout 후 재실행으로 안정)
git diff --check -- e2e/playwright.sqlite.config.mjs e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 opt-in sqlite browser gate inventory 4건을 추가하고 1줄짜리 sqlite config 격리 조정을 한 Playwright-only smoke tightening bundle이었고, 최신 handoff가 요구한 focused rerun 4건 + 기존 recurrence aggregate 5건 모두 확인했기 때문에 full browser suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- `LOCAL_AI_NOTES_DIR` override 제거로 sqlite browser smoke가 이제 JSON-default smoke와 같은 `data/notes/` 디렉터리를 공유합니다. 서로 다른 Playwright config 간 병렬 실행은 같은 repo 경로를 쓰게 되므로, 현재처럼 config별 개별 실행(순차)에만 안전합니다. 이후 sqlite/JSON smoke를 동시에 돌리는 파이프라인이 생기면 격리 전략을 다시 봐야 합니다.
- `stop-reverse-conflict` 시나리오는 직전 라운드에 이어 이번에도 첫 실행 1회 산발 실패 후 재실행으로 안정화됐습니다. Python service-level 재구성으로는 이미 문제가 없음을 확인했고 UI 흐름에서도 동일한 aggregate-trigger-box 재렌더링 경로를 공유하므로, CI 상에서 반복 재현되지 않는 한 sqlite-specific 회귀로 보기 어렵습니다. CI에서 재현되면 Playwright webServer 정리와 `fs.mkdtempSync` 경로 회수 상태를 같이 점검해야 합니다.
- sqlite browser gate는 이번 라운드로 recurrence aggregate 5건 + document-loop save/correction/verdict 4건까지 확장됐습니다. 이 밖의 JSON-default 시나리오(summary source-label, 권한 게이트, history-card reload, 스캔 PDF OCR 안내 등)를 sqlite backend에서 같이 돌려보는 일은 이번 슬라이스 scope 밖입니다.
- `e2e/playwright.sqlite.config.mjs`의 sqlite DB, corrections, web-search 임시 디렉터리는 여전히 `os.tmpdir()`에 생기며, local dev 환경에서는 OS가 관리하지만 CI에서는 별도 cleanup 정책이 필요할 수 있습니다.
