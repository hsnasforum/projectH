# docs: README project-brief PRODUCT_PROPOSAL browser response-surface residual truth sync

## 변경 파일
- `README.md` — 1곳(line 114): "evidence, summary-range panels" → "evidence/source panel, summary span / applied-range panel"
- `docs/project-brief.md` — 2곳(line 15, 74): summary-range/streaming cancel → shipped surface 반영, search result preview/source-type labels/applied-preferences badge 추가
- `docs/PRODUCT_PROPOSAL.md` — 1곳(line 54): summary-range → shipped surface 반영, search result preview/source-type labels/applied-preferences badge 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 라운드에서 core docs(PRODUCT_SPEC, ACCEPTANCE_CRITERIA, ARCHITECTURE, TASK_BACKLOG, MILESTONES, NEXT_STEPS) 동기화 완료
- 비핵심 docs(README smoke 목록, project-brief, PRODUCT_PROPOSAL)에 동일 패턴 잔여
- "summary-range panel", "streaming cancel", 누락된 search result preview/source-type labels/applied-preferences badge

## 핵심 변경
- "summary-range" → "summary span / applied-range panel"
- "streaming cancel" → "streaming progress + cancel"
- "evidence/source panels, summary-range metadata" → "evidence/source panel, structured search result preview panel, summary source-type labels, summary span / applied-range panel"
- applied-preferences badge 항목 추가
- README smoke 목록은 실제 Playwright assertion 범위 내에서만 수정

## 검증
- `git diff --stat` — 3 files changed, 14 insertions(+), 6 deletions(-)
- `rg 'summary-range|streaming cancel'` — 3개 대상 파일 모두 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 browser response-surface wording 동기화 완료
