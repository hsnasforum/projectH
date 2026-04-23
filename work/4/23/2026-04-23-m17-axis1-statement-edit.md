# 2026-04-23 M17 Axis 1 statement edit

## 변경 파일
- `app/handlers/aggregate.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `app/frontend/src/components/Sidebar.tsx`
- `app/frontend/src/App.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `app/static/dist/assets/index.css`
- `app/static/dist/assets/index.js`
- `work/4/23/2026-04-23-m17-axis1-statement-edit.md`

## 사용 skill
- `doc-sync`: M17 Axis 1 shipped 기록을 `docs/MILESTONES.md`에 추가했습니다.
- `finalize-lite`: 지정 검증과 focused browser smoke 결과, `/app-preview` dist 갱신 필요성을 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 이번 `/work` closeout에 기록했습니다.

## 변경 이유
- advisory seq 49 / implement handoff seq 50 기준 review queue 후보의 statement를 사용자가 수락 전에 다듬을 수 있어야 했습니다.
- 기존 수락 경로는 durable candidate의 원문 statement만 `PreferenceStore.description`으로 저장했습니다.
- 별도 `CandidateReviewAction.EDIT` 기록을 만들지 않고, 기존 `/api/candidate-review` accept 요청에 optional `statement`를 실어 한 단계로 수락하는 범위였습니다.

## 핵심 변경
- `submit_candidate_review()`가 optional `statement` payload를 정규화하고, accept 시 `PreferenceStore.record_reviewed_candidate_preference(description=...)`에 우선 사용합니다.
- `postCandidateReview()`와 `App.tsx` / `Sidebar.tsx` / `ReviewQueuePanel.tsx` callback signature에 optional `statement`를 추가했습니다.
- `ReviewQueuePanel`에 per-candidate inline edit state, `편집` 버튼, statement textarea, `취소` 버튼을 추가했습니다.
- 편집 중 `수락`을 누르면 수정된 statement를 함께 전송하고, `보류`/`거절`은 기존 action 흐름을 유지합니다.
- `web-smoke.spec.mjs`에 `review queue edit` focused scenario를 추가해 편집 statement가 preference description에 저장되는지 확인합니다.
- `/app-preview` smoke가 새 React UI를 보도록 `npx vite build`를 실행해 fixed-name dist asset `index.css` / `index.js`를 갱신했습니다.

## 검증
- `python3 -m py_compile app/handlers/aggregate.py`
  - 통과: 출력 없음
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `git diff --check -- app/handlers/aggregate.py app/frontend/src/api/client.ts app/frontend/src/components/ReviewQueuePanel.tsx app/frontend/src/components/Sidebar.tsx app/frontend/src/App.tsx docs/MILESTONES.md e2e/tests/web-smoke.spec.mjs`
  - 통과: 출력 없음
- `cd app/frontend && npx vite build`
  - 통과: `index.css`, `index.js` 생성
  - 참고: Vite CJS Node API deprecation warning이 출력됐습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review queue edit" --reporter=line`
  - 통과: `1 passed (24.1s)`
  - 참고: Node warning `The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.`이 출력됐지만 테스트는 통과했습니다.
- `find app/static/dist/assets -maxdepth 1 -type f -printf '%f\n' | sort`
  - 확인: `index.css`, `index.js`
- `git diff --check -- app/handlers/aggregate.py app/frontend/src/api/client.ts app/frontend/src/components/ReviewQueuePanel.tsx app/frontend/src/components/Sidebar.tsx app/frontend/src/App.tsx docs/MILESTONES.md e2e/tests/web-smoke.spec.mjs app/static/dist/index.html app/static/dist/assets/index.css app/static/dist/assets/index.js`
  - 통과: 출력 없음

## 남은 리스크
- inline edit는 statement/description만 바꾸며 fingerprint, candidate lifecycle, review status는 바꾸지 않습니다.
- 빈 문자열로 편집한 뒤 수락하면 `_normalize_optional_text()` 결과가 없으므로 기존 durable candidate statement로 fallback합니다.
- rich text 편집, 별도 edit 저장 단계, `CandidateReviewAction.EDIT` session 기록은 handoff boundary대로 추가하지 않았습니다.
- 전체 Playwright suite는 실행하지 않았고, 이번 handoff의 focused `review queue edit` smoke만 실행했습니다.
- 작업 전부터 있던 untracked `report/gemini/2026-04-23-m17-definition.md`는 이번 implement 범위 밖이라 건드리지 않았습니다.
