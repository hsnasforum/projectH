## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-ordinal-prefix-smoke-coverage-docs-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`의 preview-card ordinal-prefix smoke-coverage docs truth sync가 실제 문서와 현재 smoke contract에 맞는지 다시 검수하고, 같은 preview-card visible-contract 축에서 다음 단일 슬라이스를 하나로 좁히기 위해서입니다.

## 핵심 변경
- latest `/work`인 `work/4/3/2026-04-03-document-search-preview-card-ordinal-prefix-smoke-coverage-docs-truth-sync.md`의 주장은 현재 트리 기준으로 truthful합니다. `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`의 smoke coverage wording은 실제로 `both cards' filenames` / `preview card filenames`에서 `both cards' ordered labels` / `preview card ordered labels`로 바뀌어 있습니다.
- 최신 `/work`의 변경 이유도 현재 구현과 맞습니다. `app/static/app.js`는 response detail과 transcript preview card 이름 모두를 여전히 `(idx + 1) + ". " + fileName`으로 렌더링하고, `e2e/tests/web-smoke.spec.mjs`는 search-plus-summary와 search-only 양쪽에서 `1. budget-plan.md`, `2. memo.md` direct assertion을 이미 포함합니다. smoke coverage 요약 문서를 ordered label 기준으로 맞춘 판단이 맞습니다.
- latest `/work`의 검증 주장도 현재 기준으로 맞습니다. `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 깨끗했고, stale wording `both cards' filenames|preview card filenames`는 더 이상 남아 있지 않으며, `ordered labels` wording은 네 문서에 실제로 존재합니다.
- latest `/work`의 `make e2e-test` / `python3 -m unittest -v tests.test_web_app` 미실행 판단도 이번 docs-only 라운드 범위에서는 truthful합니다. 이번 변경은 smoke wording sync만 다뤘고, current tree에서 preview-card ordered-label contract을 보장하는 code/test 경로는 바뀌지 않았습니다.
- same-day latest `/verify`였던 `verify/4/3/2026-04-03-document-search-search-plus-summary-transcript-preview-card-second-card-ordinal-prefix-regression-coverage-verification.md`는 사실관계 자체는 맞고, 거기서 제안한 next slice도 latest `/work`가 실제로 닫았습니다. 다만 next-slice handoff로서는 이제 stale입니다.
- 다음 exact slice는 `document-search preview-card ordered-label current-contract docs truth sync`로 갱신했습니다. 현재 smoke coverage 요약 문서 4개는 ordered label wording으로 맞아졌지만, current-contract 문서인 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`는 아직 generic `matched file's name` wording에 머물러 있습니다. current UI와 current smoke truth는 preview card가 bare filename이 아니라 ordered visible label을 렌더링함을 보여 주므로, 같은 family에서 남은 가장 작은 contract-truth sync는 이 3개 문서의 top-level wording 정리입니다.

## 검증
- `sed -n '1,260p' work/4/3/2026-04-03-document-search-preview-card-ordinal-prefix-smoke-coverage-docs-truth-sync.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-search-plus-summary-transcript-preview-card-second-card-ordinal-prefix-regression-coverage-verification.md`
- `sed -n '1,220p' README.md`
- `sed -n '1,220p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '1,120p' docs/MILESTONES.md`
- `sed -n '1,120p' docs/TASK_BACKLOG.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/PRODUCT_SPEC.md`
- `sed -n '200,320p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '1000,1026p' app/static/app.js`
- `git status --short`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "both cards' filenames|preview card filenames" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "ordered labels" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "matched file's name|ordered labels|1\\. budget-plan\\.md|2\\. memo\\.md|search-preview-name|idx \\+ 1" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs app/static/app.js`
- `make e2e-test`는 재실행하지 않았습니다. 이번 확인의 직접 대상이 docs-only truth sync였고, code/test 경로 변경이 없기 때문입니다.
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. server 로직 변경이 없기 때문입니다.

## 남은 리스크
- smoke coverage 요약 문서는 now aligned이지만, current-contract 문서 3개는 아직 preview card를 bare filename 수준으로만 서술합니다.
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 이번 슬라이스와 무관한 `.pipeline/*`, watcher, operator 문서 변경을 건드리거나 정리하지 말아야 합니다.
