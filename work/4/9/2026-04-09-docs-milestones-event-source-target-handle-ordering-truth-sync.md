# docs: MILESTONES event-source target-handle ordering truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 302): event-source 순서 행의 "later target or handle materialization" → "now-materialized target and handle"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 동일 블록 line 294-298에서 이미 target과 handle을 "now-materialized"로 기술
- 권위 문서(PRODUCT_SPEC:1395-1412, ARCHITECTURE:1100-1114, ACCEPTANCE_CRITERIA:1052-1066)도 동일
- line 302만 "later target or handle materialization" 잔존

## 핵심 변경
- "beneath any later target or handle materialization" → "beneath the now-materialized target and handle"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES event-source/target/handle 순서 수식어 진실 동기화 완료
