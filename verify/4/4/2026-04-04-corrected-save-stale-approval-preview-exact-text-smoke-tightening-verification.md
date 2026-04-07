## 변경 파일
- `verify/4/4/2026-04-04-corrected-save-stale-approval-preview-exact-text-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/4/2026-04-04-corrected-save-stale-approval-preview-exact-text-smoke-tightening.md`의 corrected-save stale approval-preview exact-text smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest 기존 `/verify`인 `verify/4/4/2026-04-04-corrected-save-long-history-approval-preview-exact-text-smoke-tightening-verification.md`가 next slice를 stale `#approval-preview` exact-text로 넘긴 상태였으므로, persistent verification truth와 다음 Claude 실행 슬롯을 이번 latest `/work` 기준으로 갱신해야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:461`은 first bridge scenario의 stale `#approval-preview`를 `toHaveText(correctedTextA)`로 검증합니다.
  - same scenario는 `e2e/tests/web-smoke.spec.mjs:424`에서 fixed multiline `correctedTextA = "수정본 A입니다.\n핵심만 남겼습니다."`를 정의합니다.
  - current shipped template은 `app/templates/index.html:323`에서 dedicated `<pre id="approval-preview">`를 그대로 제공합니다.
  - current shipped runtime은 `app/static/app.js:3074`에서 `approval.preview_markdown`을 `approvalPreview.textContent`로 직접 렌더링합니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, `git show --stat --oneline 7895e86 -- e2e/tests/web-smoke.spec.mjs`도 stale preview assertion 1건을 exact-text 1건으로 바꾼 test-only commit임을 다시 확인했습니다.
  - `git branch -r --contains 7895e86` 결과는 `origin/main`이었습니다.
- rerun 결과도 latest `/work`와 충돌하지 않습니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (3.7m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 17-scenario Playwright smoke coverage와 document-first MVP framing을 그대로 유지하고 있습니다.
  - 이번 라운드는 runtime이나 stored contract 변경이 아니라 test-only smoke tightening 1건이므로 새 문서 갭은 확인되지 않았습니다.
- corrected-save approval-preview family는 stale snapshot branch까지 now exact-text로 닫혔습니다.
  - `e2e/tests/web-smoke.spec.mjs:461`은 now exact-text입니다.
  - remaining same-family preview assertions are `e2e/tests/web-smoke.spec.mjs:454`와 `e2e/tests/web-smoke.spec.mjs:462`입니다.
- next exact slice는 `corrected-save-initial-approval-preview exact-text smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs:454`는 same first bridge scenario의 initial `#approval-preview`를 아직 `toContainText("수정본 A입니다.")`로만 확인합니다.
  - same scenario는 `e2e/tests/web-smoke.spec.mjs:424`의 fixed multiline `correctedTextA`를 그대로 재사용할 수 있고, `app/static/app.js:3074`는 preview를 `textContent`로 직접 렌더링합니다.
  - `e2e/tests/web-smoke.spec.mjs:461`이 이미 stale preview를 `toHaveText(correctedTextA)`로 고정했기 때문에 `e2e/tests/web-smoke.spec.mjs:462`의 negative partial check는 우선순위가 낮아졌습니다.
  - 따라서 initial positive preview 1건을 `toHaveText(correctedTextA)`로 바꾸는 것이 가장 작은 남은 same-family 후속입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/4/2026-04-04-corrected-save-stale-approval-preview-exact-text-smoke-tightening.md`
- `sed -n '1,260p' verify/4/4/2026-04-04-corrected-save-long-history-approval-preview-exact-text-smoke-tightening-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git show --stat --oneline 7895e86 -- e2e/tests/web-smoke.spec.mjs`
- `git branch -r --contains 7895e86`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `sed -n '454,462p' e2e/tests/web-smoke.spec.mjs`
- `rg -n '#approval-preview|수정본 A입니다\\.|핵심만 남겼습니다\\.|수정본 B입니다\\.|다시 손봤습니다\\.' e2e/tests/web-smoke.spec.mjs app/static/app.js app/templates/index.html`
- `nl -ba app/templates/index.html | sed -n '323,323p'`
- `nl -ba app/static/app.js | sed -n '3073,3075p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '452,462p'`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `ls -1 verify/4/4 | tail -n 8`
- `make e2e-test`
  - `17 passed (3.7m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server runtime 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 건드리거나 정리하면 안 됩니다.
- corrected-save approval-preview family에는 `e2e/tests/web-smoke.spec.mjs:454`와 `e2e/tests/web-smoke.spec.mjs:462`가 아직 남아 있습니다.
- 이번 handoff는 exact-text coverage가 아직 없는 initial positive preview `e2e/tests/web-smoke.spec.mjs:454` 한 건만 좁히도록 제한했습니다. negative partial check `e2e/tests/web-smoke.spec.mjs:462`는 `e2e/tests/web-smoke.spec.mjs:461` exact-text가 이미 stale snapshot branch를 강하게 고정하므로 후순위입니다.
