# 2026-04-23 M15 Axis 3 review queue list UI

## 변경 파일
- `app/frontend/src/api/client.ts`
- `app/frontend/src/hooks/useChat.ts`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `app/frontend/src/components/Sidebar.tsx`
- `app/frontend/src/components/ChatArea.tsx`
- `app/frontend/src/App.tsx`
- `app/static/dist/assets/index-Chj1x-63.css`
- `app/static/dist/assets/index-ZWNljoPw.js`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m15-axis3-review-queue-ui.md`

## 사용 skill
- `doc-sync`: M15 Axis 3 shipped 기록을 `docs/MILESTONES.md`에 맞췄습니다.
- `finalize-lite`: TypeScript, focused Playwright, whitespace 검증 결과와 남은 리스크를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 실패 후 수정 이력을 `/work` 형식으로 기록했습니다.

## 변경 이유
- advisory seq 39 / implement handoff seq 40 기준 M15 Axis 3 review queue list UI를 구현해야 했습니다.
- React frontend의 review badge는 count만 보여주고 개별 review queue item과 accept/defer/reject action을 노출하지 않았습니다.
- 기존 `/api/candidate-review`는 `candidate_id`와 `candidate_updated_at`을 요구하므로 frontend API payload를 backend contract에 맞춰야 했습니다.

## 핵심 변경
- `useChat` state/return에 `reviewQueueItems`를 추가하고, session load 및 stream final merge 경로에서 `review_queue_items`를 보존하도록 했습니다.
- `ReviewQueuePanel.tsx`를 추가해 statement, 고품질 badge, 수락/보류/거절 버튼을 sidebar에 렌더링했습니다.
- `Sidebar.tsx`는 `ReviewQueuePanel`을 `PreferencePanel` 위에 표시하고, `ChatArea.tsx`의 review badge는 `data-testid="review-queue-badge"`를 가진 clickable button으로 바꿨습니다.
- `postCandidateReview`가 `candidate_id`, `candidate_updated_at`, `review_action`을 함께 보내도록 확장했고, panel action은 `supporting_confirmation_refs[].candidate_updated_at`을 우선 사용해 backend stale-candidate guard와 맞췄습니다.
- `/app-preview`가 source 변경을 반영하도록 Vite build 산출물의 tracked dist asset을 갱신했습니다.
- `web-smoke.spec.mjs`에 React preview에서 badge click -> panel -> accept -> queue removal을 확인하는 focused scenario를 추가했습니다.

## 검증
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `cd app/frontend && npx vite build`
  - 통과: `✓ built in 1.90s`
  - 참고: Vite CJS Node API deprecation warning이 출력됐습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review queue panel" --reporter=line`
  - 1차 실패: React session list가 `session_id`가 아니라 session title을 표시해 session button locator가 실패했습니다.
  - 2차 실패: `item.updated_at`을 `candidate_updated_at`으로 보내 backend가 `409` stale-candidate guard를 반환했습니다.
  - 최종 통과: `1 passed (23.7s)`; test setup title과 `supporting_confirmation_refs[].candidate_updated_at` 사용으로 수정했습니다.
- `git diff --check -- app/frontend/src/components/ReviewQueuePanel.tsx app/frontend/src/components/Sidebar.tsx app/frontend/src/components/ChatArea.tsx app/frontend/src/hooks/useChat.ts app/frontend/src/App.tsx app/frontend/src/api/client.ts docs/MILESTONES.md e2e/tests/web-smoke.spec.mjs app/static/dist`
  - 통과: 출력 없음

## 남은 리스크
- `postCandidateReview`는 handoff boundary대로 non-200 응답을 사용자에게 노출하지 않습니다. 이번 smoke는 backend 응답을 직접 assert하지만 실제 UI error handling은 아직 없습니다.
- `/app-preview` dist asset은 `dist/` ignore 규칙 때문에 새 hash 파일을 추적하지 않고 기존 tracked asset 파일명에 build 내용을 담았습니다. 기능 검증은 통과했지만 asset hash filename 정합성 정리는 별도 packaging 정책으로 다루는 편이 낫습니다.
- 전체 Playwright suite와 SQLite browser suite는 실행하지 않았습니다. 이번 handoff acceptance 범위인 TypeScript check, focused React preview smoke, whitespace check만 실행했습니다.
