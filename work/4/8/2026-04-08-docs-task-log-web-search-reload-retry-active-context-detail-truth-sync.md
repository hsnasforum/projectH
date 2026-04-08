# Docs task-log web-search reload-retry-active-context detail truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`web_search_record_loaded`, `web_search_retried`, `answer_with_active_context` 3개 action이 ARCHITECTURE에서 이름만 나열. 실제 코드에서 고정된 detail 객체를 로깅.

## 핵심 변경

### docs/ARCHITECTURE.md
- `web_search_record_loaded`: `{query, record_id, record_path, result_count}`
- `web_search_retried`: `{query, result_count, page_count, record_path, urls, search_queries, deprioritized_urls}`
- `answer_with_active_context`: `{label, source_paths, intent, conversation_mode, retrieved_chunk_count, selected_evidence_count, retry_feedback_label, retry_feedback_reason, retry_target_message_id}`

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- web-search/follow-up action family ARCHITECTURE 참조 추가

## 검증

- 3개 문서 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- task-log action detail shape 문서화가 모든 주요 user-visible action family에서 완료됨.
