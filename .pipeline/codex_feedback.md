STATUS: implement

다음 슬라이스: `document-search search-plus-summary response-detail preview-card first-card snippet-text regression coverage`

근거:
- latest `/work`: `work/4/3/2026-04-03-document-search-search-plus-summary-response-detail-preview-card-second-card-snippet-text-regression-coverage.md`
- latest `/verify`: `verify/4/3/2026-04-03-document-search-search-plus-summary-response-detail-preview-card-second-card-snippet-text-regression-coverage-verification.md`
- latest `/work`의 코드 변경과 browser rerun claim은 truthful합니다. current tree 기준으로 folder-search scenario 3의 response detail second-card snippet text `budget` assertion이 실제로 추가됐고, `make e2e-test`도 다시 통과했습니다.
- 이번 라운드 범위도 current MVP 안입니다. browser smoke assertion 1건만 추가했고 approval/storage/session schema, web investigation, reviewed-memory 쪽으로 넓어지지 않았습니다. docs를 건드리지 않은 것도 이번 라운드 범위에서는 truthful합니다.
- 다만 `/work`의 `response detail both cards × all properties ... snippet text 전부 잠김` 결론은 현재 tree와 맞지 않습니다. search-plus-summary response detail path의 first-card snippet은 아직 `toBeVisible()`까지만 잠기고, first-card snippet text direct assertion은 없습니다.
- 따라서 가장 작은 same-family current-risk reduction은 folder-search scenario 3의 search-plus-summary response detail panel에서 first-card snippet text를 직접 잠그는 것입니다. latest `/work`가 방금 second-card snippet text를 닫았으므로, 같은 panel의 first-card snippet text를 바로 이어서 잠그는 편이 transcript path나 다른 quality axis로 이동하는 것보다 더 작고 truthful합니다.

dirty worktree 경고:
- unrelated dirty worktree가 이미 있습니다: `.pipeline/README.md`, `.pipeline/experimental.pid`, `.pipeline/logs/experimental/*`, `.pipeline/state/*`, `ab_compare.py`, `pipeline-watcher-v3-logged.sh`, `start-pipeline.sh`, `watcher_core.py`, `verify/4/2/*`
- Codex verification 산출물인 `verify/4/3/*.md`와 `.pipeline/codex_feedback.md`도 현재 dirty입니다.
- 이번 슬라이스와 무관한 dirty 파일은 건드리거나 정리하지 마세요.

먼저 읽기:
- `AGENTS.md`
- `work/4/3/2026-04-03-document-search-search-plus-summary-response-detail-preview-card-second-card-snippet-text-regression-coverage.md`
- `verify/4/3/2026-04-03-document-search-search-plus-summary-response-detail-preview-card-second-card-snippet-text-regression-coverage-verification.md`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

구현 범위:
- folder-search scenario 3에서 `#response-search-preview .search-preview-snippet` first-card가 non-empty snippet text를 실제로 포함하는지 직접 잠그세요. 가능하면 현재 fixture에 맞는 안정적인 핵심 단어를 고르세요.
- 대상은 search-plus-summary response detail panel 경로만 우선 추가합니다. transcript path, second-card, tooltip/badge, search-only path는 이번 슬라이스에서 넓히지 마세요.
- smoke wording이 materially 더 구체화되지 않으면 docs는 건드리지 마세요.

범위 제한:
- 기본 대상: `e2e/tests/web-smoke.spec.mjs`
- 필요 시 docs 대상: `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`
- `app/static/app.js`, `core/agent_loop.py`, approval/storage/web investigation/reviewed-memory 경로 수정 금지
- unrelated dirty worktree cleanup 금지

필수 검증:
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "response-search-preview|search-preview-snippet|budget|budget-plan\\.md|folder-search" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- browser-visible smoke contract 변경이므로 `make e2e-test`
- Python/server 로직 변경이 없으면 `python3 -m unittest -v tests.test_web_app`는 재실행하지 않아도 되지만, 안 돌리면 `/work`에 명시하세요.

closeout 요구:
- `work/4/3/` 아래 새 `/work` 메모 1개 남기기
- 응답은 한국어 존댓말 유지
