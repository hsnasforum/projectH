# review-outcome follow-up quick-meta smoke + inventory sync bundle

## 변경 파일

- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

이전 라운드가 `supplementQuickMetaReviewOutcome()` 공유 헬퍼로 `renderSession()`/`renderResult()` parity를 코드 레벨에서 닫았으나, review accept 후 plain follow-up 응답(renderResult 경로)에서의 quick-meta retention과, 이후 새로운 correction이 현재 context를 교체한 뒤의 quick-meta drop은 브라우저 assertion으로 고정되지 않았습니다. 이 라운드는 그 browser-proof gap을 닫습니다.

## 핵심 변경

1. **`findSessionReviewedSource()` 수정** (`app/static/app.js`): 세션 메시지를 역순으로 탐색할 때, `candidate_review_record`만 찾는 대신 최신 `session_local_candidate`를 가진 메시지에서 먼저 멈추도록 변경. 해당 메시지에 `candidate_review_record`가 있으면 반환, 없으면 null 반환. 이로써 새로운 unreviewed correction target이 존재하면 오래된 review가 quick-meta에 전파되지 않음.

2. **`supplementQuickMetaReviewOutcome()` 수정** (`app/static/app.js`): `correctionTargetMessage`가 존재하면(null이 아니면) 해당 target의 review record만 사용하고 세션 전체 탐색으로 fallback하지 않도록 변경. `correctionTargetMessage`가 null일 때만(예: chat follow-up) `findSessionReviewedSource()`로 fallback.

3. **e2e 시나리오 확장** (`e2e/tests/web-smoke.spec.mjs`): 기존 candidate confirmation 시나리오에 이미 추가되어 있던 follow-up 경로의 transcript-meta assertion을 수정. 새 correction이 다른 소스에 적용된 후에도 원래 reviewed source message의 transcript card는 자체 `candidate_review_record`를 그대로 표시하므로 `toHaveCount(1)` (원래 reviewed source 1건 유지)로 정정.

4. **inventory 동기화** (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`): 시나리오 11 설명에 "retains review-outcome quick-meta on plain follow-up responses, and drops review-outcome quick-meta after a later correction creates a newer unreviewed context" 반영.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다" --reporter=line` → 1 passed (43.5s)
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md` → clean
- full Playwright suite 미실행: 이번 라운드는 single-scenario 내의 quick-meta parity 보강이며, shared browser helper 전체가 흔들렸다는 증거 없음.

## 남은 리스크

- `reject`/`defer` review outcome의 browser-level quick-meta retention/drop은 아직 별도 시나리오로 고정되지 않았습니다.
- transcript-meta의 review-outcome label은 각 메시지 자체의 `candidate_review_record`에서 직접 렌더링되며, 세션 전체의 "현재 context" 판단과는 별개입니다. 이 동작은 의도된 것이나, 추후 UX 검토 시 stale transcript label 정책이 변경될 수 있습니다.
