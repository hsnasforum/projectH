## 변경 파일
- `verify/4/4/2026-04-04-corrected-save-post-approval-approval-meta-basis-scoped-selector-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/4/2026-04-04-corrected-save-post-approval-approval-meta-basis-scoped-selector-smoke-tightening.md`의 corrected-save approval-meta basis scoped-selector tightening 주장이 current tree와 rerun 결과 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest 기존 `/verify`인 `verify/4/4/2026-04-04-corrected-save-approval-meta-new-save-explanation-scoped-selector-smoke-tightening-verification.md`가 next slice를 duplicate basis line scoped-selector로 넘긴 상태였으므로, persistent verification truth와 다음 Claude 실행 슬롯을 이번 latest `/work` 기준으로 갱신해야 했습니다.

## 핵심 변경
- latest `/work`의 핵심 code/test change는 current tree 기준으로 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:492`는 second corrected-save scenario의 duplicate approval-meta basis line을 `#approval-meta span` scoped exact-text `toHaveText(...)`로 검증합니다.
  - current shipped runtime은 `app/static/app.js:3061`에서 same basis line을 fixed string으로 push하고, `app/static/app.js:3072`에서 each meta line을 `<span>` 단위로 렌더링합니다.
  - current shipped template은 `app/templates/index.html:312`에서 dedicated `#approval-meta` container를 그대로 제공합니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, `git show --stat --oneline 568ebc1 -- e2e/tests/web-smoke.spec.mjs`도 whole-box duplicate basis assertion 1건을 span-scoped exact-text 1건으로 바꾼 test-only commit임을 다시 확인했습니다.
  - `git branch -r --contains 568ebc1` 결과는 `origin/main`이었습니다.
- 다만 latest `/work`의 `post-approval` timing wording은 current tree와 정확히 맞지 않습니다.
  - changed assertion은 `e2e/tests/web-smoke.spec.mjs:492`에 있고, 실제 `approve-button` click은 `e2e/tests/web-smoke.spec.mjs:495`에서 발생합니다.
  - 따라서 이 assertion은 approval 이후가 아니라 approval card가 열린 직후 duplicate basis line을 검증하는 위치입니다.
- rerun 결과도 latest `/work`의 test outcome 주장과 일치합니다.
  - `make e2e-test`를 다시 실행했고 `17 passed (3.3m)`로 종료되었습니다.
- 문서 재대조 결과도 current truth와 충돌하지 않습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 17-scenario Playwright smoke coverage와 document-first MVP framing을 그대로 유지하고 있습니다.
  - 이번 라운드는 runtime이나 stored contract 변경이 아니라 test-only smoke tightening 1건이므로 새 문서 갭은 확인되지 않았습니다.
- corrected-save approval-meta positive selector family는 이번 라운드로 닫혔습니다.
  - `e2e/tests/web-smoke.spec.mjs:450-452`와 `e2e/tests/web-smoke.spec.mjs:492`는 now `#approval-meta span` scoped exact-text assertions로 정리되었습니다.
  - 남은 broad assertions는 `e2e/tests/web-smoke.spec.mjs:453`의 negative whole-box assertion과 `e2e/tests/web-smoke.spec.mjs:454`, `e2e/tests/web-smoke.spec.mjs:461`, `e2e/tests/web-smoke.spec.mjs:493`의 `#approval-preview` partial assertions입니다.
- next exact slice는 `corrected-save-long-history-approval-preview exact-text smoke tightening`으로 갱신했습니다.
  - current `e2e/tests/web-smoke.spec.mjs:493`는 same long-history scenario의 dedicated `#approval-preview`를 아직 `toContainText("수정본 A입니다.")`로만 확인합니다.
  - current shipped template은 `app/templates/index.html:323`에서 dedicated `<pre id="approval-preview">`를 제공하고, runtime은 `app/static/app.js:3074`에서 preview를 `textContent`로 직접 렌더링합니다.
  - same scenario는 `e2e/tests/web-smoke.spec.mjs:476`에서 fixed multiline `correctedTextA = "수정본 A입니다.\n핵심만 남겼습니다."`를 사용하므로, line 493 한 건만 `toHaveText(correctedTextA)`로 좁히는 것이 가장 작은 다음 same-family user-visible improvement입니다.
  - `e2e/tests/web-smoke.spec.mjs:453`의 negative whole-box assertion은 line 450과 line 492의 exact positive basis checks보다 덜 user-visible하고 이미 상당 부분 함의되므로, 지금 즉시 우선할 next slice로는 덜 적합합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/4/2026-04-04-corrected-save-post-approval-approval-meta-basis-scoped-selector-smoke-tightening.md`
- `sed -n '1,240p' verify/4/4/2026-04-04-corrected-save-approval-meta-new-save-explanation-scoped-selector-smoke-tightening-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git show --stat --oneline 568ebc1 -- e2e/tests/web-smoke.spec.mjs`
- `git branch -r --contains 568ebc1`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `sed -n '448,453p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '490,493p' e2e/tests/web-smoke.spec.mjs`
- `rg -n '#approval-meta|저장 기준: 기록된 수정본 스냅샷|원래 grounded brief 초안|더 새 수정본을 저장하려면 응답 카드에서 새 저장 요청을 다시 만들어야 합니다' e2e/tests/web-smoke.spec.mjs app/static/app.js app/templates/index.html`
- `make e2e-test`
  - `17 passed (3.3m)`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '490,495p'`
- `sed -n '486,496p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '446,456p' e2e/tests/web-smoke.spec.mjs`
- `rg -n '#approval-preview|approval-preview|수정본 A입니다\\.|핵심만 남겼습니다\\.' e2e/tests/web-smoke.spec.mjs app/static/app.js app/templates/index.html`
- `sed -n '3072,3075p' app/static/app.js`
- `rg -n '#approval-meta span|#approval-meta\\)' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '475,477p'`
- `nl -ba app/static/app.js | sed -n '3072,3074p'`
- `python3 -m unittest -v tests.test_web_app`는 재실행하지 않았습니다. 이번 latest `/work`는 Playwright assertion tightening만 다뤘고 Python/server runtime 변경이 없었기 때문입니다.

## 남은 리스크
- unrelated dirty worktree가 이미 넓게 존재합니다. 다음 Claude 라운드는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/*`, watcher/pipeline 스크립트, `work/README.md`, `verify/README.md` 등 현재 슬라이스와 무관한 dirty 파일을 건드리거나 정리하면 안 됩니다.
- latest `/work` 파일명/본문의 `post-approval` timing wording은 line 492의 실제 위치와 어긋납니다. 이후 handoff와 closeout에서는 approval click 전/후를 더 정확히 적어야 합니다.
- corrected-save approval card에는 line 453의 negative whole-box assertion과 여러 `#approval-preview` partial assertions이 아직 남아 있습니다.
- 이번 handoff는 same long-history scenario의 `#approval-preview` line 493 한 건만 exact-text로 좁히도록 제한했습니다. line 454/461/462까지 한 번에 넓히면 범위가 불필요하게 커집니다.
