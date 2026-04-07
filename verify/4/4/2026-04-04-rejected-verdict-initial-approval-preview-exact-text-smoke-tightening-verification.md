## 변경 파일
- `verify/4/4/2026-04-04-rejected-verdict-initial-approval-preview-exact-text-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/4/2026-04-04-rejected-verdict-initial-approval-preview-exact-text-smoke-tightening.md`의 rejected-verdict initial approval-preview exact-text smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest `/verify`인 `verify/4/4/2026-04-04-corrected-save-initial-approval-preview-exact-text-smoke-tightening-verification.md`는 next slice를 rejected-verdict initial `#approval-preview` exact-text로 넘긴 상태였으므로, persistent verification truth와 다음 Claude 실행 슬롯을 이번 latest `/work` 기준으로 갱신해야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 코드 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:379-386`은 rejected-verdict scenario용 `expectedNotePreview`를 local fixture and mock note-body contract로 구성하고, `e2e/tests/web-smoke.spec.mjs:387`에서 initial `#approval-preview`를 `toHaveText(expectedNotePreview)`로 검증합니다.
  - same scenario는 `e2e/tests/web-smoke.spec.mjs:389`에서 full preview snapshot을 읽고, later immutability를 `e2e/tests/web-smoke.spec.mjs:409`에서 `toHaveText(originalApprovalPreview)`로 다시 고정합니다.
  - current shipped template은 `app/templates/index.html:323`에서 dedicated `<pre id="approval-preview">`를 제공하고, runtime은 `app/static/app.js:3074`에서 `approval.preview_markdown`을 `approvalPreview.textContent`로 직접 렌더링합니다.
  - expected note-body shape itself remains deterministic in `model_adapter/mock.py:41-55` via `create_summary_note`.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, `git show --stat --oneline 3eda111 -- e2e/tests/web-smoke.spec.mjs`도 rejected-verdict initial preview assertion 1건을 exact-text contract로 넓힌 test-only commit임을 다시 확인했습니다.
  - `git branch -r --contains 3eda111` 결과는 `origin/main`이었습니다.
- rerun 결과도 latest `/work`와 일치합니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (3.7m)`로 종료되었습니다.
  - target scenario인 `내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다`도 same rerun에서 통과했습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 17-scenario Playwright smoke coverage와 document-first MVP framing을 그대로 유지하고 있습니다.
  - 이번 라운드는 runtime이나 stored contract 변경이 아니라 test-only smoke tightening 1건이므로 새 문서 갭은 확인되지 않았습니다.
- latest `/work`의 supplementary rationale 중 Python simulation 부분은 이번 verification round에서 독립 재실행하지 않았습니다.
  - 다만 current spec의 `expectedNotePreview`, `model_adapter/mock.py:41-55`의 note-body format, 그리고 `make e2e-test` full pass는 그 exact expected string이 현재 shipped mock contract와 충돌하지 않음을 보여 줍니다.
- approval-preview family의 meaningful positive exact-text coverage는 now 닫혔습니다.
  - `e2e/tests/web-smoke.spec.mjs:387`, `e2e/tests/web-smoke.spec.mjs:462`, `e2e/tests/web-smoke.spec.mjs:469`, `e2e/tests/web-smoke.spec.mjs:501`은 모두 positive exact-text입니다.
  - remaining `e2e/tests/web-smoke.spec.mjs:470` negative partial check는 `e2e/tests/web-smoke.spec.mjs:469` exact positive check가 same stale snapshot branch를 이미 더 강하게 고정하므로 후순위입니다.
- next exact slice는 `rejected-verdict-initial-content-verdict-status exact-text smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs:377-378`는 same rejected-verdict scenario의 initial `#response-content-verdict-status`를 두 개의 partial clause로만 확인합니다.
  - current runtime은 `app/static/app.js:1792-1799`에서 same status를 deterministic `statusParts.join(" ")`로 조합하고, `app/templates/index.html:179`는 dedicated `#response-content-verdict-status` slot을 제공합니다.
  - current approval-card-open branch에서 joined text는 `저장 승인 거절과는 별도입니다. 이 버튼을 누르면 grounded-brief 원문 응답에 내용 거절을 즉시 기록합니다. 이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.`로 고정됩니다.
  - 따라서 same scenario initial status 1건을 exact-text로 바꾸는 것이 가장 작은 다음 current-risk reduction입니다.

## 검증
- `sed -n '1,240p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/4/2026-04-04-rejected-verdict-initial-approval-preview-exact-text-smoke-tightening.md`
- `sed -n '1,260p' verify/4/4/2026-04-04-corrected-save-initial-approval-preview-exact-text-smoke-tightening-verification.md`
- `git status --short`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '360,410p'`
- `rg -n 'expectedNotePreview|#approval-preview|middleSignal|originalApprovalPreview' e2e/tests/web-smoke.spec.mjs`
- `nl -ba model_adapter/mock.py | sed -n '41,55p'`
- `git log --oneline -- e2e/tests/web-smoke.spec.mjs | head -n 6`
- `sed -n '1,240p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `git show --stat --oneline 3eda111 -- e2e/tests/web-smoke.spec.mjs`
- `git branch -r --contains 3eda111`
- `rg -n '#approval-preview' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`
- `nl -ba app/templates/index.html | sed -n '323,323p'`
- `nl -ba app/static/app.js | sed -n '3073,3075p'`
- `rg -n '저장 승인 거절과는 별도입니다\\.|이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다\\.|이 답변 내용을 거절로 기록했습니다\\.|거절 메모를 기록했습니다\\. 내용 거절 판정은 그대로 유지됩니다\\.' e2e/tests/web-smoke.spec.mjs app/static/app.js core tests`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '371,406p'`
- `rg -n 'response-content-verdict-status|response-content-reason-status|내용 거절' app/static/app.js app/templates/index.html core`
- `nl -ba app/static/app.js | sed -n '1788,1798p'`
- `nl -ba app/static/app.js | sed -n '1766,1778p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '394,399p'`
- `nl -ba app/static/app.js | sed -n '1792,1803p'`
- `nl -ba app/templates/index.html | sed -n '177,180p'`
- `rg -n 'response-content-verdict-status' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`
- `make e2e-test`
  - `17 passed (3.7m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server runtime 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 건드리거나 정리하면 안 됩니다.
- latest `/work`의 Python simulation rationale는 이번 verification round에서 독립 재실행하지 않았습니다. 현재 verification truth는 current code inspection과 `make e2e-test` rerun에 기반합니다.
- remaining `e2e/tests/web-smoke.spec.mjs:470` negative partial check는 still 존재하지만, `e2e/tests/web-smoke.spec.mjs:469` exact positive check가 same stale snapshot branch를 이미 더 강하게 커버하므로 후순위입니다.
