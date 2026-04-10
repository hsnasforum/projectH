# docs: MILESTONES reviewed_memory_transition_audit_contract current-shipped wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 259): "the next shipped surface is now also implemented" → "the current contract now also emits"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 259가 "next shipped surface is now also implemented"로 혼합 시제 사용
- 권위 문서(PRODUCT_SPEC:1223-1232, ARCHITECTURE:956-965, ACCEPTANCE_CRITERIA:729-738)에서 current-emission 패턴 사용
- 동일 블록의 rollback(line 216), disable(line 228), conflict(line 242) 헤딩은 이전 슬라이스에서 이미 동일 패턴으로 수정 완료
- 이 슬라이스로 4개 계약 헤딩 패턴 통일 완료

## 핵심 변경
- "the next shipped surface is now also implemented as one read-only aggregate-level `reviewed_memory_transition_audit_contract` with" → "the current contract now also emits one read-only aggregate-level `reviewed_memory_transition_audit_contract` with"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES 4개 계약 헤딩(rollback/disable/conflict/transition-audit) current-emission 패턴 통일 완료
