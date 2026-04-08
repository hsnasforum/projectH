# Docs task-log candidate confirmation-review detail field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`candidate_confirmation_recorded`와 `candidate_review_recorded`의 detail field shape이 이름만 나열된 상태. `app/handlers/aggregate.py:82-95,194-207`에서 이미 고정된 detail 객체를 로깅.

## 핵심 변경

### docs/ARCHITECTURE.md
- `candidate_confirmation_recorded`: `{message_id, artifact_id, source_message_id, candidate_id, candidate_family, candidate_updated_at, confirmation_scope, confirmation_label}`
- `candidate_review_recorded`: `{message_id, artifact_id, source_message_id, candidate_id, candidate_family, candidate_updated_at, review_scope, review_action, review_status}`

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- candidate action family core 필드 참조 및 ARCHITECTURE 참조 추가

## 검증

- 3개 문서 모두 candidate action detail 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- task-log action detail shape 문서화가 save-note, feedback/correction/verdict, candidate, agent_response, reviewed-memory 모든 주요 family에서 완료됨.
- system-level preference action(`preference_activated`, `preference_paused`, `preference_rejected`)은 내부 전용으로 문서화 범위 밖.
