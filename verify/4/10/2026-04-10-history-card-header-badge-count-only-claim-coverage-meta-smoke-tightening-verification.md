# history-card header-badge count-only claim-coverage meta smoke tightening verification

## 변경 파일
- `verify/4/10/2026-04-10-history-card-header-badge-count-only-claim-coverage-meta-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 최신 `/work`인 `work/4/10/2026-04-10-history-card-header-badge-count-only-claim-coverage-meta-smoke-tightening.md`가 현재 코드와 최소 검증 결과를 truthfully 설명하는지 다시 확인해야 했습니다.
- 동시에 same-family header-badge smoke를 또 다른 docs sync가 아니라 한 개의 exact current-risk reduction으로 이어야 했습니다.

## 핵심 변경
- 최신 `/work` closeout은 현재도 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:1145-1242`에는 card5 fixture와 count-only `.meta` 어서션이 실제로 들어 있습니다.
  - `app/static/app.js:2225-2231`은 `claim_coverage_summary`를 `교차 확인` / `단일 출처` / `미확인` count text로 포맷하고, `app/static/app.js:2958-2964`는 그 결과를 `claim_coverage_progress_summary`보다 먼저 `detailLines`에 push합니다.
  - isolated Playwright rerun은 해당 generic header-badge 시나리오 1건만 다시 통과했습니다.
- 이번 라운드의 최소 검증도 `/work` 주장과 일치합니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10`은 공백 오류를 보고하지 않았습니다.
  - root docs(`docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`)를 다시 확인했을 때 이번 라운드는 shipped user-visible contract를 넓히지 않는 동일 scenario 내부 smoke tightening이므로 same-round docs sync가 필요한 상태는 아니었습니다.
  - broader unit suite나 full Playwright suite가 필요한 shared-helper drift 신호는 이번 시나리오 범위에서 보이지 않았습니다.
- 다음 exact slice는 same-family count-plus-progress 결합 경계를 잠그는 smoke tightening이 맞습니다.
  - 현재 generic header-badge scenario는 progress-only(card1), empty-only(card2~4), count-only(card5)는 모두 관찰하지만, `claim_coverage_summary`와 `claim_coverage_progress_summary`가 동시에 non-empty인 investigation card fixture는 아직 없습니다.
  - `app/static/app.js:2958-2969`는 count line을 먼저 push한 뒤 progress summary를 추가하고 `detailLines.join(" · ")`로 `.meta`를 구성하므로, 두 필드가 함께 있을 때 count line 우선순서와 separator 경계가 현재 renderer의 마지막 미잠금 조합입니다.
  - 따라서 `CONTROL_SEQ: 21`의 가장 작은 truthful next slice는 같은 시나리오 안에서 combined count-plus-progress case를 추가하고, `.meta`가 count line 다음 progress summary를 정확한 순서로 렌더링하며 answer-mode label/leading-trailing separator artifact를 만들지 않는다는 contract를 잠그는 것입니다.

## 검증
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs work/4/10/2026-04-10-history-card-header-badge-count-only-claim-coverage-meta-smoke-tightening.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1100,1275p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1270,1355p'`
- `nl -ba app/static/app.js | sed -n '2225,2235p;2954,2972p'`
- `find work/4/10 -maxdepth 1 -type f | sort`
- `find verify/4/10 -maxdepth 1 -type f | sort`
- `rg -n -C 2 "claim_coverage_summary|claim_coverage_progress_summary" e2e/tests/web-smoke.spec.mjs | sed -n '1,220p'`
- `rg -n "claim_coverage_summary:" e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed (5.6s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음
- broader unit/Playwright rerun은 하지 않았습니다. 이번 변경과 검증 범위가 기존 시나리오 1건의 fixture/assertion tightening에 한정되고, shared browser helper나 runtime contract 확장 신호가 없었기 때문입니다.

## 남은 리스크
- generic header-badge scenario는 이제 count-only path까지 잠그지만, count line과 progress summary가 함께 있는 combined investigation meta path는 아직 직접 잠그지 못합니다.
- repo에는 unrelated local changes가 많아서 다음 라운드도 `app.web` history-card smoke 범위를 넘기지 않는 편이 안전합니다.
- 이번 verify는 isolated scenario 재실행 기준이므로 broader browser family drift는 별도 evidence 없이는 판단하지 않았습니다.
