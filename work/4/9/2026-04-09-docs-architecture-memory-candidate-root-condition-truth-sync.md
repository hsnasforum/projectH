# docs: ARCHITECTURE memory-candidate root condition truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — Current message records의 grounded-brief 소스 메시지 섹션(line 222-229)에서 8개 메모리/후보 필드에 조건 주석 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 슬라이스에서 PRODUCT_SPEC과 ACCEPTANCE_CRITERIA에는 이미 조건 주석 추가 완료
- ARCHITECTURE만 generic 목록으로 남아 3개 문서 간 상세 수준 불일치
- 출하 동작:
  - `session_local_memory_signal`은 `original_response_snapshot` 필요 (`storage/session_store.py:519-530`)
  - `session_local_candidate`/`candidate_recurrence_key`는 소스 메시지 앵커 필요 (`app/serializers.py:4354-4465`)
  - `candidate_confirmation_record`/`durable_candidate`/`candidate_review_record`는 시블링/조인 관계 (`app/serializers.py:164-212, 4238-4255`)

## 핵심 변경
- `session_local_memory_signal`: `requires original_response_snapshot` 추가
- `session_local_candidate`: `requires same source-message anchor` 추가
- `candidate_confirmation_record`: `sibling of session_local_candidate` 추가
- `candidate_recurrence_key`: `sibling of session_local_candidate` 추가
- `durable_candidate`: `sibling of session_local_candidate + candidate_confirmation_record` 추가
- `candidate_review_record`: `resolves when durable_candidate join matches` 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 6줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 3개 권위 문서 모두 세션 메시지 메모리/후보 루트 조건 진실 동기화 완료
