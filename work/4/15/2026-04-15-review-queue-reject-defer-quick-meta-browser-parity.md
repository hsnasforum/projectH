# review-queue reject/defer quick-meta browser parity

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

accept-path review-outcome parity는 이전 라운드들에서 이미 닫혔습니다 (source-message transcript meta, quick-meta, follow-up retention, stale-clear). 이 라운드는 같은 shipped `검토 후보` 표면에서 `reject`와 `defer` review action이 동일한 browser contract를 따르는지 고정합니다. `app/static/app.js`는 변경 없이 기존 `formatReviewOutcomeLabel()`/`supplementQuickMetaReviewOutcome()` 공유 경로가 세 action 모두를 처리하므로, browser assertion만 추가했습니다.

## 핵심 변경

1. **새 시나리오 추가** (`e2e/tests/web-smoke.spec.mjs`): "review-queue reject/defer는 accept와 동일한 quick-meta, transcript-meta, stale-clear 경로를 따릅니다" 시나리오 신설.
   - reject path: 수정 → 확인 → review queue → `거절` 클릭 → quick-meta `검토 거절됨` + transcript-meta `검토 거절됨` 1건 → follow-up 후 quick-meta retention → 새 correction 후 stale-clear (quick-meta drop, transcript-meta 1건 유지)
   - defer path: 같은 세션에서 새 수정 → 확인 → review queue → `보류` 클릭 → quick-meta `검토 보류됨` + transcript-meta `검토 보류됨` 1건 → follow-up 후 quick-meta retention → 새 correction 후 stale-clear
   - payload 검증: reject record (`review_action: reject`, `review_status: rejected`), defer record (`review_action: defer`, `review_status: deferred`)
2. **smoke inventory 동기화** (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`): 시나리오 126번 추가 및 관련 설명 반영.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다" --reporter=line` → 1 passed (44.2s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review-queue reject/defer는 accept와 동일한 quick-meta, transcript-meta, stale-clear 경로를 따릅니다" --reporter=line` → 1 passed (40.8s)
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/15` → clean
- full Playwright suite 미실행: 이번 라운드는 e2e 시나리오 추가와 docs inventory sync에 한정되어 있고, `app/static/app.js` 변경 없으므로 shared browser helper 전체가 흔들렸다는 증거 없음.

## 남은 리스크

- `reject`/`defer` 후 `renderResult()` 경로 (streamed response)에서의 quick-meta retention은 별도 browser assertion으로 고정하지 않았습니다. 코드 레벨에서 `supplementQuickMetaReviewOutcome()`이 세 action 모두에 동일하게 적용되므로 parity는 코드 구조로 보장됩니다.
- `reject`된 candidate에 대한 aggregate 제외 논리는 아직 미구현입니다.
