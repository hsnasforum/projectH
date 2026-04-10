# docs: MILESTONES reviewed_memory_boundary_defined current-shipped wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 201): "the next contract decision now also fixes" → "is now fixed to one shipped narrow reviewed scope"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 201이 "next contract decision now also fixes"로 프레이밍
- 권위 문서(PRODUCT_SPEC:1128-1134, ARCHITECTURE:860-863, ACCEPTANCE_CRITERIA:644-646)에서 이미 current shipped로 기술

## 핵심 변경
- "the next contract decision now also fixes `reviewed_memory_boundary_defined` to one fixed narrow reviewed scope" → "`reviewed_memory_boundary_defined` is now fixed to one shipped narrow reviewed scope"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES boundary_defined 헤딩 shipped 진실 동기화 완료
