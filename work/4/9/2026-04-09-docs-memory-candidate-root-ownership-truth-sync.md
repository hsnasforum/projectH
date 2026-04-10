# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA memory-candidate root ownership truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Current Message Fields 섹션(line 267-274)에서 8개 메모리/후보 필드에 grounded-brief 소스 메시지 전용 소유권 주석 추가
- `docs/ACCEPTANCE_CRITERIA.md` — per-message 필드 목록(line 106-107)에서 메모리 시그널 및 후보 루트 소유권을 grounded-brief 소스 메시지 전용으로 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 기존 문서는 메모리/후보 필드를 generic "optional per-message"로 기술
- 실제 출하 동작:
  - `session_local_memory_signal` 등 메모리 시그널은 `original_response_snapshot`이 있는 grounded-brief 소스 메시지에서만 구체화 (`storage/session_store.py:519-575`)
  - `session_local_candidate`, `candidate_recurrence_key` 등은 동일 소스 메시지 앵커 필요 (`app/serializers.py:4354-4465`)
  - `candidate_review_record`는 현재 `durable_candidate` 조인이 일치할 때만 해소 (`app/serializers.py:4238-4255`)
- `docs/ARCHITECTURE.md:215-233`은 이미 소유권 기반으로 정확하게 기술

## 핵심 변경
- PRODUCT_SPEC: 8개 필드 각각에 `grounded-brief source message only` + 필요 조건(앵커, 시블링 관계) 주석 추가
- ACCEPTANCE_CRITERIA: 메모리 시그널 루트와 후보 루트/시블링을 grounded-brief 소스 메시지 전용으로 명시, `candidate_confirmation_record`/`candidate_recurrence_key`/`durable_candidate` 누락 보완

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 10줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 세션 메시지 메모리/후보 루트 소유권 진실 동기화가 3개 권위 문서 모두에서 완료
