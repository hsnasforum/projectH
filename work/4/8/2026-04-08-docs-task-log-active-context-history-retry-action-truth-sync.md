# Docs task-log active-context-history-retry action truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

user-visible 보조 action 3개(`web_search_retried`, `web_search_record_loaded`, `answer_with_active_context`)가 task-log docs에서 누락. 이 action들은 피드백 재시도, 검색 이력 reload, active-context follow-up 응답 등 shipped browser-visible 흐름에 해당하며 테스트에서도 커버됨.

## 핵심 변경

3개 문서에 `web_search_record_loaded`, `web_search_retried`, `answer_with_active_context` 추가 (총 shipped action 22개).

## 검증

- 3개 문서 모두 3개 action 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 내부 처리 action(`agent_response`, `request_intent_classified`, `read_file`, `summarize_file` 등)은 여전히 문서화 범위 밖.
