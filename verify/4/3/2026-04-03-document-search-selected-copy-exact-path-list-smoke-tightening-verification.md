## 변경 파일
- `verify/4/3/2026-04-03-document-search-selected-copy-exact-path-list-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-selected-copy-exact-path-list-smoke-tightening.md`의 test-only smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 검수해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-exact-path-smoke-tightening-verification.md`가 다음 exact slice로 넘긴 selected-copy exact-path-list tightening이 실제로 닫혔으므로, stale handoff를 갱신하고 다음 단일 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 search-only 시나리오 clipboard assertion은 현재 `expect(clipboardText).toBe(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath)`로 실제 반영되어 있습니다.
  - stale `expect(clipboardText).toContain("budget-plan.md")` assertion은 현재 0건입니다.
- latest `/work`의 exact path list 판단도 current shipped behavior와 맞습니다.
  - `app/static/app.js`의 `renderSelected()`는 `selectedText.textContent = items.join("\n")`를 사용합니다.
  - 같은 파일의 click handler는 `copyTextValue(selectedText.textContent || "", "선택 경로를 복사했습니다.")`를 호출하므로, clipboard 값은 selected path panel의 exact multiline text와 동일합니다.
- rerun 결과도 latest `/work`와 일치합니다.
  - `git diff -- e2e/tests/web-smoke.spec.mjs`는 현재 clean입니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 통과했습니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (2.5m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 여전히 current MVP 내부의 document-search browser smoke hardening을 다루고 있습니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`의 `selected-copy` 설명은 coverage 존재 여부를 서술할 뿐 exact clipboard string까지는 약속하지 않으므로, 이번 tightening과 충돌하지 않습니다.
- same-day latest `/verify`는 사실관계 자체는 맞지만, 거기서 넘긴 next slice는 latest `/work`가 실제로 닫았으므로 handoff로서는 stale입니다.
- 다음 exact slice는 `document-search search-plus-summary selected-text exact-path-list smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs`에는 `#selected-text` assertion이 2곳 있는데, search-only line은 now exact clipboard assertion으로 동일 DOM text가 간접적으로 잠겨 있습니다.
  - 반면 folder-search(search-plus-summary) 시나리오는 아직 `await expect(page.locator("#selected-text")).toContainText("budget-plan.md");`로만 확인하므로, 두 번째 경로 누락이나 순서 오류가 생겨도 통과할 수 있습니다.
  - current UI는 같은 `renderSelected()` helper로 exact multiline path list를 렌더링하고, folder-search scenario는 이미 quick-meta/transcript meta에서 `출처 2개`, preview panel에서 both-card order를 확인하므로, 다음 가장 작은 current-risk reduction은 folder-search `#selected-text`만 exact relative path list로 잠그는 것입니다.

## 검증
- `sed -n '1,260p' work/4/3/2026-04-03-document-search-selected-copy-exact-path-list-smoke-tightening.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-preview-card-full-path-tooltip-exact-path-smoke-tightening-verification.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,240p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -n 'expect\\(clipboardText\\)\\.toBe\\(|expect\\(clipboardText\\)\\.toContain\\("budget-plan\\.md"\\)' e2e/tests/web-smoke.spec.mjs`
- `rg -n 'selected-text.*budget-plan\\.md|#selected-text' e2e/tests/web-smoke.spec.mjs`
- `sed -n '235,290p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '1168,1178p' app/static/app.js`
- `sed -n '1630,1685p' app/static/app.js`
- `sed -n '7840,7858p' core/agent_loop.py`
- `sed -n '7988,8007p' core/agent_loop.py`
- `make e2e-test`
  - `17 passed (2.5m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server 로직 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 정리하거나 되돌리면 안 됩니다.
- selected-copy clipboard exact path list smoke tightening은 now aligned입니다.
- 다만 folder-search(search-plus-summary) `#selected-text` visible panel은 아직 exact path list로 잠겨 있지 않습니다. 다음 handoff는 그 한 슬라이스만 구현하도록 좁혔습니다.
