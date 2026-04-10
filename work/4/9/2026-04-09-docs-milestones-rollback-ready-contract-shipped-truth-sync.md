# docs: MILESTONES rollback_ready contract-decision wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 211): `rollback_ready_reviewed_memory_effect` 헤딩에서 "next contract decision now also fixes ... future rollback target" → "is now fixed as one shipped rollback contract surface"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 211이 "next contract decision now also fixes ... to one exact future rollback target"으로 프레이밍
- 권위 문서(PRODUCT_SPEC:1135-1142, 1483-1485; ARCHITECTURE:864-869; ACCEPTANCE_CRITERIA:647-652)에서 이미 shipped로 기술
- 동일 블록의 `disable_ready` 헤딩(line 223)은 이전 슬라이스에서 이미 shipped로 수정 완료

## 핵심 변경
- "the next contract decision now also fixes `rollback_ready_reviewed_memory_effect` to one exact future rollback target" → "`rollback_ready_reviewed_memory_effect` is now fixed as one shipped rollback contract surface"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES rollback_ready 헤딩 shipped 진실 동기화 완료
