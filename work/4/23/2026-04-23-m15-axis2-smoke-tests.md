# 2026-04-23 M15 Axis 2 quality integration smoke tests

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m15-axis2-smoke-tests.md`

## 사용 skill
- `doc-sync`: M15 Axis 2 smoke coverage shipped 기록을 `docs/MILESTONES.md`에 맞췄습니다.
- `finalize-lite`: handoff acceptance 명령과 남은 미검증 범위를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 검증 결과를 `/work` 형식에 맞춰 기록했습니다.

## 변경 이유
- advisory seq 36 / implement handoff seq 37 기준 M15 Axis 2 품질 통합 smoke coverage가 필요했습니다.
- M14 Axis 2/3 및 M15 Axis 1에서 추가된 `quality_info`가 review queue API와 browser-facing badge 경로에서 깨지지 않는지 targeted Playwright 시나리오로 고정해야 했습니다.

## 핵심 변경
- `web-smoke.spec.mjs` 끝에 `/api/chat/stream` NDJSON final payload를 읽는 helper를 추가했습니다.
- correction -> `/api/candidate-confirmation` 흐름으로 durable candidate를 만들고, `review_queue_items[0].quality_info` shape를 검증하는 Playwright 시나리오를 추가했습니다.
- 동일 흐름에서 high-quality review item이 생긴 경우 `.quality-count` DOM badge 텍스트를 best-effort로 확인하는 시나리오를 추가했습니다.
- focused grep acceptance가 두 신규 시나리오를 모두 잡도록 두 번째 test title에도 `quality-info` prefix를 포함했습니다.
- `docs/MILESTONES.md` M15 shipped infrastructure에 Axis 2 smoke tests 항목을 추가했습니다.
- production code(`app/`, `storage/`, `core/`)와 Playwright config는 변경하지 않았습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs docs/MILESTONES.md`
  - 통과: 출력 없음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "quality-info" --reporter=line`
  - 통과: `2 passed (47.9s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs --config playwright.sqlite.config.mjs --reporter=line`
  - 통과: `123 passed (4.7m)`
  - 참고: 실행 중 `NO_COLOR`/`FORCE_COLOR` 경고와 PDF fixture의 `incorrect startxref pointer(3)` 웹서버 로그가 있었지만 실패로 이어지지 않았습니다.

## 남은 리스크
- `.quality-count` DOM assertion은 high-quality backend item이 존재하고 실제 DOM element가 보일 때만 텍스트를 확인하는 조건부 검증입니다. 현재 shipped `/app` smoke는 static shell을 사용하므로 React `ChatArea.tsx` badge 노출 경로가 항상 강제 검증되지는 않습니다.
- non-SQLite 전체 browser smoke는 실행하지 않았습니다. 대신 handoff acceptance에 따라 default backend focused 신규 시나리오 2개와 SQLite 전체 smoke를 실행했습니다.
