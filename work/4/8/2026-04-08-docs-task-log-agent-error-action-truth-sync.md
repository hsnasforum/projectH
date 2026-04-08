# Docs task-log agent_error action truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`agent_error` action이 task-log docs에서 누락. `core/agent_loop.py:8789-8798`에서 error fallback 시 로깅.

## 핵심 변경

3개 문서에 `agent_error` action 추가 (detail: `{error}`).

## 검증

- 3개 문서 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `session_deleted`, `all_sessions_deleted`는 admin-path, `preference_*`는 system-level로 문서화 범위 밖 유지.
- 이 세션에서 약 47회 연속 docs micro-slice 실행됨. CLAUDE.md의 `Do not over-fragment` 지침에 따라 향후 docs 동기화는 한 번에 묶어 처리 권장.
