# docs: MILESTONES NEXT_STEPS current browser response-surface summary truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 29): response surface 요약 확장
- `docs/NEXT_STEPS.md` — 3곳(line 10-11, 14): evidence/source, search result preview, source-type labels, summary span, streaming 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- MILESTONES:29 "response cards and note preview"가 현재 shipped surface(evidence/source panel, structured search result preview, summary source-type labels, summary span / applied-range panel)를 반영하지 않음
- NEXT_STEPS:11 "summary-range panel"은 구명칭; README에서는 "summary span / applied-range panel" 사용
- NEXT_STEPS:14 "streaming cancel"은 "streaming progress + cancel"이 정확

## 핵심 변경
- MILESTONES:29 — "response cards and note preview" → "response cards with note preview, structured search result preview panel, evidence/source panel, summary source-type labels (`문서 요약` / `선택 결과 요약`), and summary span / applied-range panel"
- NEXT_STEPS:10 — "evidence/source panel" → "evidence/source panel with source-role trust labels"
- NEXT_STEPS:11 — "summary-range panel" → "structured search result preview panel" + "summary source-type labels" + "summary span / applied-range panel" (3줄로 분리)
- NEXT_STEPS:14 — "streaming cancel" → "streaming progress + cancel"
- README/PRODUCT_SPEC과 동일한 문구 사용

## 검증
- `git diff -- docs/MILESTONES.md docs/NEXT_STEPS.md` — 확인
- `rg` — stale 문구 0건, 새 문구 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — MILESTONES/NEXT_STEPS browser response-surface summary 진실 동기화 완료
