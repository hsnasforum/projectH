## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-exact-path-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-exact-path-smoke-tightening.md`의 test-only smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 검수해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-preview-card-match-badge-exact-text-smoke-tightening-verification.md`가 다음 exact slice로 넘긴 preview-card tooltip exact-path tightening이 실제로 닫혔으므로, stale handoff를 갱신하고 다음 단일 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`에는 `searchFolderRelBudgetPath`, `searchFolderRelMemoPath` 정의 2건과 exact `title` assertion 8건이 실제로 존재합니다.
  - stale `toHaveAttribute("title", /.*\\/...)` regex assertion은 현재 0건입니다.
- latest `/work`가 절대 경로가 아니라 상대 경로 상수로 바꾼 판단도 current shipped behavior와 맞습니다.
  - `app/static/app.js`의 response detail / transcript preview renderer는 둘 다 `nameEl.title = sr.path || ""`를 그대로 사용합니다.
  - `core/agent_loop.py`의 uploaded-folder search path는 `FileSearchResult(path=relative_path, ...)`로 만들어지므로, folder picker 시나리오의 tooltip 값은 `picked-search-folder/...` 형태의 상대 경로가 맞습니다.
- rerun 결과도 latest `/work`와 일치합니다.
  - `git diff -- e2e/tests/web-smoke.spec.mjs`는 현재 clean입니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 통과했습니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (2.6m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 어긋나지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 여전히 document-search browser smoke hardening을 current MVP 내부의 QA 축으로 다루고 있습니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`의 preview-card / `selected-copy` 설명도 current tree와 충돌하지 않습니다.
- same-day latest `/verify`는 사실관계 자체는 맞지만, 거기서 넘긴 next slice는 latest `/work`가 실제로 닫았으므로 handoff로서는 stale입니다.
- 다음 exact slice는 `document-search selected-source-path copy exact-path-list smoke tightening`으로 갱신했습니다.
  - current search-only smoke는 `selected-copy` click 이후 clipboard를 `expect(clipboardText).toContain("budget-plan.md")`로만 확인합니다.
  - current UI는 `copyTextValue(selectedText.textContent, ...)`를 쓰고, `renderSelected()`는 selected path list를 줄바꿈으로 join하므로 copied text는 exact relative path list로 안정적으로 결정됩니다.
  - 따라서 현재 smoke는 두 번째 경로 누락이나 예상 외 prefix/suffix가 생겨도 통과할 수 있고, exact clipboard list로 잠그는 것이 다음 가장 작은 user-visible current-risk reduction입니다.

## 검증
- `sed -n '1,260p' work/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-exact-path-smoke-tightening.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-preview-card-match-badge-exact-text-smoke-tightening-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,240p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -n "searchFolderRelBudgetPath|searchFolderRelMemoPath" e2e/tests/web-smoke.spec.mjs`
- `rg -n 'toHaveAttribute\\("title", /\\.\\*\\\\/' e2e/tests/web-smoke.spec.mjs`
- `sed -n '184,284p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '1000,1215p' app/static/app.js`
- `sed -n '740,800p' core/agent_loop.py`
- `rg -n 'selected-copy|clipboardText|budget-plan\\.md|memo\\.md' e2e/tests/web-smoke.spec.mjs`
- `sed -n '256,269p' e2e/tests/web-smoke.spec.mjs`
- `make e2e-test`
  - `17 passed (2.6m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server 로직 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 정리하거나 되돌리면 안 됩니다.
- preview-card tooltip exact-path smoke tightening은 now aligned입니다.
- 다만 current `selected-copy` smoke는 clipboard 전체 path list를 exact하게 잠그지 못합니다. 다음 handoff는 그 한 슬라이스만 구현하도록 좁혔습니다.
