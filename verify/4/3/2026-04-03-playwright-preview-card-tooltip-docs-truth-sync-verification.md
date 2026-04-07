## 변경 파일
- `verify/4/3/2026-04-03-playwright-preview-card-tooltip-docs-truth-sync-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-playwright-preview-card-tooltip-docs-truth-sync.md`가 직전 `/verify`가 잡았던 tooltip docs truth-sync current-risk를 실제로 닫았는지 다시 확인해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-regression-coverage-verification.md`가 다음 exact slice로 넘긴 same-family docs truth-sync 1건이 current tree와 truly 일치하는지도 재대조해야 했습니다.

## 핵심 변경
- latest `/work`의 docs-only 주장은 truthful합니다.
  - `docs/MILESTONES.md`의 search-only smoke 항목은 이제 `selected-copy` regression coverage와 함께 preview card filename의 full-path tooltip coverage를 반영합니다.
  - `docs/TASK_BACKLOG.md`의 implemented item 13도 같은 tooltip coverage를 반영합니다.
  - `README.md`, `docs/ACCEPTANCE_CRITERIA.md`에 먼저 반영돼 있던 tooltip wording과 now-closed root docs 2개가 현재 tree에서 서로 맞습니다.
- 이번 라운드 범위는 current MVP 안에 머물렀습니다.
  - Playwright smoke coverage 설명 2개 문서의 truth-sync만 다뤘고 production behavior, approval/storage/session schema, web investigation, reviewed-memory, watcher 쪽으로 넓어지지 않았습니다.
- latest `/work`가 적은 family closeout 판단도 이번에는 맞습니다.
  - preview-card tooltip family의 code(`app/static/app.js`), regression coverage(`e2e/tests/web-smoke.spec.mjs`), root docs(`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`)는 현재 tree에서 정합합니다.
- 따라서 다음 exact slice는 새 quality axis가 아니라 same-family current-risk 1건으로 좁히는 편이 맞습니다.
  - current shipped docs(`README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`)는 preview card가 filename 외에도 match type badge(`파일명 일치` / `내용 일치`)와 content snippet을 보여 준다고 적습니다.
  - 구현도 `app/static/app.js`의 transcript/response preview renderer 양쪽에서 `search-preview-match`, `search-preview-snippet`를 실제로 렌더링합니다.
  - 하지만 current Playwright smoke는 preview card visibility, hidden-body, `selected-copy`, filename tooltip만 잠그고 있고, badge/snippet user-visible contract는 직접 잠그지 않습니다.
  - 그래서 다음 한 슬라이스는 `document-search preview-card match-badge-snippet regression coverage`가 가장 작고 truthful한 same-family current-risk reduction입니다.

## 검증
- `sed -n '1,240p' work/4/3/2026-04-03-playwright-preview-card-tooltip-docs-truth-sync.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-regression-coverage-verification.md`
- `sed -n '1,260p' .pipeline/codex_feedback.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 통과
- `rg -n "selected-copy|tooltip|search-only response|preview card" docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - latest `/work` 주장과 일치
- `sed -n '75,95p' README.md`
- `sed -n '126,138p' docs/PRODUCT_SPEC.md`
- `sed -n '18,32p' docs/ACCEPTANCE_CRITERIA.md`
  - preview card contract가 filename + tooltip + match badge + content snippet까지 문서화되어 있음을 재확인
- `sed -n '996,1045p' app/static/app.js`
- `sed -n '1178,1210p' app/static/app.js`
  - transcript/response detail preview 양쪽 모두 `search-preview-match`, `search-preview-snippet` 렌더링 확인
- `rg -n "search-preview-match|search-preview-snippet|파일명 일치|내용 일치|snippet|preview card" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py app/static/app.js README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - docs/implementation에는 존재하지만 current Playwright smoke에 direct badge/snippet assertion 부재 확인
- 미실행:
  - `python3 -m unittest -v tests.test_web_app`
  - `make e2e-test`
  - latest `/work`가 docs-only truth-sync 라운드라 이번 검수에서는 다시 돌리지 않았습니다. underlying browser rerun truth는 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-regression-coverage-verification.md`의 `17 passed (2.0m)`를 유지했습니다.

## 남은 리스크
- latest `/work` 자체는 현재 tree와 맞고, preview-card tooltip docs truth-sync current-risk도 이번 라운드로 닫혔습니다.
- 다만 preview card의 match badge와 content snippet은 현재 shipped contract이면서도 direct browser regression coverage가 없습니다.
- 따라서 `.pipeline/codex_feedback.md`는 `STATUS: implement`를 유지하되, 다음 exact slice를 `document-search preview-card match-badge-snippet regression coverage` 1건으로 갱신했습니다.
