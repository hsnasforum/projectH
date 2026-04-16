# 2026-04-17 sqlite browser corrected-save verdict parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/17/2026-04-17-sqlite-browser-corrected-save-verdict-parity.md`는 opt-in sqlite browser gate를 recurrence aggregate 5건에서 document-loop save/correction/verdict 4건까지 확장했고, 이를 위해 `e2e/playwright.sqlite.config.mjs`에서 `LOCAL_AI_NOTES_DIR` override를 제거했다고 주장합니다.
- 이번 verification 라운드는 그 config 조정이 실제로 save/corrected-save/content-verdict continuity 4건을 sqlite backend에서 살리는지, 문서 동기화가 현재 tree와 맞는지, 그리고 이전 sqlite recurrence gate를 깨지 않았는지를 가장 좁은 범위에서 다시 확인하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 재실행 결과에 대체로 부합합니다.
  - `e2e/playwright.sqlite.config.mjs`에는 더 이상 `LOCAL_AI_NOTES_DIR` override가 없고, 주석도 `data/notes/` 기본값을 유지하는 이유와 현재 sqlite 격리 범위(sqlite DB / corrections / web-search)만 설명합니다.
  - document-loop save/correction/verdict 4개 Playwright 시나리오는 sqlite config로 모두 다시 `1 passed`였습니다.
  - 이전 sqlite recurrence family는 이번 라운드의 직접 수정 대상이 아니므로 전부 다시 돌리지는 않았지만, representative smoke인 emitted-apply-confirm lifecycle 1건을 spot-check한 결과 계속 `1 passed`였습니다.
  - `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 sqlite browser gate를 recurrence aggregate 5건 + document-loop save/correction/verdict 4건으로 일관되게 설명합니다.
- 따라서 최신 `/work`는 이번 라운드의 실제 변경 목표였던 sqlite document-loop save/correction/verdict parity bundle 기준으로 truthful합니다.
- 다만 `/work`가 적은 "기존 recurrence aggregate 5건 모두 확인"은 이번 verification 라운드에서 독립 재실행하지 않았습니다. 현재 config 변경이 notes dir override 제거 한 줄에 한정되고 representative recurrence rerun이 green이어서 모순은 보이지 않지만, 이 `/verify`는 4개 신규 대상 + recurrence representative 1건만 재실행한 검수 결과입니다.

## 검증
- `git status --short`
  - 결과: rolling `.pipeline` runtime 파일, same-day `/work` / `/verify`, runtime/controller unrelated hunks가 섞인 dirty tree였고, `e2e/playwright.sqlite.config.mjs`는 계속 untracked file 상태였습니다.
- `git diff -- e2e/playwright.sqlite.config.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: sqlite browser gate 설명이 current 9-scenario inventory와 notes-dir policy를 반영하는 것을 확인했습니다.
  - 보충: dirty tree 때문에 git base 대비 diff는 5건→9건의 round-only delta가 아니라 sqlite browser gate 섹션 누적 상태로 보입니다. 그래서 최신 `/work` truth는 이전 `/verify`와 현재 파일 본문을 같이 대조해 판단했습니다.
- `sed -n '1,220p' e2e/playwright.sqlite.config.mjs`
- `rg -n "SQLite Browser Smoke|corrected-save first bridge|원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다|내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다|corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다|LOCAL_AI_NOTES_DIR" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs e2e/playwright.sqlite.config.mjs`
  - 결과: docs 4개, sqlite config, `web-smoke.spec.mjs`가 같은 9개 sqlite gate inventory와 notes-dir policy를 가리키는 것을 확인했습니다.
- `sed -n '1,220p' docs/NEXT_STEPS.md`
  - 결과: sqlite는 여전히 opt-in seam이고 broader default rollout/corrections migration은 later라는 framing이 최신 `/work`와 충돌하지 않음을 확인했습니다.
- `node --check e2e/playwright.sqlite.config.mjs`
  - 결과: 출력 없음
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다" --reporter=line`
  - 결과: `1 passed (5.7s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다" --reporter=line`
  - 결과: `1 passed (6.0s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다" --reporter=line`
  - 결과: `1 passed (6.1s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다" --reporter=line`
  - 결과: `1 passed (5.7s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다" --reporter=line`
  - 결과: `1 passed (8.6s)`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
  - 보충: `e2e/playwright.sqlite.config.mjs`는 현재 untracked라 `git diff --check`로 직접 검사되지 않습니다. 대신 `node --check`와 Playwright rerun으로 config syntax/behavior를 확인했습니다.
- full `make e2e-test`, full sqlite browser suite, Python unit suite는 미실행
  - 이유: 이번 `/work`는 sqlite config 1줄 조정 + save/correction/verdict browser parity tightening round였고, 변경 영향을 직접 받는 Playwright 4건과 representative sqlite recurrence spot-check 1건이 가장 좁은 검증이었습니다.

## 남은 리스크
- sqlite browser gate는 이번 라운드로 recurrence aggregate 5건 + save/correction/verdict 4건까지 확인됐습니다. 다음 same-family current-risk는 approval 이후가 아니라 core document-loop summary/search surface입니다.
- 우선순위상 secondary-mode web investigation/history-card sqlite parity보다, `문서 요약` / `선택 결과 요약` / search preview / search-only hidden-body 같은 기본 문서 생산성 흐름을 sqlite browser path에서 먼저 닫는 편이 맞습니다.
- 따라서 다음 exact slice는 existing `web-smoke.spec.mjs`의 core document summary/search 4건을 `e2e/playwright.sqlite.config.mjs`로 재사용해 sqlite backend에서도 동일한 visible contract가 유지되는지 닫는 bounded browser bundle이어야 합니다.
