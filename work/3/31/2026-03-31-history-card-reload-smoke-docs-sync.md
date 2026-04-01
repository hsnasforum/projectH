# 2026-03-31 history-card reload smoke docs sync

## 변경 파일
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 이전 라운드에서 추가한 history-card reload Playwright smoke의 docs sync가 빠졌다는 지적에 따라 문서 동기화 슬라이스를 지시.
- smoke scenario count가 15→16으로 늘어난 사실과 새 scenario 설명이 5개 문서에 반영되지 않았음.
- 근거: `work/3/31/2026-03-31-history-card-reload-badge-playwright-smoke.md`, `verify/3/31/2026-03-31-history-card-reload-badge-playwright-smoke-verification.md`

## 핵심 변경
- `README.md`: scenario 16번 항목 추가 (history-card `다시 불러오기` click reload badge 유지)
- `docs/ACCEPTANCE_CRITERIA.md`: "15 core browser scenarios" → "16 core browser scenarios", scenario 설명 1줄 추가
- `docs/MILESTONES.md`: history-card reload browser smoke milestone 1줄 추가
- `docs/TASK_BACKLOG.md`: 완료 항목 22번 추가
- `docs/NEXT_STEPS.md`: "15 browser scenarios" → "16 browser scenarios", scenario 목록에 reload smoke 설명 삽입
- UI, app logic, tests, approval flow, reviewed-memory 변경 없음 — docs-only slice

## 검증
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`: 통과
- 문구 대조: 5개 파일 모두에서 "16 browser scenarios" 또는 "16 core browser", "history-card.*다시 불러오기", "설명 카드", "설명형 단일 출처" 확인

## 남은 리스크
- dirty worktree가 여전히 넓음.
