## 변경 파일
- `verify/4/4/2026-04-04-corrected-save-initial-approval-preview-exact-text-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/4/2026-04-04-corrected-save-initial-approval-preview-exact-text-smoke-tightening.md`의 corrected-save initial approval-preview exact-text smoke tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest `/verify`인 `verify/4/4/2026-04-04-corrected-save-stale-approval-preview-exact-text-smoke-tightening-verification.md`는 next slice를 initial `#approval-preview` exact-text로 넘긴 상태였으므로, persistent verification truth와 다음 Claude 실행 슬롯을 이번 latest `/work` 기준으로 갱신해야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 코드 주장은 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:454`는 now first bridge scenario의 initial `#approval-preview`를 `toHaveText(correctedTextA)`로 검증합니다.
  - 같은 scenario는 `e2e/tests/web-smoke.spec.mjs:424`에서 fixed multiline `correctedTextA = "수정본 A입니다.\n핵심만 남겼습니다."`를 정의하고, stale snapshot branch도 `e2e/tests/web-smoke.spec.mjs:461`에서 same constant로 exact-text를 유지합니다.
  - long-history branch도 `e2e/tests/web-smoke.spec.mjs:493`에서 이미 `toHaveText(correctedTextA)`로 고정돼 있습니다.
  - current shipped template은 `app/templates/index.html:323`에서 dedicated `<pre id="approval-preview">`를 그대로 제공하고, runtime은 `app/static/app.js:3074`에서 `approval.preview_markdown`을 `approvalPreview.textContent`로 직접 렌더링합니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, `git show --stat --oneline 047f1c0 -- e2e/tests/web-smoke.spec.mjs`도 initial preview assertion 1건만 exact-text 1건으로 바꾼 test-only commit임을 다시 확인했습니다.
  - `git branch -r --contains 047f1c0` 결과는 `origin/main`이었습니다.
- rerun 결과는 latest `/work`보다 더 깨끗한 current truth를 보여 줍니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (3.6m)`로 종료되었습니다.
  - latest `/work`에 적힌 `16 passed, 1 failed`와 `test #7` pre-existing failure는 current rerun에서 재현되지 않았습니다. 따라서 그 failure description은 current truth라기보다 일시적 또는 환경성 결과였던 것으로 보입니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 17-scenario Playwright smoke coverage와 document-first MVP framing을 그대로 유지하고 있습니다.
  - 이번 라운드는 runtime이나 stored contract 변경이 아니라 test-only smoke tightening 1건이므로 새 문서 갭은 확인되지 않았습니다.
- corrected-save approval-preview family는 meaningful positive exact-text coverage가 now 닫혔습니다.
  - `e2e/tests/web-smoke.spec.mjs:454`, `e2e/tests/web-smoke.spec.mjs:461`, `e2e/tests/web-smoke.spec.mjs:493`은 모두 `toHaveText(correctedTextA)`입니다.
  - remaining corrected-save `e2e/tests/web-smoke.spec.mjs:462` negative partial check는 `e2e/tests/web-smoke.spec.mjs:461` exact positive check가 이미 same stale snapshot branch를 더 강하게 고정하므로 우선순위가 낮습니다.
- next exact slice는 `rejected-verdict-initial-approval-preview exact-text smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs:379`는 rejected-verdict scenario의 initial original-draft `#approval-preview`를 아직 `toContainText("중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다.")`로만 확인합니다.
  - same scenario는 `e2e/tests/web-smoke.spec.mjs:381`에서 full preview snapshot을 읽어 later immutability를 `e2e/tests/web-smoke.spec.mjs:401`에서 exact-text로 다시 확인합니다.
  - file top-level constants `e2e/tests/web-smoke.spec.mjs:9`의 `longFixturePath`와 `e2e/tests/web-smoke.spec.mjs:21`의 `middleSignal`, 그리고 `model_adapter/mock.py:41-55`의 deterministic note-body generation을 함께 쓰면 initial preview 1건도 exact-text contract로 좁힐 수 있습니다.
  - 따라서 current approval-preview family에서 가장 작은 다음 current-risk reduction은 rejected-verdict scenario initial positive preview 1건을 exact-text로 강화하는 것입니다.

## 검증
- `sed -n '1,240p' AGENTS.md`
- `sed -n '1,240p' work/README.md`
- `sed -n '1,240p' verify/README.md`
- `sed -n '1,240p' .pipeline/README.md`
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/4/2026-04-04-corrected-save-initial-approval-preview-exact-text-smoke-tightening.md`
- `sed -n '1,260p' verify/4/4/2026-04-04-corrected-save-stale-approval-preview-exact-text-smoke-tightening-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '452,462p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -n '#approval-preview|수정본 A입니다\\.|핵심만 남겼습니다\\.|수정본 B입니다\\.|다시 손봤습니다\\.' e2e/tests/web-smoke.spec.mjs app/static/app.js app/templates/index.html`
- `git log --oneline -- e2e/tests/web-smoke.spec.mjs | head -n 5`
- `git show --stat --oneline 047f1c0 -- e2e/tests/web-smoke.spec.mjs`
- `git branch -r --contains 047f1c0`
- `curl --max-time 2 -I http://127.0.0.1:8879/`
- `sed -n '327,421p' e2e/tests/web-smoke.spec.mjs`
- `rg -n '중간 섹션 핵심 결정은 승인 기반 저장을 유지하는 것입니다\\.|grounded brief|저장 승인' -g '*.py' -g '*.json' -g '*.md' app core tests model_adapter storage tools`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `sed -n '1,140p' e2e/tests/web-smoke.spec.mjs`
- `nl -ba model_adapter/mock.py | sed -n '35,55p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '360,401p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1,25p'`
- `make e2e-test`
  - `17 passed (3.6m)`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server runtime 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 건드리거나 정리하면 안 됩니다.
- latest `/work`의 `16 passed, 1 failed` 서술은 current rerun과 다릅니다. 구현 diff 자체는 맞았지만, verification truth는 now `17 passed (3.6m)` 기준으로 읽어야 합니다.
- corrected-save family의 remaining negative partial check `e2e/tests/web-smoke.spec.mjs:462`는 still 존재하지만, `e2e/tests/web-smoke.spec.mjs:461` exact positive check가 same stale snapshot branch를 이미 더 강하게 커버하므로 후순위입니다.
