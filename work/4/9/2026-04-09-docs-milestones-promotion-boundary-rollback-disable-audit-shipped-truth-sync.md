# docs: MILESTONES promotion-boundary summary rollback disable operator-audit shipped truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 193): "rollback, disable, and operator-audit rules remain later" → "rollback, disable, and operator-audit contract surfaces are also shipped as read-only objects (state machines and satisfaction booleans remain later)"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 193이 rollback/disable/operator-audit를 "remain later"로 전역 부정
- 실제로 `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_transition_audit_contract`는 이미 read-only 계약 객체로 출하됨
- state machine과 satisfaction boolean만 실제로 later
- 동일 파일 line 216, 228, 259에서 이미 "current contract now also emits"로 기술
- 권위 문서 모두 shipped로 기술

## 핵심 변경
- "rollback, disable, and operator-audit rules remain later" → "rollback, disable, and operator-audit contract surfaces are also shipped as read-only objects (state machines and satisfaction booleans remain later)"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES promotion-boundary 요약의 rollback/disable/operator-audit shipped/later 경계 진실 동기화 완료
