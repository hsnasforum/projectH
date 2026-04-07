## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-snippet-text-smoke-coverage-docs-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`의 preview-card snippet-text smoke coverage docs truth sync가 실제 트리와 맞는지 다시 검수하고, 같은 document-search preview-card 축에서 다음 단일 슬라이스를 하나로 좁히기 위해서입니다.

## 핵심 변경
- latest `/work`인 `work/4/3/2026-04-03-document-search-preview-card-snippet-text-smoke-coverage-docs-truth-sync.md`의 주장은 현재 트리 기준으로 truthful합니다. `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`의 smoke coverage wording은 실제로 `snippet visibility` / `content snippet visibility`에서 `snippet text content` / `content snippet text`로 바뀌어 있고, 대상 파일 diff도 현재 없습니다.
- wording sync의 근거도 현재 smoke 본문과 맞습니다. `e2e/tests/web-smoke.spec.mjs`에는 search-plus-summary와 search-only 양쪽 모두 response detail과 transcript의 both cards snippet에 대한 direct text assertion이 실제로 존재합니다. 문서가 이제 visibility 수준이 아니라 text content 수준으로 설명하는 것이 맞습니다.
- latest `/work`의 docs 범위 판단도 truthful합니다. `docs/PRODUCT_SPEC.md`와 `docs/NEXT_STEPS.md`는 여전히 generic `content snippet` 수준으로 남아 있지만, 현재 구현/coverage를 과장하거나 누락하는 stale wording은 보이지 않아 이번 라운드에서 건드리지 않은 판단이 맞습니다.
- latest `/work`는 테스트를 돌렸다고 주장하지 않았고, 현재 재검증 기준에서도 docs-only change 자체를 확인하는 데 필요한 좁은 diff/grep 검증은 통과했습니다. 추가로 `make e2e-test`를 다시 돌렸고 현재 트리에서 `17 passed (2.1m)`로 통과했습니다.
- same-day latest `/verify`였던 `verify/4/3/2026-04-03-document-search-search-only-transcript-preview-card-first-card-snippet-text-regression-coverage-verification.md`는 사실관계 자체는 맞고, 거기서 제안한 docs truth sync next slice도 latest `/work`가 실제로 닫았습니다. 다만 next-slice handoff로서는 이제 stale입니다.
- 다음 exact slice는 `document-search search-only response-detail preview-card first-card ordinal-prefix regression coverage`로 갱신했습니다. current tree에서 preview-card 이름은 실제 UI 코드상 `(idx + 1) + ". " + fileName`으로 렌더링되지만, smoke는 아직 `budget-plan.md` / `memo.md` bare filename만 직접 잠그고 ordinal prefix는 잠그지 않습니다. tooltip과 match badge는 이미 direct assertion으로 닫혀 있으므로, body text가 숨겨지는 search-only response detail의 first-card ordinal prefix가 같은 family의 가장 작은 current-risk reduction입니다.

## 검증
- `sed -n '70,100p' README.md`
- `sed -n '1310,1326p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '30,42p' docs/MILESTONES.md`
- `sed -n '18,30p' docs/TASK_BACKLOG.md`
- `sed -n '182,285p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '1008,1022p' app/static/app.js`
- `sed -n '1190,1202p' app/static/app.js`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "snippet visibility|content snippet visibility|snippet text content|content snippet text" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "idx \\+ 1|search-preview-name|budget-plan\\.md|memo\\.md" app/static/app.js e2e/tests/web-smoke.spec.mjs`
- `rg -n "snippet visibility|content snippet visibility|snippet text content|content snippet text|content snippet" docs README.md`
- `make e2e-test` (`17 passed (2.1m)`)
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. server 로직 변경이 없고, 이번 확인의 직접 대상이 docs truth sync와 browser smoke contract이기 때문입니다.

## 남은 리스크
- preview-card snippet-text docs truth sync는 닫혔지만, preview-card filename ordinal prefix는 아직 smoke에서 direct text assertion으로 잠겨 있지 않습니다.
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 이번 슬라이스와 무관한 `.pipeline/*`, watcher, operator 문서 변경을 건드리거나 정리하지 말아야 합니다.
