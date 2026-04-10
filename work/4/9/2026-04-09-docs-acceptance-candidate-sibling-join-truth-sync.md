# docs: ACCEPTANCE_CRITERIA candidate summary sibling join truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — per-message 후보 요약(line 107)에서 5개 후보 필드에 개별 시블링/조인 조건 주석 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- PRODUCT_SPEC(line 270-274)과 ARCHITECTURE(line 225-229)는 이미 개별 조건을 정확히 기술
- ACCEPTANCE_CRITERIA만 "same source-message anchor" 한 줄 요약으로 남아 조건 상세 누락
- 출하 동작:
  - `session_local_candidate`: 소스 메시지 앵커 필요
  - `candidate_confirmation_record`/`candidate_recurrence_key`: `session_local_candidate`의 시블링
  - `durable_candidate`: `session_local_candidate` + `candidate_confirmation_record` 조인 필요
  - `candidate_review_record`: `durable_candidate` 조인 일치 시에만 해소

## 핵심 변경
- 5개 후보 필드 각각에 개별 조건 괄호 주석 추가 (requires, sibling of, resolves when)

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 3개 권위 문서 모두 세션 메시지 후보 루트/시블링/조인 조건 상세 진실 동기화 완료. 응답 페이로드 + 세션 메시지 필드 소유권 family 전체 완료.
