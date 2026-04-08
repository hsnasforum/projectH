# Docs PRODUCT_SPEC ACCEPTANCE_CRITERIA ARCHITECTURE task-log cancel-permission-ocr action truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

shipped user-visible 보조 action(`stream_cancel_requested`, `web_search_permission_updated`, `permissions_updated`, `ocr_not_supported`)이 task-log docs에서 누락. 이 action들은 streaming cancel, web-search permission 변경, OCR 미지원 안내 등 현재 shipped browser-visible 흐름에 해당.

## 핵심 변경

### docs/PRODUCT_SPEC.md
- task-log 요약에 stream-cancel, permission updates, OCR guidance action 추가

### docs/ACCEPTANCE_CRITERIA.md
- shipped action 목록에 4개 보조 action 추가 (총 19개)

### docs/ARCHITECTURE.md
- action inventory에 4개 보조 action 추가

## 검증

- 3개 문서 모두 4개 보조 action 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 내부 처리 action(`agent_response`, `read_file`, `summarize_file`, `web_search_retried`, `request_intent_classified` 등)은 여전히 문서화 범위 밖.
