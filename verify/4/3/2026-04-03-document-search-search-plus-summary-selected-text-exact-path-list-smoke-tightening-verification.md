## 변경 파일
- `verify/4/3/2026-04-03-document-search-search-plus-summary-selected-text-exact-path-list-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-search-plus-summary-selected-text-exact-path-list-smoke-tightening.md`의 test-only smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 검수해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-selected-copy-exact-path-list-smoke-tightening-verification.md`가 다음 exact slice로 넘긴 search-plus-summary `#selected-text` exact-path-list tightening이 실제로 닫혔으므로, stale handoff를 갱신하고 다음 단일 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 folder-search(search-plus-summary) 시나리오 `#selected-text` assertion은 현재 `toHaveText(searchFolderRelBudgetPath + "\n" + searchFolderRelMemoPath)`로 반영되어 있습니다.
  - `#selected-text` assertion은 현재 2건이며, line 202는 exact, line 260은 아직 `toContainText("budget-plan.md")`입니다.
- latest `/work`의 exact path list 판단도 current shipped behavior와 맞습니다.
  - `app/static/app.js`의 `renderSelected()`는 `selectedText.textContent = items.join("\n")`를 사용합니다.
  - folder-search summary path는 `core/agent_loop.py`에서 `selected_source_paths=[item.path for item in selected_results]`로 내려오므로, visible selected path panel도 exact multiline relative path list로 안정적으로 결정됩니다.
- rerun 결과도 latest `/work`와 일치합니다.
  - `git diff -- e2e/tests/web-smoke.spec.mjs`는 현재 clean입니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 통과했습니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (2.6m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 current MVP 내부의 document-search browser smoke hardening을 다루고 있습니다.
  - 이번 라운드는 docs wording이 아니라 assertion exactness tightening이므로, root docs와의 truth mismatch는 새로 생기지 않았습니다.
- same-day latest `/verify`는 사실관계 자체는 맞지만, 거기서 넘긴 next slice는 latest `/work`가 실제로 닫았으므로 handoff로서는 stale입니다.
- 다음 exact slice는 `document-search search-only selected-text exact-path-list smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs`의 `#selected-text` assertion 2건 중 search-plus-summary line 202는 now exact이지만, search-only line 260은 아직 `toContainText("budget-plan.md")`로만 확인합니다.
  - search-only 시나리오의 clipboard `toBe()` assertion이 동일 DOM text를 간접적으로 잠그고 있기는 하지만, visible selected path panel 자체는 아직 direct exactness로 잠겨 있지 않습니다.
  - 같은 helper(`renderSelected()`), 같은 상수(`searchFolderRelBudgetPath`, `searchFolderRelMemoPath`), 같은 파일에서 1줄 tightening만 더 하면 되므로, 새 quality axis로 넘어가기보다 이 same-family current-risk reduction 1건을 먼저 닫는 편이 더 좁고 truthful합니다.

## 검증
- `sed -n '1,260p' work/4/3/2026-04-03-document-search-search-plus-summary-selected-text-exact-path-list-smoke-tightening.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-selected-copy-exact-path-list-smoke-tightening-verification.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,240p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -n '#selected-text' e2e/tests/web-smoke.spec.mjs`
- `rg -n 'toContainText\\("budget-plan\\.md"\\)' e2e/tests/web-smoke.spec.mjs`
- `sed -n '184,290p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '1168,1178p' app/static/app.js`
- `sed -n '1632,1644p' app/static/app.js`
- `make e2e-test`
  - `17 passed (2.6m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server 로직 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 정리하거나 되돌리면 안 됩니다.
- search-plus-summary `#selected-text` exact path list smoke tightening은 now aligned입니다.
- 다만 search-only visible `#selected-text` panel은 아직 direct exact path list assertion으로 잠겨 있지 않습니다. 다음 handoff는 그 한 슬라이스만 구현하도록 좁혔습니다.
