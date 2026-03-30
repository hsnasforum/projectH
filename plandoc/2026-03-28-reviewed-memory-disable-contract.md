# 2026-03-28 reviewed-memory disable contract

## 배경

같은 세션의 `recurrence_aggregate_candidates`는 이제 read-only `aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`를 함께 노출합니다. 이번 문서의 disable contract와 그 first read-only surface도 이제 shipped 되었고, current payload에서 stop-apply target boundary를 inspect할 수 있습니다.

현재 shipped contract는 여전히 document-first MVP이며, reviewed-memory store/apply, repeated-signal promotion, cross-session counting, user-level memory는 열지 않습니다.

## 현재 사실

- `candidate_review_record`는 one source-message reviewed-but-not-applied trace입니다.
- `review_queue_items`는 source-message review queue입니다.
- `candidate_recurrence_key`는 one source-message recurrence primitive입니다.
- `recurrence_aggregate_candidates`는 same-session cross-source grouping surface입니다.
- `aggregate_promotion_marker`는 blocked promotion marker입니다.
- `reviewed_memory_precondition_status`는 blocked-only precondition surface입니다.
- `reviewed_memory_boundary_draft`는 fixed narrow reviewed scope를 가리키는 future boundary draft입니다.
- `reviewed_memory_rollback_contract`는 same aggregate 위의 future rollback target contract를 가리키는 read-only object입니다.
- `reviewed_memory_disable_contract`는 same aggregate 위의 future stop-apply target contract를 가리키는 read-only object입니다.

이들 중 어느 것도 reviewed-memory apply result, disable-capable effect record, disable state machine이 아닙니다.

## 결정

### 1. `disable_ready_reviewed_memory_effect`의 exact 의미

`disable_ready_reviewed_memory_effect`는 future reviewed-memory layer가 one later applied reviewed-memory effect의 future influence를 explicit local operator action으로 stop-apply할 수 있어야 한다는 뜻입니다.

의미하는 것:
- later reviewed-memory effect stop-apply
- explicit local operator-driven stop-apply transition
- effect identity와 audit trace를 남긴 채 apply만 멈추는 later machinery

의미하지 않는 것:
- source-message `corrected_text` 삭제 또는 되감기
- current `candidate_review_record` 삭제
- current `candidate_recurrence_key` 삭제
- `recurrence_aggregate_candidates` identity history 수정
- `reviewed_memory_boundary_draft` 삭제
- `reviewed_memory_rollback_contract` 삭제
- rollback처럼 already-applied effect를 되감는 reversal 그 자체

### 2. first disable target boundary

첫 disable target은 current boundary draft나 current rollback contract가 아니라 one later applied reviewed-memory effect입니다.

고정 규칙:
- reviewed scope는 `same_session_exact_recurrence_aggregate_only`
- disable target은 그 scope 안의 one later applied reviewed-memory effect only
- current `reviewed_memory_boundary_draft`와 current `reviewed_memory_rollback_contract`는 basis ref로 남고 disable target이 아닙니다

disable 이후 남아야 하는 것:
- `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- `reviewed_memory_boundary_draft`
- `reviewed_memory_rollback_contract`
- operator-visible audit trace

disable 이후 비활성화될 수 있는 것:
- later applied reviewed-memory effect only
- 그 effect의 future influence only

### 3. rollback과의 관계

disable과 rollback은 separate later machinery로 유지합니다.

- rollback = already-applied reviewed-memory effect reversal
- disable = already-applied reviewed-memory effect stop-apply without reversal

따라서:
- rollback != disable
- disable != delete
- disable != review reject
- disable != candidate dismissal
- current boundary draft/rollback contract는 disable state machine이 아닙니다

### 4. conflict / operator-audit와의 관계

disable target contract는 conflict visibility와 operator audit보다 먼저, 또는 별도로 닫혀야 합니다. 먼저 “무엇을 stop-apply하는가”가 정의되어야 이후 disable trace와 conflict repair schema를 정직하게 설계할 수 있기 때문입니다.

하지만 disable contract alone으로 unblock 되면 안 됩니다.

- `conflict_visible_reviewed_memory_scope`는 same reviewed scope 안에서 conflicting reviewed effects/signals를 보여주는 separate machinery입니다.
- `operator_auditable_reviewed_memory_transition`는 disable/rollback/change를 explicit local trace로 남기는 separate machinery입니다.
- current append-only `task_log`는 audit mirror일 수 있어도 canonical reviewed-memory disable store가 아닙니다.

## 현재 shipped disable-contract shape

현재 가장 작은 shipped surface는 one read-only `reviewed_memory_disable_contract`입니다.

current shape:
- `disable_version = first_reviewed_memory_effect_stop_apply_v1`
- `reviewed_scope = same_session_exact_recurrence_aggregate_only`
- `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- `disable_target_kind = future_applied_reviewed_memory_effect_only`
- `disable_stage = contract_only_not_applied`
- `effect_behavior = stop_apply_without_reversal`
- `audit_trace_expectation = operator_visible_local_transition_required`
- `defined_at = aggregate.last_seen_at`

이 object는 still read-only contract입니다.

열지 않는 것:
- reviewed-memory store
- reviewed-memory apply result
- disable state machine
- rollback state machine
- cross-session scope

## cross-session boundary

disable-ready reviewed-memory effect도 same-session-first로 유지합니다.

이유:
- first disable target은 one current same-session aggregate identity와 its exact supporting refs에 묶입니다
- cross-session counting은 별도의 local store, stale-resolution, conflict-repair rules가 필요합니다
- disable target이 정의되어도 cross-session counting은 자동으로 열리지 않습니다

따라서 same-session aggregate가 여전히 honest boundary입니다.

## confidence / threshold

- `confidence_marker = same_session_exact_key_match`는 현재 그대로 충분합니다
- disable contract가 정의되어도 second conservative confidence level은 자동으로 열리지 않습니다
- threshold 2 grounded briefs도 그대로 유지합니다
- category별 threshold tuning은 later question입니다

## 추천 next slice

다음 구현 slice는 `conflict_visible_reviewed_memory_scope` exact contract를 먼저 좁게 고정하는 쪽이 가장 작습니다.

이 slice가 먼저여야 하는 이유:
- boundary draft, rollback contract, disable contract는 이제 모두 shipped 되었지만 conflict visibility는 여전히 exact contract가 없습니다
- reviewed-memory apply, repeated-signal promotion, cross-session counting보다 훨씬 좁고 honest합니다
- rollback reversal과 disable stop-apply 위에서 어떤 충돌을 보여야 하는지 먼저 고정해야 later state confusion을 막을 수 있습니다
