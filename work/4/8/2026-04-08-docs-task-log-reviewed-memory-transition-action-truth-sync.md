# Docs task-log reviewed-memory transition action truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

shipped reviewed-memory transition/conflict action 6개가 task-log docs에서 누락. 이 action들은 aggregate reviewed-memory UI에서 emit, apply, confirm result, stop, reverse, conflict check 흐름에 해당하며 `app/handlers/aggregate.py`에서 이미 로깅됨.

## 핵심 변경

3개 문서에 다음 6개 action 추가 (총 shipped action 28개):
- `reviewed_memory_transition_emitted`
- `reviewed_memory_transition_applied`
- `reviewed_memory_transition_result_confirmed`
- `reviewed_memory_transition_stopped`
- `reviewed_memory_transition_reversed`
- `reviewed_memory_conflict_visibility_checked`

## 검증

- 3개 문서 모두 6개 action 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- system-level preference action(`preference_activated`, `preference_paused`, `preference_rejected`)은 여전히 문서화 범위 밖.
