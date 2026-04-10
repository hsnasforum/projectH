# docs: NEXT_STEPS TASK_BACKLOG aggregate item contract-object current-shipped wording truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — 6곳(line 122, 146, 156, 166, 177, 189): "may now also expose" → "now also exposes"
- `docs/TASK_BACKLOG.md` — 7곳(line 145, 146, 336, 367, 397, 425, 456): "can now also expose" / "may now also expose" → "now also expose"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 13개 행이 이미 출하된 read-only aggregate item 계약 객체를 "may/can now also expose"로 약하게 기술
- MILESTONES(line 200, 204, 216, 228, 242, 259)와 권위 문서(PRODUCT_SPEC, ARCHITECTURE, ACCEPTANCE_CRITERIA)는 이미 current-shipped 패턴 사용

## 핵심 변경
- NEXT_STEPS: 6개 계약 객체 헤딩에서 "may now also expose" → "now also exposes"
- TASK_BACKLOG: 7개 계약 객체 헤딩에서 "can/may now also expose" → "now also expose"

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 13줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 기획 문서 aggregate item 계약 객체 shipped 문구 진실 동기화 완료
