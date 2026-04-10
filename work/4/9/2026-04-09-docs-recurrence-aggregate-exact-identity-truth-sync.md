# docs: ACCEPTANCE_CRITERIA recurrence_aggregate_candidates exact-identity truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — Session And Trace Gates 섹션(line 110)에서 `recurrence_aggregate_candidates` 파생 조건 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 기존 요약은 "computed top-level list, separate from source-message fields"로 generic 기술
- 실제 출하 동작:
  - 현재 세션의 직렬화된 소스 메시지 `candidate_recurrence_key` 레코드에서 파생
  - 2개 이상의 distinct grounded-brief 앵커가 동일한 exact recurrence identity를 공유할 때만 생성
  - `app/serializers.py:3902-4124`, `tests/test_web_app.py:1125-1185`, `tests/test_smoke.py:5056-5165`
- 더 정확한 문구가 이미 다른 섹션에 존재 (PRODUCT_SPEC:59, 225-228, ARCHITECTURE:77, 187-189, ACCEPTANCE_CRITERIA:52)

## 핵심 변경
- 파생 조건을 `candidate_recurrence_key` 레코드 기반 + 2개 이상 distinct 앵커 + 동일 exact recurrence identity로 명시

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — `recurrence_aggregate_candidates` exact-identity 파생 계약 진실 동기화 완료
