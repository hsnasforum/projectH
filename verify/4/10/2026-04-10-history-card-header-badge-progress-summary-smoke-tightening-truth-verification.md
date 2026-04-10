# history-card header-badge progress-summary smoke tightening truth verification

## 변경 파일
- `verify/4/10/2026-04-10-history-card-header-badge-progress-summary-smoke-tightening-truth-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/10/2026-04-10-history-card-header-badge-progress-summary-smoke-tightening.md`가 현재 코드와 검증 결과를 truthfully 설명하는지 다시 확인해야 했습니다.
- 동시에 같은 family에서 `CONTROL_SEQ: 18`의 다음 한 슬라이스를 새 runtime/test 확장이 아니라 bounded docs truth-sync로 좁힐 수 있는지 판단해야 했습니다.

## 핵심 변경
- 최신 `/work` closeout은 현재도 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:1113`에서 generic header-badge fixture가 non-empty `claim_coverage_progress_summary`를 전달합니다.
  - `e2e/tests/web-smoke.spec.mjs:1166` 부근에서 같은 card meta에 progress summary 텍스트가 보이는지 직접 assertion 합니다.
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` 재실행 결과 `1 passed (4.7s)`로 latest `/work`의 핵심 주장을 다시 확인했습니다.
- 이번 라운드에서 남아 있는 same-family drift는 runtime이 아니라 root docs입니다.
  - 실제 Playwright smoke scenario 수는 `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 기준 `82`입니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1350`는 아직 `79 core browser scenarios`라고 적습니다.
  - `docs/MILESTONES.md:50`와 `docs/TASK_BACKLOG.md:36`는 header-badge smoke 설명에서 now-shipped progress summary visibility를 빠뜨립니다.
  - `docs/NEXT_STEPS.md:22`는 scenario count는 `82`로 맞지만, header-badge contract 설명에서는 progress summary 항목을 아직 빠뜨립니다.
- 따라서 `CONTROL_SEQ: 18`의 가장 작은 truthful next slice는 새 browser/runtime work가 아니라, root docs를 현재 header-badge smoke contract와 `82` scenario count에 맞추는 one-bundle docs truth-sync입니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10/2026-04-10-history-card-header-badge-progress-summary-smoke-tightening.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line`
- `git log --oneline -n 5 -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1100,1185p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
- `sed -n '1350,1395p' docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/MILESTONES.md | sed -n '44,58p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '30,40p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '18,30p'`
- broader unit/browser suite는 재실행하지 않았습니다. latest `/work`가 closeout 범위만 다루고 있고, claimed change에 직접 대응하는 isolated Playwright scenario가 이미 통과했기 때문입니다.

## 남은 리스크
- `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`는 아직 current header-badge smoke contract를 fully reflect하지 못합니다.
- 이번 라운드는 isolated header-badge scenario만 재실행했으므로 broader Playwright family drift는 별도 라운드 범위입니다.
- repo에는 unrelated local changes가 많으므로 다음 라운드는 해당 편집을 건드리지 않고 docs truth-sync만 bounded하게 닫아야 합니다.
