# docs: PRODUCT_SPEC ARCHITECTURE summary-range metadata residual truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 3곳(line 135, 145, 1832): "summary-range" → "summary span / applied-range"
- `docs/ARCHITECTURE.md` — 2곳(line 44, 116): "summary-range" → "summary span / applied-range"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- "summary-range"는 구명칭; shipped truth는 "summary span / applied-range"
- metadata/selection 맥락에서는 panel 대신 metadata 수식어 유지
- smoke coverage 맥락에서는 panel 수식어 사용

## 핵심 변경
- PRODUCT_SPEC:135, 145 — "attach evidence and summary-range metadata" → "attach evidence/source and summary span / applied-range metadata"
- PRODUCT_SPEC:1832 — "file summary with evidence and summary range" → "file summary with evidence/source panel and summary span / applied-range panel"
- ARCHITECTURE:44 — "evidence and summary-range selection" → "evidence/source and summary span / applied-range selection"
- ARCHITECTURE:116 — "evidence and summary-range metadata are attached" → "evidence/source and summary span / applied-range metadata are attached"

## 검증
- `git diff --stat` — 2 files changed, 5 insertions(+), 5 deletions(-)
- `rg 'summary-range'` — 2개 대상 파일 모두 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — PRODUCT_SPEC/ARCHITECTURE의 summary-range metadata 잔여 동기화 완료
