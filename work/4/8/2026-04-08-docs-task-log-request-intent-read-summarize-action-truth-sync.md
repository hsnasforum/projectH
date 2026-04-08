# Docs task-log request-intent-read-summarize action truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

document-loop의 핵심 action 7개(`request_intent_classified`, `read_search_results`, `summarize_search_results`, `read_uploaded_file`, `summarize_uploaded_file`, `read_file`, `summarize_file`)가 task-log docs에서 누락. 이들은 shipped file summary, uploaded-file summary, document search 흐름을 직접 backing.

## 핵심 변경

### docs/ARCHITECTURE.md
7개 document-loop action per-action detail shape 추가

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- document-loop action family ARCHITECTURE 참조 추가

## 검증

- 3개 문서 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `agent_error` 등 error-path action은 별도 범위.
- system-level preference action은 시스템 내부 전용 유지.
- 이로써 shipped task-log action의 모든 주요 document-loop/web-search/approval/feedback/candidate/reviewed-memory family에서 detail shape 문서화 완료.
