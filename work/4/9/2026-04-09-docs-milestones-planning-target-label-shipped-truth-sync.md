# docs: MILESTONES planning_target_ref label current-shipped wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 307): "the next contract decision now also fixes readiness-target label narrowing" → "readiness-target label narrowing is now fixed and shipped"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 307이 "next contract decision now also fixes"로 프레이밍
- 권위 문서(PRODUCT_SPEC:1180-1198, ARCHITECTURE:909-916, ACCEPTANCE_CRITERIA:685-698)에서 이미 current shipped로 기술
- `eligible_for_reviewed_memory_draft_planning_only` 라벨과 planning-target 의미는 이미 출하 확정

## 핵심 변경
- "the next contract decision now also fixes readiness-target label narrowing" → "readiness-target label narrowing is now fixed and shipped"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES planning_target_ref 라벨 헤딩 shipped 진실 동기화 완료
