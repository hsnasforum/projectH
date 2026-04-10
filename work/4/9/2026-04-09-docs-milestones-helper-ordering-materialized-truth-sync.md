# docs: MILESTONES local effect presence helper current-materialized wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 5곳(line 296, 298-299, 300, 301, 304): helper ordering 블록의 "future"/"later" 수식어 제거, "now-materialized"/"now-shipped" 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 동일 블록 line 288-295에서 이미 "current implementation now evaluates/materializes"로 기술
- 권위 문서(PRODUCT_SPEC:1314-1329, ARCHITECTURE:1063-1100, ACCEPTANCE_CRITERIA:1005-1053)도 이미 "now-materialized" 프레이밍
- line 296-304만 "future"/"later" 수식어 잔존

## 핵심 변경
- rollback handle: "future rollback-capability backer" → "now-materialized"
- target: "later local target" → "now-materialized", "later rollback and later disable handles" → "now-materialized rollback handle (and later disable handles when implemented)"
- fact source: "later local fact source" → "now-materialized"
- event: "later local event" → "now-materialized"
- basis ordering: "below any later emitted transition record" → "below the now-shipped emitted transition record"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 6줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES helper ordering 블록 materialized 수식어 진실 동기화 완료
