## 변경 파일
- `verify/4/4/2026-04-04-aggregate-trigger-planning-target-exact-text-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/4/2026-04-04-aggregate-trigger-planning-target-exact-text-smoke-tightening.md`의 aggregate trigger planning-target exact-text smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest 기존 `/verify`인 `verify/4/4/2026-04-04-aggregate-trigger-section-label-exact-text-smoke-tightening-verification.md`는 이전 section-label slice를 기준으로 다음 handoff를 남긴 상태였으므로, persistent verification truth와 다음 Claude 실행 슬롯을 현재 latest `/work` 기준으로 갱신해야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:747`은 now `aggregateTriggerBox.getByTestId("aggregate-trigger-item").locator(".history-item-summary").filter({ hasText: "계획 타깃" })` 기준 exact-text assertion `toHaveText("계획 타깃 eligible_for_reviewed_memory_draft_planning_only")`를 사용합니다.
  - current shipped runtime은 `app/static/app.js:2566-2570`에서 planning target line을 별도 `div.history-item-summary`로 렌더링하고, 문자열도 `계획 타깃 ${planningTargetLabel}`로 고정 조합합니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, `git show --stat --oneline 3a6bcec -- e2e/tests/web-smoke.spec.mjs`도 planning-target assertion 1건만 교체한 test-only commit임을 다시 확인했습니다.
  - `git branch -r --contains 3a6bcec` 결과는 `origin/main`이었습니다.
- rerun 결과도 latest `/work`와 일치합니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (2.3m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 17-scenario Playwright smoke coverage와 document-first MVP framing을 그대로 유지하고 있습니다.
  - 이번 라운드는 runtime이나 stored contract 변경이 아니라 test-only smoke tightening 1건이므로 새 문서 갭은 확인되지 않았습니다.
- dedicated exact-text로 좁힐 수 있는 aggregate trigger surface는 현재 planning-target까지 truthful하게 닫혔습니다.
  - same-session recurrence aggregate scenario에서 아직 box-level `toContainText`로 남아 있는 것은 `capability unblocked_all_required`와 `audit contract_only_not_emitted` 두 문자열뿐입니다.
  - 두 문자열은 `app/static/app.js:2547-2554`의 같은 meta `span` 안에서 `반복 N회`, `마지막 확인 ...`과 함께 결합됩니다.
  - 따라서 다음 smallest same-family follow-up은 exact-text가 아니라 `aggregate-trigger-capability-meta scoped-selector smoke tightening`으로 좁히는 편이 더 truthful합니다.
  - `capability`는 current shipped start eligibility와 직접 이어지는 문자열이라 `audit`보다 current-risk reduction 우선순위가 높습니다.

## 검증
- `sed -n '1,260p' work/4/4/2026-04-04-aggregate-trigger-planning-target-exact-text-smoke-tightening.md`
- `sed -n '1,260p' verify/4/4/2026-04-04-aggregate-trigger-section-label-exact-text-smoke-tightening-verification.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,240p' work/README.md`
- `sed -n '1,240p' verify/README.md`
- `sed -n '1,240p' .pipeline/README.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '708,890p'`
- `rg -n 'aggregateTriggerBox\\)|aggregate-trigger-|검토 메모 적용 후보|capability |audit |계획 타깃 ' e2e/tests/web-smoke.spec.mjs`
- `nl -ba app/static/app.js | sed -n '2528,2600p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -n '계획 타깃 eligible_for_reviewed_memory_draft_planning_only|planningTarget|history-item-summary' e2e/tests/web-smoke.spec.mjs app/static/app.js`
- `git show --stat --oneline 3a6bcec -- e2e/tests/web-smoke.spec.mjs`
- `git branch -r --contains 3a6bcec`
- `make e2e-test`
  - `17 passed (2.3m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server runtime 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 건드리거나 정리하면 안 됩니다.
- aggregate trigger same-session scenario에는 `capability`와 `audit`가 아직 box-level `toContainText`로 남아 있습니다.
- 다만 두 문자열은 recurrence count 및 relative timestamp와 같은 composite meta span 안에 있으므로, 다음 슬라이스에서 exact-text까지 무리하게 밀어붙이면 timing/wording flake를 키울 수 있습니다. 이번 handoff는 먼저 `capability`를 span selector로 좁히는 current-risk reduction 1건만 요구합니다.
