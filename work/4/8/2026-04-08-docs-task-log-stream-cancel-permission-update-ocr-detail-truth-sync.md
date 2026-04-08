# Docs task-log stream-cancel-permission-update-ocr detail truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`stream_cancel_requested`, `web_search_permission_updated`, `permissions_updated`, `ocr_not_supported` 4개 singleton action이 ARCHITECTURE에서 이름만 나열. 코드에서 고정 detail 객체를 로깅.

## 핵심 변경

### docs/ARCHITECTURE.md
- `stream_cancel_requested`: `{request_id}`
- `web_search_permission_updated`: `{web_search}`
- `permissions_updated`: `{web_search}`
- `ocr_not_supported`: `{source_path, error}`

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- singleton action family ARCHITECTURE 참조 추가

## 검증

- 3개 문서 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `request_received`, `request_cancelled`, `document_context_updated`의 detail shape은 request plumbing 범위로 별도 문서화 대상.
- 이들을 제외하면 shipped user-visible task-log action detail shape 문서화가 완료됨.
