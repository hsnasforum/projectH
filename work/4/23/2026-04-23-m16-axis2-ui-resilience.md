# 2026-04-23 M16 Axis 2 UI resilience

## 변경 파일
- `app/frontend/src/App.tsx`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m16-axis2-ui-resilience.md`

## 사용 skill
- `doc-sync`: M16 Axis 2 shipped 기록을 `docs/MILESTONES.md`의 현재 구현 사실과 맞췄습니다.
- `finalize-lite`: 지정된 TypeScript, whitespace 검증 결과와 미실행 범위를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 이번 `/work` closeout에 기록했습니다.

## 변경 이유
- implement handoff seq 44 기준 `handleCandidateReview` 실패가 silent catch로 버려지고 있었습니다.
- 기존 correction, feedback, content verdict, corrected save handler는 실패 시 toast를 띄우므로 review action도 같은 사용자 피드백 패턴을 따라야 했습니다.
- 이번 slice는 error surfacing만 다루며 loading state, retry, error-path Playwright mocking, `app/static/dist` 갱신은 범위 밖이었습니다.

## 핵심 변경
- `handleCandidateReview` catch에서 `addToast("error", "검토 액션 제출에 실패했습니다.")`를 호출하도록 바꿨습니다.
- `handleCandidateReview`의 `useCallback` dependency array에 `addToast`를 추가했습니다.
- 성공 toast는 추가하지 않았습니다. handoff에서 success toast는 optional이었고, 이번 범위는 accept/defer/reject 실패 surfacing만 요구했기 때문입니다.
- `docs/MILESTONES.md`의 M16 섹션을 shipped Axis 1-2와 planned Axis 3으로 정리하고 Axis 2 UI resilience 항목을 추가했습니다.

## 검증
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `git diff --check -- app/frontend/src/App.tsx docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- handoff boundary대로 Playwright error-path test, Vite build, `app/static/dist` 갱신은 실행하지 않았습니다.
- 네트워크 실패나 stale candidate 응답의 상세 원인은 아직 toast 문구에 구분해 표시하지 않습니다.
- 이번 docs 변경은 실제 파일 기준으로 M16 Axis 1 구현이 이미 존재하는 상태를 반영해 `Planned Infrastructure`를 shipped Axis 1-2와 planned Axis 3으로 나누었습니다.
