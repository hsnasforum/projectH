# docs: local event and event-source ordering qualifier truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 5곳(line 1378, 1394, 1395, 1406-1407): fact source 순서 행의 "any later unblocked/emitted/apply" → "now-shipped", event의 "later same-aggregate" → 제거, event-source "should stay" → "now-materialized", target sharing "later rollback/disable" → "now-materialized rollback (and later disable when implemented)"
- `docs/ARCHITECTURE.md` — 2곳(line 1074, 1100): event/event-source의 "later"/"should stay" → "now-materialized"
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 1052): event-source의 "must stay" → "now-materialized"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 동일 문서 내에서 이미 "current implementation now materializes"로 구체화 완료 기술
- 후속 순서/계층 설명 행에서 동일 헬퍼를 "later"/"should stay" 수식어로 기술하여 모순

## 핵심 변경
- fact source 순서: "any later unblocked/emitted/apply" → "now-shipped"
- event: "later same-aggregate event layer" → "same-aggregate event layer"
- event-source: "should stay" → "is one now-materialized"
- target sharing: "later rollback/disable handles" → "now-materialized rollback handle (and later disable handle when implemented)"

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 8줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — event/event-source/target 순서 수식어 진실 동기화 완료
