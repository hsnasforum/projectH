# history-card header-badge empty progress-summary smoke negatives verification

## 변경 파일
- `verify/4/10/2026-04-10-history-card-header-badge-empty-progress-summary-smoke-negatives-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 최신 `/work`인 `work/4/10/2026-04-10-history-card-header-badge-empty-progress-summary-smoke-negatives.md`가 현재 코드와 최소 검증 결과를 truthfully 설명하는지 다시 확인해야 했습니다.
- 동시에 same-family header-badge smoke를 또 다른 docs sync가 아니라 한 개의 exact current-risk reduction으로 이어야 했습니다.

## 핵심 변경
- 최신 `/work` closeout은 현재도 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:1180-1217`에는 card2/card3/card4의 empty `claim_coverage_progress_summary` hidden-empty negative assertions이 실제로 들어 있습니다.
  - `app/static/app.js:2954-2969`는 `claim_coverage_summary`와 `claim_coverage_progress_summary`를 각각 non-empty일 때만 `detailLines`에 추가하고, 값이 없으면 `.meta`를 만들지 않습니다.
  - isolated Playwright rerun은 해당 generic header-badge 시나리오 1건만 다시 통과했습니다.
- 이번 라운드의 최소 검증도 `/work` 주장과 일치합니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10/2026-04-10-history-card-header-badge-empty-progress-summary-smoke-negatives.md`는 공백 오류를 보고하지 않았습니다.
  - broader unit suite나 full Playwright suite가 필요한 shared-helper drift 신호는 이번 시나리오 범위에서 보이지 않았습니다.
- 다음 exact slice는 same-family count-only mixed-summary 경계를 잠그는 smoke tightening이 맞습니다.
  - `app/static/app.js:2958-2964`는 `claim_coverage_summary`가 있으면 `사실 검증 ...` count line을 먼저 push하고, `claim_coverage_progress_summary`가 비어 있으면 그 한 줄만 남깁니다.
  - 그러나 현재 generic header-badge scenario(`e2e/tests/web-smoke.spec.mjs:1102-1217`)에는 `claim_coverage_summary`만 채워지고 `claim_coverage_progress_summary`는 빈 investigation card fixture가 아직 없습니다.
  - 따라서 `CONTROL_SEQ: 20`의 가장 작은 truthful next slice는 count-only mixed case에서 `.meta`가 count line만 렌더링하고 stray separator나 progress text를 만들지 않는다는 contract를 같은 시나리오 안에서 잠그는 것입니다.

## 검증
- `git status --short`
- `git diff --stat`
- `git diff -- e2e/tests/web-smoke.spec.mjs work/4/10/2026-04-10-history-card-header-badge-empty-progress-summary-smoke-negatives.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1100,1235p'`
- `nl -ba app/static/app.js | sed -n '2948,2972p'`
- `find work/4/10 -maxdepth 1 -type f | sort`
- `find verify/4/10 -maxdepth 1 -type f | sort`
- `rg -n "header-badge|progress-summary|claim_coverage_progress_summary" work/4/10 verify/4/10 -g '*.md'`
- `rg -n "claim_coverage_summary|claim_coverage_progress_summary" e2e/tests/web-smoke.spec.mjs`
- `nl -ba app/static/app.js | sed -n '2220,2248p'`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed (5.3s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10/2026-04-10-history-card-header-badge-empty-progress-summary-smoke-negatives.md` → 출력 없음
- broader unit/Playwright rerun은 하지 않았습니다. 이번 변경과 검증 범위가 기존 시나리오 1건의 negative tightening에 한정되고, shared browser helper나 runtime contract 확장 신호가 없었기 때문입니다.

## 남은 리스크
- generic header-badge scenario는 이제 empty progress-summary hidden path는 잠그지만, `claim_coverage_summary`만 있고 `claim_coverage_progress_summary`는 빈 count-only investigation meta path는 아직 직접 잠그지 못합니다.
- repo에는 unrelated local changes가 많아서 다음 라운드도 `app.web` history-card smoke 범위를 넘기지 않는 편이 안전합니다.
- 이번 verify는 isolated scenario 재실행 기준이므로 broader browser family drift는 별도 evidence 없이는 판단하지 않았습니다.
