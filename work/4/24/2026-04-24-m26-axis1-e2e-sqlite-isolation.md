# 2026-04-24 M26 Axis 1 e2e sqlite isolation

## 변경 파일
- `e2e/playwright.config.mjs`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m26-axis1-e2e-sqlite-isolation.md`

## 사용 skill
- `doc-sync`: M26 정의와 Axis 1 shipped entry를 현재 구현 사실에 맞춰 `docs/MILESTONES.md`에 반영했습니다.
- `finalize-lite`: handoff acceptance에 적힌 좁은 검증만 실행하고 `/work` closeout을 실제 결과 기준으로 정리했습니다.

## 변경 이유
- 이번 라운드는 `CONTROL_SEQ: 104` handoff로, default Playwright config가 반복 실행 사이에 `data/projecth.db`를 재사용하면서 correction 누적이 쌓여 false global candidate hit를 만들던 문제를 줄이는 M26 Axis 1 slice입니다.
- `e2e/playwright.sqlite.config.mjs`는 이미 `fs.mkdtempSync()`로 per-run SQLite DB를 쓰고 있었지만, 기본 `e2e/playwright.config.mjs`에는 같은 격리 패턴이 없어 cross-run test isolation이 깨질 수 있었습니다.
- 이번 변경은 production 서버 경로는 건드리지 않고, Playwright default config에만 per-run temp DB를 부여하는 bounded test-infra slice입니다.

## 핵심 변경
- `e2e/playwright.config.mjs`
  - `node:os`, `node:fs` import를 추가했습니다.
  - `fs.mkdtempSync(path.join(os.tmpdir(), "pw-default-"))`로 run마다 새로운 temp 디렉터리를 만들고 `defaultSqliteDbPath`를 계산하도록 했습니다.
  - `webServer.command`에 `LOCAL_AI_SQLITE_DB_PATH=${defaultSqliteDbPath}`를 추가해 default Playwright run이 repo 기본 `data/projecth.db` 대신 run-local SQLite DB를 사용하게 했습니다.
- `docs/MILESTONES.md`
  - `Milestone 26: Global Candidate E2E Test Isolation` 정의와 Axis 1 shipped entry를 추가했습니다.

## 검증
- `cd e2e && npx playwright test --list`
  - 통과: config parse error 없이 전체 테스트 목록을 출력했습니다.
  - 결과: `Total: 143 tests in 2 files`
- `git diff --check -- e2e/playwright.config.mjs docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- 이번 라운드는 handoff 경계에 따라 config parse/list 확인만 했고, 실제 full browser suite는 돌리지 않았습니다. release gate는 verify lane 범위입니다.
- per-run DB isolation만 추가했고 per-test DB reset은 하지 않았습니다. 따라서 같은 run 안에서는 기존 fixture uniqueness convention이 계속 필요합니다.
- `data/notes/`와 `data/web-search/`는 handoff 지시대로 repo 기본 경로를 유지했습니다. 이번 라운드는 SQLite DB 격리만 다뤘습니다.
- 작업 시작 시점에 이미 존재하던 unrelated untracked 상태(`report/gemini/2026-04-23-m20-closure-consolidation.md`, `report/gemini/2026-04-23-m21-axis2-reject-scope.md`, `report/gemini/2026-04-23-m21-definition.md`, `report/gemini/2026-04-23-m22-scope-definition.md`)는 건드리지 않았습니다.
