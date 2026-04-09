# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA ARCHITECTURE TASK_BACKLOG browser response-surface wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 1곳(line 1842): "streaming cancel" → "streaming progress + cancel"
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 25, 1360): "summary-range panel" → "summary span / applied-range panel", "streaming cancel" → "streaming progress + cancel"
- `docs/ARCHITECTURE.md` — 4곳(line 109, 1319, 1330, 1359): "evidence and summary-range panels" → "evidence/source panel and summary span / applied-range panel", "summary-range panel" → "summary span / applied-range panel", "streaming cancel" → "streaming progress + cancel"
- `docs/TASK_BACKLOG.md` — 1곳(line 18): "Evidence/source panel and summary-range panel" → "Evidence/source panel, structured search result preview panel, summary source-type labels, and summary span / applied-range panel"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- "summary-range panel"은 구명칭; shipped truth는 "summary span / applied-range panel" (README/PRODUCT_SPEC 기준)
- "streaming cancel"은 불완전; shipped truth는 "streaming progress + cancel" (progress box + cancel button)
- "evidence and summary-range panels"은 현재 shipped surface를 반영하지 않음
- TASK_BACKLOG:18에서 structured search result preview panel과 summary source-type labels 누락

## 핵심 변경
- 4개 파일 8곳에서 stale wording 교체
- README/MILESTONES/NEXT_STEPS와 동일한 문구 사용
- 코드, 테스트, 런타임 변경 없음

## 검증
- `git diff --stat` — 4 files changed, 8 insertions(+), 8 deletions(-)
- `rg 'summary-range panel'` — 4개 대상 파일 모두 0건
- `rg 'streaming cancel'` — 4개 대상 파일 모두 0건 (project-brief.md만 잔여, scope 외)
- `git diff --check` — 공백 오류 없음

## 남은 리스크
- `docs/project-brief.md`에 "streaming cancel" 잔여 — 현재 슬라이스 scope 외
