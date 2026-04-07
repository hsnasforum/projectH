## 변경 파일
- `verify/4/4/2026-04-04-aggregate-trigger-section-label-exact-text-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/4/2026-04-04-aggregate-trigger-section-label-exact-text-smoke-tightening.md`의 aggregate trigger section label exact-text smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest 기존 `/verify`인 `verify/4/4/2026-04-04-aggregate-trigger-title-exact-text-smoke-tightening-verification.md`는 이전 title slice를 기준으로 다음 handoff를 남긴 상태였으므로, persistent verification truth와 다음 Claude 실행 슬롯을 현재 latest `/work` 기준으로 갱신해야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:743`은 now `aggregateTriggerBox.locator(".sidebar-section-label")` 기준 exact-text assertion `toHaveText("검토 메모 적용 후보")`를 사용합니다.
  - current shipped template은 `app/templates/index.html:28-30`에서 `#aggregate-trigger-box` 안의 dedicated `.sidebar-section-label` 요소에 정확히 `검토 메모 적용 후보`를 렌더링합니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, `git show --stat --oneline 4b3aff2 -- e2e/tests/web-smoke.spec.mjs`도 section label assertion 1건만 교체한 test-only commit임을 다시 확인했습니다.
  - `git branch -r --contains 4b3aff2` 결과는 `origin/main`이었습니다.
- rerun 결과도 latest `/work`와 일치합니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (2.3m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 17-scenario Playwright smoke coverage와 document-first MVP framing을 그대로 유지하고 있습니다.
  - 이번 라운드는 runtime이나 stored contract 변경이 아니라 test-only smoke tightening 1건이므로 새 문서 갭은 확인되지 않았습니다.
- 다음 exact slice는 `aggregate-trigger-planning-target exact-text smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs:747`은 aggregate trigger box 전체에 대해 `계획 타깃 eligible_for_reviewed_memory_draft_planning_only`를 `toContainText`로만 확인합니다.
  - current shipped runtime은 `app/static/app.js:2566-2570`에서 planning target line을 별도 `div.history-item-summary`로 렌더링하고, 문자열도 `계획 타깃 ${planningTargetLabel}`로 고정 조합합니다.
  - 따라서 same-session recurrence aggregate scenario에서 planning-target line 자체를 exact-text로 좁히는 것이 가장 작은 same-family user-visible follow-up입니다.
  - `capability` / `audit` copy는 현재 `app/static/app.js:2547-2554`에서 recurrence count 및 relative timestamp와 한 `span`에 합쳐져 있어, 이번 다음 슬라이스보다 selector/wording 리스크가 큽니다.

## 검증
- `sed -n '1,260p' work/4/4/2026-04-04-aggregate-trigger-section-label-exact-text-smoke-tightening.md`
- `sed -n '1,260p' verify/4/4/2026-04-04-aggregate-trigger-title-exact-text-smoke-tightening-verification.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,240p' work/README.md`
- `sed -n '1,240p' verify/README.md`
- `sed -n '1,240p' .pipeline/README.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '738,752p'`
- `nl -ba app/templates/index.html | sed -n '24,34p'`
- `nl -ba app/static/app.js | sed -n '2556,2572p'`
- `rg -n '검토 메모 적용 후보|sidebar-section-label|계획 타깃 eligible_for_reviewed_memory_draft_planning_only|capability unblocked_all_required|audit contract_only_not_emitted' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `git show --stat --oneline 4b3aff2 -- e2e/tests/web-smoke.spec.mjs`
- `git branch -r --contains 4b3aff2`
- `make e2e-test`
  - `17 passed (2.3m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server runtime 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 건드리거나 정리하면 안 됩니다.
- aggregate trigger same-session scenario에는 planning-target copy, capability meta, audit meta처럼 box-level `toContainText`로 남아 있는 문자열이 아직 있습니다.
- 이번 handoff는 그중 가장 작은 전용 고정 줄인 planning-target 1건만 닫도록 제한했습니다. capability/audit meta까지 한 번에 넓히면 dynamic copy가 섞인 meta span 때문에 test-only smoke tightening 범위를 불필요하게 확장하게 됩니다.
