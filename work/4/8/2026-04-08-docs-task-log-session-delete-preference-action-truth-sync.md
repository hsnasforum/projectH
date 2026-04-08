# Docs task-log session-delete-preference action truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

마지막 5개 shipped task-log action(`session_deleted`, `all_sessions_deleted`, `preference_activated`, `preference_paused`, `preference_rejected`)이 docs에서 누락.

## 핵심 변경

3개 문서에 5개 admin/system maintenance action 추가:
- `session_deleted`: `{}` (admin path)
- `all_sessions_deleted`: `{count}` (admin path)
- `preference_activated`: `{preference_id}` (system maintenance)
- `preference_paused`: `{preference_id}` (system maintenance)
- `preference_rejected`: `{preference_id}` (system maintenance)

## 검증

- 3개 문서 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 이로써 shipped task-log의 모든 action이 authoritative docs에서 문서화 완료됨.
- task-log action detail shape 문서화 체인 종결.
