# Docs task-log reviewed-memory transition detail truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

reviewed-memory transition 6개 action이 ARCHITECTURE에서 이름만 나열. `app/handlers/aggregate.py:279-669`에서 각각 고정 detail 객체를 로깅.

## 핵심 변경

### docs/ARCHITECTURE.md
6개 reviewed-memory transition action per-action detail shape 추가:
- `reviewed_memory_transition_emitted`: `{canonical_transition_id, transition_action, aggregate_fingerprint, operator_reason_or_note, record_stage, emitted_at}`
- `reviewed_memory_transition_applied`: `{canonical_transition_id, transition_action, aggregate_fingerprint, record_stage, applied_at}`
- `reviewed_memory_transition_result_confirmed`: `{canonical_transition_id, aggregate_fingerprint, record_stage, applied_effect_kind, result_stage, result_at}`
- `reviewed_memory_transition_stopped`: `{canonical_transition_id, aggregate_fingerprint, record_stage, stopped_at}`
- `reviewed_memory_transition_reversed`: `{canonical_transition_id, aggregate_fingerprint, record_stage, reversed_at}`
- `reviewed_memory_conflict_visibility_checked`: `{canonical_transition_id, transition_action, aggregate_fingerprint, source_apply_transition_ref, conflict_entry_count, record_stage, checked_at}`

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- reviewed-memory transition action family ARCHITECTURE 참조 추가

## 검증

- 3개 문서 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `request_received`, `request_cancelled`, `document_context_updated`의 detail shape은 request plumbing 범위.
- 이들을 제외하면 현재 shipped task-log action의 모든 주요 family에서 detail shape 문서화 완료.
