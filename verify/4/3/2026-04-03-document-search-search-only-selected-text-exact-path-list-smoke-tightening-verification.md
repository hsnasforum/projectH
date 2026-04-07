## 변경 파일
- `verify/4/3/2026-04-03-document-search-search-only-selected-text-exact-path-list-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-search-only-selected-text-exact-path-list-smoke-tightening.md`의 test-only smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 검수해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-search-plus-summary-selected-text-exact-path-list-smoke-tightening-verification.md`가 다음 exact slice로 넘긴 search-only `#selected-text` exact-path-list tightening이 실제로 닫혔으므로, stale handoff를 갱신하고 다음 단일 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 `#selected-text` assertion은 현재 line 202, line 260 모두 `toHaveText(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath)`로 반영되어 있습니다.
  - stale `toContainText("budget-plan.md")`는 현재 `e2e/tests/web-smoke.spec.mjs`에서 0건입니다.
- latest `/work`의 exact path list 판단도 current shipped behavior와 맞습니다.
  - `app/static/app.js`의 `renderSelected()`는 현재 `selectedText.textContent = items.join("\n")`를 사용하므로, selected path panel contract은 exact multiline text입니다.
- rerun 결과도 latest `/work`와 일치합니다.
  - `git diff -- e2e/tests/web-smoke.spec.mjs`는 현재 clean입니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 통과했습니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (2.5m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 current MVP 내부의 document-search browser smoke hardening을 다루고 있습니다.
  - 이번 라운드는 production behavior나 docs wording이 아니라 Playwright assertion exactness tightening만 다루므로, root docs와의 새 truth mismatch는 확인되지 않았습니다.
- 다음 exact slice는 `document-search selected-copy success-notice exact-text smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs`의 search-only 시나리오는 selected-copy click 뒤 `await expect(page.locator("#notice-box")).toContainText("선택 경로를 복사했습니다.");`로만 확인합니다.
  - 반면 current shipped UI는 `app/static/app.js`의 `renderNotice()`에서 `noticeBox.textContent = message`로 exact text를 렌더링하고, 같은 파일의 `selectedCopyButton` click handler는 고정 success string `"선택 경로를 복사했습니다."`를 전달합니다.
  - 따라서 현재 family를 벗어나 새 quality axis로 넘어가기보다, same-family current-risk reduction 1건으로 selected-copy success notice만 `toHaveText()`로 잠그는 편이 더 좁고 truthful합니다.

## 검증
- `sed -n '1,260p' work/4/3/2026-04-03-document-search-search-only-selected-text-exact-path-list-smoke-tightening.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-search-plus-summary-selected-text-exact-path-list-smoke-tightening-verification.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,260p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -n '#selected-text|searchFolderRelBudgetPath|searchFolderRelMemoPath' e2e/tests/web-smoke.spec.mjs`
- `rg -n 'toContainText\\("budget-plan\\.md"\\)' e2e/tests/web-smoke.spec.mjs`
- `rg -n '선택 경로를 복사했습니다\\.|본문을 복사했습니다\\.' e2e/tests/web-smoke.spec.mjs`
- `rg -n 'responseCopyTextButton|selectedCopyButton|copyTextValue\\(' app/static/app.js`
- `sed -n '184,290p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '1160,1185p' app/static/app.js`
- `sed -n '3196,3225p' app/static/app.js`
- `sed -n '3400,3455p' app/static/app.js`
- `make e2e-test`
  - `17 passed (2.5m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server 로직 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, `watcher_core.py`, `work/README.md`, `verify/README.md`, pipeline 스크립트류 등 현재 슬라이스와 무관한 dirty 파일을 정리하거나 되돌리면 안 됩니다.
- search-plus-summary와 search-only의 `#selected-text` exact path list smoke tightening은 now aligned입니다.
- 다만 selected-copy success notice는 아직 direct exact-text assertion으로 잠겨 있지 않습니다. 다음 handoff는 그 한 슬라이스만 구현하도록 좁혔습니다.
