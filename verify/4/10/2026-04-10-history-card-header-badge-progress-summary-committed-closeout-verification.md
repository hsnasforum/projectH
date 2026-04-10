# history-card header-badge progress-summary committed-closeout verification

## 변경 파일
- `verify/4/10/2026-04-10-history-card-header-badge-progress-summary-committed-closeout-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`는 여전히 `work/4/10/2026-04-10-history-card-claim-progress-summary-surfacing-closeout.md`이므로, 이 closeout이 current truth 기준으로 계속 맞는지 먼저 유지 확인해야 했습니다.
- 동시에 latest `/verify`가 seq16으로 넘긴 exact slice가 현재 코드베이스에 실제로 반영되었는지, 반영됐다면 다음 Claude 라운드를 새 기능이 아니라 bounded closeout으로 좁혀야 하는지 다시 판단해야 했습니다.

## 핵심 변경
- 최신 `/work` closeout은 현재도 truthful합니다.
  - history-card progress summary surfacing의 shipped 경로(`storage/web_search_store.py` → `app/serializers.py` → `app/static/app.js`) 자체를 뒤집는 새 변경은 보이지 않았습니다.
- seq16 exact slice는 이제 dirty tree가 아니라 현재 `HEAD` 커밋에 이미 들어와 있습니다.
  - `git rev-parse --short HEAD` 기준 현재 `HEAD`는 `59e9941`입니다.
  - 커밋 `59e9941`(`test: add progress-summary assertion to header-badge smoke scenario`)가 `e2e/tests/web-smoke.spec.mjs`의 generic header-badge 시나리오에 progress summary fixture와 assertion을 추가합니다.
  - `e2e/tests/web-smoke.spec.mjs:1113`에서 첫 investigation card가 non-empty `claim_coverage_progress_summary`를 받습니다.
  - `e2e/tests/web-smoke.spec.mjs:1166-1168`에서 같은 시나리오가 history-card meta에 progress summary가 보이는지 직접 assertion 합니다.
- 이 exact slice에 필요한 최소 검증은 현재 통과합니다.
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed`
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs` → 출력 없음
- 현재 확인 범위에서는 same-family docs drift를 더 넓힐 이유는 없습니다.
  - `README.md:138`과 `docs/ACCEPTANCE_CRITERIA.md:1366`가 설명하는 progress summary contract는 커밋 `59e9941`의 시나리오 업데이트와 맞습니다.
  - `docs/NEXT_STEPS.md`는 더 압축된 smoke summary이며, 현재 committed change와 직접 충돌하는 새 문구 오류는 확인하지 못했습니다.
- 하지만 새 `/work` closeout은 아직 없습니다.
  - 따라서 `CONTROL_SEQ: 17`의 가장 truthful한 next slice는 새 product/test 확장이 아니라, 이미 커밋된 header-badge smoke tightening을 새 `/work` closeout으로 canonical truth에 닫는 것입니다.

## 검증
- `ls -lt work/4/10 | head -n 20`
- `ls -lt verify/4/10 | head -n 20`
- `git status --short -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md work/4/10 verify/4/10 .pipeline/claude_handoff.md`
- `git diff -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md .pipeline/claude_handoff.md`
- `sed -n '1,120p' docs/NEXT_STEPS.md`
- `sed -n '90,130p' docs/MILESTONES.md`
- `sed -n '1,90p' docs/TASK_BACKLOG.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1102,1172p'`
- `git status --short -- e2e/tests/web-smoke.spec.mjs`
- `git diff --name-only -- e2e/tests/web-smoke.spec.mjs`
- `git diff --cached --name-only -- e2e/tests/web-smoke.spec.mjs`
- `git log --oneline -n 5 -- e2e/tests/web-smoke.spec.mjs`
- `git show --stat --summary HEAD -- e2e/tests/web-smoke.spec.mjs`
- `git rev-parse --short HEAD`

## 남은 리스크
- 커밋 `59e9941`가 이미 들어와 있어도 새 `/work`가 없으면 canonical closeout truth는 여전히 뒤처집니다.
- 이번 라운드는 isolated scenario와 해당 diff hygiene만 재실행했으므로 broader Playwright family나 full browser suite drift까지는 독립적으로 재확인하지 않았습니다.
- 다음 라운드가 이 committed bundle을 closeout 없이 더 넓히면 same-family truth 정리가 다시 흔들릴 수 있습니다.
