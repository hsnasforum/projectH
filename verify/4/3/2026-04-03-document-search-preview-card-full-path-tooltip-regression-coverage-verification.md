## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-regression-coverage-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-regression-coverage.md`가 주장한 tooltip 회귀 검증 추가가 실제 코드·문서와 재실행 결과에 맞는지 다시 확인해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-playwright-selected-copy-coverage-docs-truth-sync-verification.md`가 다음 exact slice로 잡았던 `document-search preview-card full-path-tooltip regression coverage`가 실제로 landed했고, 그 closeout이 fully truthful한지도 좁게 재대조해야 했습니다.

## 핵심 변경
- latest `/work`의 코드·검증 주장은 대부분 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 search-only 시나리오에는 실제로 response detail preview와 transcript preview 양쪽의 `.search-preview-name` 첫 요소에 대해 `title` attribute가 full path(`.../budget-plan.md`)인지 확인하는 assertion 2건이 추가되어 있습니다.
  - 재실행한 `make e2e-test`도 `17 passed (2.0m)`로 통과해 latest `/work`의 browser rerun claim과 맞습니다.
- 이번 라운드의 범위는 current MVP 안에 머물렀습니다.
  - document-search preview card의 tooltip regression coverage와 그에 대한 docs sync 일부만 다뤘습니다.
  - approval/storage/session schema, web investigation, reviewed-memory, watcher, 장기 north-star 범위로는 넓어지지 않았습니다.
- 다만 latest `/work`의 "code/regression/docs가 모두 정합" 결론은 현재 tree와 완전히 맞지 않습니다.
  - `README.md`와 `docs/ACCEPTANCE_CRITERIA.md`는 새 full-path tooltip coverage를 반영합니다.
  - 하지만 `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 Playwright smoke coverage 설명은 아직 `selected-copy` regression까지만 적고, 이번 tooltip regression coverage는 반영하지 않습니다.
  - `AGENTS.md`의 Document Sync Rules는 smoke coverage 변경 시 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 동시 갱신을 요구하므로, latest `/work`는 docs truth-sync를 fully closed했다고 보기 어렵습니다.
- 따라서 다음 exact slice는 새 quality axis가 아니라 same-family current-risk인 `playwright preview-card tooltip docs truth-sync` 1건이 맞습니다.

## 검증
- `sed -n '1,240p' work/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-regression-coverage.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-playwright-selected-copy-coverage-docs-truth-sync-verification.md`
- `sed -n '1,220p' .pipeline/codex_feedback.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 통과
- `rg -n -C 2 "search-preview-name|toHaveAttribute\\(|title\\)|title =|full path tooltip|tooltip|selected-copy|search-only response" e2e/tests/web-smoke.spec.mjs app/static/app.js README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - tooltip assertion은 `e2e/tests/web-smoke.spec.mjs`에 존재
  - 구현은 `app/static/app.js`의 transcript/response preview 양쪽에서 `nameEl.title = sr.path || ""`
  - `README.md`, `docs/ACCEPTANCE_CRITERIA.md`는 tooltip coverage 반영
  - `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 아직 tooltip coverage 미반영
- `make e2e-test`
  - `17 passed (2.0m)`
- 미실행:
  - `python3 -m unittest -v tests.test_web_app`
  - 이번 latest `/work`는 Playwright assertion + docs 범위였고 Python/server 코드 변경이 없어 browser rerun만 재실행했습니다.

## 남은 리스크
- tooltip regression coverage 자체는 landed했고 browser rerun도 통과했지만, smoke coverage truth-sync는 아직 root docs 2곳(`docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`)에서 덜 닫힌 상태입니다.
- 따라서 `.pipeline/codex_feedback.md`는 `STATUS: implement`를 유지하되, 다음 exact slice를 `playwright preview-card tooltip docs truth-sync` 1건으로 갱신했습니다.
