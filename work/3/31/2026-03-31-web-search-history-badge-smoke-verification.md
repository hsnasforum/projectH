# 2026-03-31 web-search history badge dedicated browser smoke 확인

## 변경 파일
- 없음 (기존 dirty worktree에 이미 구현 완료 상태)

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로 web-search history card header badge contract에 대한 dedicated browser smoke 추가를 지시했으나, dirty worktree에 이미 해당 구현이 포함되어 있었음.
- 근거: `work/3/31/2026-03-31-claim-coverage-panel-smoke.md`, `verify/3/31/2026-03-31-claim-coverage-panel-smoke-verification.md`

## 핵심 변경
- 이번 라운드에서 새로운 코드 변경 없음.
- 기존 worktree 상태 확인 결과:
  - `e2e/tests/web-smoke.spec.mjs:848` — scenario 15로 web-search history badge smoke 이미 존재
  - `renderSearchHistory()`에 deterministic fixture 3개 주입 방식
  - answer-mode badge (`설명 카드` / `최신 확인`), verification-strength badge (`검증 강` / `검증 중` / `검증 약` + CSS class), source-role trust badge compact label 검증
  - `general` answer_mode는 `.answer-mode-badge` count 0 확인
  - `app/templates/index.html`에 `renderSearchHistory` 함수, badge CSS class 모두 존재
  - README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG, NEXT_STEPS 모두 scenario count 15 반영 완료

## 검증
- `make e2e-test`: 15 passed (3.5m)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`: 통과

## 남은 리스크
- dirty worktree가 여전히 넓어서 이 15개 smoke가 커밋되기 전까지는 유실 가능성 있음.
- `renderSearchHistory`의 badge 매핑 로직은 frontend 내부에서만 검증됨. backend가 `answer_mode`, `verification_label`, `source_roles`를 올바르게 생성하는지는 별도 unit/integration test 축 필요.
