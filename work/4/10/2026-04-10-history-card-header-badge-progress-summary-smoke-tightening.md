# 2026-04-10 history-card header-badge progress-summary smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — generic header-badge 시나리오에 `claim_coverage_progress_summary` fixture 및 assertion 추가

## 사용 skill
- `work-log-closeout` — handoff가 요구한 `/work` closeout 형식과 섹션 순서를 현재 사실 기준으로 정리하는 데 사용

## 변경 이유
- 현재 `HEAD`에는 generic header-badge Playwright 시나리오에 non-empty `claim_coverage_progress_summary` fixture와 assertion을 추가한 exact slice가 이미 커밋되어 있음
- 하지만 최신 canonical `/work`는 여전히 `work/4/10/2026-04-10-history-card-claim-progress-summary-surfacing-closeout.md`여서, committed된 header-badge smoke tightening bundle을 별도 closeout으로 닫는 기록이 필요했음
- 이번 기록은 새 기능을 넓히는 라운드가 아니라, 이미 커밋된 exact slice를 current truth 기준으로 canonical `/work`에 닫는 목적임

## 핵심 변경
1. `e2e/tests/web-smoke.spec.mjs`의 generic header-badge 시나리오는 현재 non-empty `claim_coverage_progress_summary` fixture를 포함합니다.
2. 같은 시나리오는 history-card meta 영역에서 progress summary 텍스트가 실제로 보이는지 assertion 합니다.
3. 이 closeout은 기존 shipped progress-summary surfacing closeout과 구분하여, 이미 커밋된 header-badge smoke tightening bundle만 별도 canonical `/work` truth로 닫습니다.

## 검증
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed (5.2s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10/2026-04-10-history-card-header-badge-progress-summary-smoke-tightening.md` → 출력 없음
- 이번 라운드에서는 broader `tests.test_web_app`, full Playwright suite, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- 이번 closeout은 committed된 exact smoke-tightening bundle만 닫습니다. app/runtime/docs 범위의 새 변경까지 포함하지 않습니다.
- isolated header-badge 시나리오 1건만 재실행했으므로, broader browser family drift는 별도 라운드에서 독립적으로 확인해야 합니다.
