# docs: NEXT_STEPS local effect presence chain shipped qualifier truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — 6곳(line 308, 315, 329, 340, 351, 378): local-effect-presence 블록의 "future"/"later"/"should stay" 수식어 → "now-materialized"/"is"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 동일 블록의 line 304-314에서 이미 "current implementation now also evaluates/materializes"로 구체화 완료 기술
- 권위 문서(PRODUCT_SPEC:1312-1313, ARCHITECTURE:1051-1062, ACCEPTANCE_CRITERIA:994-1004)도 이미 구체화 반영
- 그러나 동일 블록 후속 행에서 동일 헬퍼를 "future"/"later" 수식어로 기술하여 모순

## 핵심 변경
- proof record: "later canonical local proof record" → "now-materialized"
- rollback handle: "future rollback-capability backer" → "now-materialized"
- target: "later local target" → "now-materialized"
- fact source: "later local fact source" → "now-materialized"
- event: "later local effect-presence event" → "now-materialized"
- shared target: "shared by later rollback and later disable handles" → "shared by the now-materialized rollback handle (and later disable handles when implemented)"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 6줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — NEXT_STEPS local-effect-presence 체인 shipped 수식어 진실 동기화 완료
