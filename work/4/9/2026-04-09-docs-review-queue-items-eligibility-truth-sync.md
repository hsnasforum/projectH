# docs: review_queue_items summary eligibility truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Current Computed Session Payload Fields 섹션(line 232-235)에서 `review_queue_items` 파생 조건 명시
- `docs/ARCHITECTURE.md` — Current Persistence Surfaces 섹션(line 192-194)에서 동일 수정
- `docs/ACCEPTANCE_CRITERIA.md` — Session And Trace Gates 섹션(line 112)에서 동일 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 기존 요약은 "derived from current serialized grounded-brief source messages"로 generic 기술
- 실제 출하 동작:
  - `durable_candidate` 항목 중 `promotion_eligibility = eligible_for_review`이고 매칭하는 현재 `candidate_review_record`가 없는 항목에서만 파생
  - `app/serializers.py:4126-4194`, `tests/test_web_app.py:3488-3514, 3678-3726, 3890-3894`
- 더 정확한 문구가 이미 다른 섹션에 존재 (PRODUCT_SPEC:58, 117 등)

## 핵심 변경
- 3개 문서 모두에서 `review_queue_items` 파생 조건을 `durable_candidate` + `promotion_eligibility = eligible_for_review` + no matching `candidate_review_record`로 명시

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 각 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — `review_queue_items` 적격성 계약 진실 동기화 완료
