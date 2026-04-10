# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA session message field ownership truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Current Message Fields 섹션(line 247-281)에서 보정/승인 트레이스 필드에 소유권 주석 추가, 섹션 끝에 소유권 요약 문단 추가
- `docs/ACCEPTANCE_CRITERIA.md` — per-message 필드 목록(line 100-101)에서 보정/승인 트레이스 필드 소유권 구분 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 기존 문서는 optional 필드를 모든 메시지에 나타날 수 있는 것처럼 기술
- 실제 출하 동작:
  - `original_response_snapshot`, `corrected_text`, `corrected_outcome`, `content_reason_record`는 원본 grounded-brief 소스 메시지에만 존재
  - `approval_reason_record`는 거절/재발행 승인 트레이스 메시지에만 존재
  - `save_content_source`, `source_message_id`는 저장/승인 트레이스 메시지에만 존재
  - 비소스 시스템 메시지는 보정 진실 소스 표면이 아님
- `core/agent_loop.py:7336-7387`, `app/serializers.py:96-131`, `tests/test_web_app.py:6198-6199` 등에서 확인

## 핵심 변경
- PRODUCT_SPEC: 6개 필드에 소유 메시지 유형 주석 추가 + 소유권 요약 문단 추가
- ACCEPTANCE_CRITERIA: 보정 필드/승인 트레이스 필드를 별도 항목으로 분리하여 소유권 명시

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 13줄 추가 / 9줄 제거 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 세션 메시지 필드 소유권 진실 동기화 완료
