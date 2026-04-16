# 2026-04-17 sqlite browser recurrence aggregate smoke baseline verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/17/2026-04-17-sqlite-browser-recurrence-aggregate-smoke-baseline.md`는 opt-in sqlite backend에 대한 첫 browser-level recurrence aggregate smoke baseline을 추가했고, emitted-apply-confirm lifecycle과 stale candidate retirement 두 시나리오를 SQLite browser gate로 닫았다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 focused rerun 결과에 맞는지 다시 확인하고, 같은 family의 다음 exact browser slice를 one-shot으로 고정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - 새 파일 `e2e/playwright.sqlite.config.mjs`가 실제로 존재합니다.
  - 이 config는 `app.web`를 port `8880`에서 `LOCAL_AI_STORAGE_BACKEND=sqlite`와 isolated temp dirs(`sqlite DB`, `notes`, `corrections`, `web-search`)로 부팅하도록 설정되어 있습니다.
  - `web-smoke.spec.mjs` 시나리오 본문을 fork하지 않고 기존 시나리오를 `-g` filter로 재사용하는 구조가 맞습니다.
- docs sync도 현재 구현과 맞습니다.
  - `README.md`에는 `SQLite Browser Smoke (opt-in backend parity gate)` 섹션이 추가되어 있고, 현재 sqlite browser gate 시나리오 2건을 명시합니다.
  - `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에도 sqlite browser smoke baseline이 반영되어 있습니다.
- focused rerun 결과도 최신 `/work`와 일치했습니다.
  - `same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다`는 sqlite config로 `1 passed`였습니다.
  - `same-session recurrence aggregate stale candidate retires before apply start`도 sqlite config로 `1 passed`였습니다.
- 따라서 최신 `/work`는 truthful합니다.
  - browser-visible recurrence aggregate baseline 2건이 실제로 sqlite backend에서 다시 통과했습니다.
  - same-family current-risk가 service-level parity에서 browser-level opt-in sqlite smoke로 이동했다는 이전 `/verify`의 판단과도 정합적입니다.

## 검증
- `git status --short`
  - 결과: rolling `.pipeline` runtime 파일, same-day `/work` / `/verify` 노트, earlier sqlite/helper/controller hunks가 섞인 dirty tree였고, `e2e/playwright.sqlite.config.mjs`는 현재 untracked new file 상태였습니다.
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,240p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
  - 결과: reviewed-memory shipped browser boundary와 sqlite opt-in framing이 최신 `/work` 설명과 충돌하지 않음을 확인했습니다.
- `git diff --stat -- e2e/playwright.sqlite.config.mjs e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: tracked diff는 docs 4개에만 잡혔고, 새 sqlite Playwright config는 untracked file이라 stat에 포함되지 않았습니다.
- `git diff -- e2e/playwright.sqlite.config.mjs e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: docs sync diff를 확인했고, `web-smoke.spec.mjs` 본문은 그대로 재사용된다고 보는 것이 맞았습니다.
- `sed -n '1,220p' e2e/playwright.sqlite.config.mjs`
  - 결과: sqlite backend env override와 isolated temp dir wiring을 직접 확인했습니다.
- `rg -n "playwright.sqlite.config|same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다|same-session recurrence aggregate stale candidate retires before apply start" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - 결과: 새 sqlite gate 문구와 대상 시나리오 2건이 docs와 existing smoke spec에 맞게 연결되어 있음을 확인했습니다.
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다" --reporter=line`
  - 결과: `1 passed (8.5s)`
- `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "same-session recurrence aggregate stale candidate retires before apply start" --reporter=line`
  - 결과: `1 passed (4.4s)`
- `git diff --check -- e2e/playwright.sqlite.config.mjs e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
  - 보충: `e2e/playwright.sqlite.config.mjs`가 현재 untracked라 `git diff --check` 자체는 그 파일 내용을 직접 lint하지 않습니다. 대신 파일 본문 직접 확인과 실제 Playwright 실행으로 새 config truth를 검증했습니다.
- full `make e2e-test`, full sqlite browser suite, Python unit suite는 미실행
  - 이유: 이번 `/work`는 Playwright-only smoke baseline tightening round였고, 최신 `/work`가 명시한 sqlite browser gate 2건 재확인에는 isolated scenario rerun이 가장 좁고 직접적인 검증이었습니다.

## 남은 리스크
- sqlite browser gate는 이번 round로 recurrence aggregate의 pre-confirm baseline 2건을 닫았습니다.
- 남은 same-family browser current-risk는 post-confirm / post-recorded lifecycle 쪽입니다.
  - `same-session recurrence aggregate active lifecycle survives supporting correction supersession`
  - `same-session recurrence aggregate recorded basis label survives supporting correction supersession`
  - `same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다`
- 이 세 시나리오는 모두 기존 emitted/apply/confirm 이후의 user-visible continuity를 다루며 setup과 검증 축이 겹치므로, 다음 exact slice는 또 하나의 micro-smoke가 아니라 sqlite browser post-confirm lifecycle bundle로 닫는 편이 맞습니다.
