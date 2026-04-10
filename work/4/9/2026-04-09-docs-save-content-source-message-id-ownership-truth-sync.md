# docs: save_content_source source_message_id ownership truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Current Message Fields 섹션(line 277, 280)에서 소유권 주석 수정, 소유권 요약 문단 수정
- `docs/ACCEPTANCE_CRITERIA.md` — per-message 필드 목록(line 103)에서 소유권 주석 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 슬라이스에서 `save_content_source`와 `source_message_id`를 "save/approval trace messages 전용"으로 기술
- 실제 출하 동작은 더 넓음:
  - grounded-brief 소스 메시지가 직접 승인 저장 후 `save_content_source`와 `source_message_id`를 가질 수 있음
  - `storage/session_store.py:644-650`, `tests/test_web_app.py:6247-6262`, `tests/test_smoke.py:4409-4423`에서 확인
- "owned by save/approval trace messages" → "present on grounded-brief source messages (after direct approved save) and on save/approval trace messages"

## 핵심 변경
- PRODUCT_SPEC: 인라인 주석과 요약 문단에서 두 필드의 소유권을 소스 메시지 + 트레이스 메시지 양쪽으로 확장
- ACCEPTANCE_CRITERIA: 동일 소유권 확장

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 4줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — `save_content_source`/`source_message_id` 소유권 진실 동기화 완료
