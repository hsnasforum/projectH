## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-ordered-label-current-contract-docs-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-preview-card-ordered-label-current-contract-docs-truth-sync.md`의 current-contract docs truth sync 주장을 현재 tree 기준으로 다시 검수하고, same-family 다음 단일 슬라이스를 current-risk reduction 하나로 좁히기 위해서입니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다. `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`는 모두 preview card를 `matched file's ordered label`로 서술하고 있고, stale wording `matched file's name`는 더 이상 남아 있지 않습니다.
- `git diff -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`가 현재 비어 있으므로, targeted docs는 지금 시점에 clean합니다. 이번 검수 관점에서는 latest `/work`가 주장한 docs truth가 이미 현재 tree에 반영되어 있다는 뜻이며, 그 주장과 모순되지는 않습니다.
- latest `/work`의 구현 근거도 현재 코드와 맞습니다. `app/static/app.js`의 response detail / transcript 렌더링은 모두 `nameEl.textContent = (idx + 1) + ". " + fileName;`를 사용하고, `e2e/tests/web-smoke.spec.mjs`는 search-plus-summary와 search-only 양쪽의 response detail / transcript 네 surface에서 모두 ordered label 존재를 계속 확인하고 있습니다.
- same-day latest `/verify`였던 `verify/4/3/2026-04-03-document-search-preview-card-ordinal-prefix-smoke-coverage-docs-truth-sync-verification.md`는 사실관계 자체는 맞지만, 거기서 제안한 next slice는 latest `/work`가 이미 닫았으므로 handoff로서는 stale입니다.
- 다음 exact slice는 `document-search preview-card ordered-label exact-text smoke tightening`으로 갱신했습니다. 현재 smoke는 네 surface에서 `1. budget-plan.md` / `2. memo.md`를 `toContainText(...)`로만 확인하므로 unexpected prefix/suffix나 extra visible text가 끼어도 통과할 수 있습니다. 현재 shipped UI는 exact visible ordered label을 렌더링하므로, 같은 family의 가장 작은 current-risk reduction은 이 ordered-label assertions를 exact text로 잠그는 것입니다.

## 검증
- `sed -n '1,260p' work/4/3/2026-04-03-document-search-preview-card-ordered-label-current-contract-docs-truth-sync.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-preview-card-ordinal-prefix-smoke-coverage-docs-truth-sync-verification.md`
- `sed -n '1,220p' README.md`
- `sed -n '1,260p' docs/PRODUCT_SPEC.md`
- `sed -n '1,260p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,180p' docs/MILESTONES.md`
- `sed -n '1,180p' docs/TASK_BACKLOG.md`
- `sed -n '990,1045p' app/static/app.js`
- `sed -n '1160,1225p' app/static/app.js`
- `sed -n '180,290p' e2e/tests/web-smoke.spec.mjs`
- `git status --short`
- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `rg -n "matched file's name" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "matched file's ordered label" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "matched file's name|ordered label|ordered labels|preview card|search-preview-name|1\\. budget-plan\\.md|2\\. memo\\.md|idx \\+ 1" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/static/app.js e2e/tests/web-smoke.spec.mjs`
- `make e2e-test`는 재실행하지 않았습니다. latest `/work` 범위가 docs-only이고 runtime/test 파일 변경이 없었기 때문입니다.
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. server 로직 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `.pipeline/*`, watcher, operator 문서, `AGENTS.md` 계열 dirty 변경을 정리하거나 되돌리면 안 됩니다.
- current-contract docs truth sync는 now aligned이지만, preview-card ordered-label regression smoke는 아직 exact visible text까지 잠겨 있지 않습니다.
- React 실험 경로인 `app/frontend/src/components/MessageBubble.tsx`는 여전히 `result.path`를 그대로 렌더링하지만, current shipped web shell entry는 `app/templates/index.html` + `/static/app.js`입니다. 이번 handoff는 shipped shell smoke만 다루고 실험 경로는 건드리지 않습니다.
