## 변경 파일
- `verify/4/4/2026-04-04-review-queue-item-statement-exact-text-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/4/2026-04-04-review-queue-item-statement-exact-text-smoke-tightening.md`의 review queue item statement exact-text smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest 기존 `/verify`인 `verify/4/4/2026-04-04-review-queue-status-hint-exact-text-smoke-tightening-verification.md`는 review queue family를 item statement follow-up으로 넘긴 상태였으므로, persistent verification truth와 다음 Claude 실행 슬롯을 이번 latest `/work` 기준으로 갱신해야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:638`은 now first visible review queue rendering에서 `reviewQueueBox.getByTestId("review-queue-item").locator("strong").first()` 기준 exact-text assertion `toHaveText("explicit rewrite correction recorded for this grounded brief")`를 사용합니다.
  - current shipped runtime은 `app/static/app.js:2440`에서 review queue card에 `data-testid="review-queue-item"`를 부여하고, `app/static/app.js:2447-2449`에서 dedicated `strong` 요소에 `item.statement || item.candidate_family || "검토 후보"`를 직접 렌더링합니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, `git show --stat --oneline 733f647 -- e2e/tests/web-smoke.spec.mjs`도 item statement assertion 1건만 교체한 test-only commit임을 다시 확인했습니다.
  - `git branch -r --contains 733f647` 결과는 `origin/main`이었습니다.
- rerun 결과도 latest `/work`와 일치합니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (2.4m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 17-scenario Playwright smoke coverage와 document-first MVP framing을 그대로 유지하고 있습니다.
  - 이번 라운드는 runtime이나 stored contract 변경이 아니라 test-only smoke tightening 1건이므로 새 문서 갭은 확인되지 않았습니다.
- next exact slice는 `review-queue-basis-meta scoped-selector smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs:639`는 first visible review queue rendering에서 `기준 명시 확인`을 아직 `reviewQueueBox` 전체 `toContainText`로만 확인합니다.
  - current shipped runtime은 `app/static/app.js:2451-2456`에서 review queue meta를 dedicated `.history-item-title span`에 `기준 ... · 상태 ... · 업데이트 ...` 형식으로 렌더링합니다.
  - same family의 남은 broad checks 중 basis는 line 순서상 먼저이고, dynamic `업데이트 ...` 때문에 full exact-text보다 selector-scoped `toContainText("기준 명시 확인")`가 가장 truthful한 다음 current-risk reduction입니다. status는 같은 span의 후속 1건으로 남겨 두는 편이 더 좁습니다.

## 검증
- `sed -n '1,260p' work/4/4/2026-04-04-review-queue-item-statement-exact-text-smoke-tightening.md`
- `sed -n '1,260p' verify/4/4/2026-04-04-review-queue-status-hint-exact-text-smoke-tightening-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '636,644p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '740,748p'`
- `nl -ba app/static/app.js | sed -n '2438,2458p'`
- `rg -n 'explicit rewrite correction recorded for this grounded brief|기준 명시 확인|상태 검토 대기|review-queue-item|history-item-title|history-item-summary|업데이트' e2e/tests/web-smoke.spec.mjs app/static/app.js`
- `rg -n '기준 명시 확인|상태 검토 대기|history-item-title span|review-queue-item' e2e/tests/web-smoke.spec.mjs app/static/app.js`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `git show --stat --oneline 733f647 -- e2e/tests/web-smoke.spec.mjs`
- `git branch -r --contains 733f647`
- `make e2e-test`
  - `17 passed (2.4m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server runtime 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 건드리거나 정리하면 안 됩니다.
- review queue family에서는 item statement exact-text는 닫혔지만, first visible review queue rendering의 meta basis/status checks는 `e2e/tests/web-smoke.spec.mjs:639-640`에 아직 box-level로 남아 있습니다.
- 이번 handoff는 그중 basis 1건만 selector-scoped로 좁히도록 제한했습니다. basis와 status를 한 라운드에 같이 바꾸면 shared dynamic meta span 때문에 test-only smoke tightening 범위를 불필요하게 확장하게 됩니다.
