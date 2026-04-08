# Docs task-log request-received-cancelled-context-update detail truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`request_received`, `request_cancelled`, `document_context_updated` 3개 action이 ARCHITECTURE에서 이름만 나열. 실제 코드에서 고정 detail 객체를 로깅.

## 핵심 변경

### docs/ARCHITECTURE.md
- `request_received`: `{user_text, source_path, search_root, search_query, save_summary, approved, approved_approval_id, rejected_approval_id, reissue_approval_id, corrected_save_message_id, note_path, retry_feedback_label, retry_feedback_reason, retry_target_message_id}`
- `request_cancelled`: `{user_text, source_path, uploaded_file_name, search_root, search_query}`
- `document_context_updated`: `{kind, label, source_paths}`

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- request plumbing action family ARCHITECTURE 참조 추가

## 검증

- 3개 문서 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 이번 슬라이스로 shipped task-log의 모든 name-only action이 ARCHITECTURE에서 detail shape 기술 완료됨.
- system-level preference action(`preference_activated`, `preference_paused`, `preference_rejected`)은 시스템 내부 전용으로 문서화 범위 밖 유지.
