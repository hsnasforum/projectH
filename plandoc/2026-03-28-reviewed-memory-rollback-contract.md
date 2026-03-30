# 2026-03-28 reviewed-memory rollback contract

## 배경

같은 세션의 `recurrence_aggregate_candidates`는 이제 read-only `aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`를 함께 노출합니다. 이번 문서의 contract와 그 first read-only surface는 이제 shipped 되었고, current payload에서 rollback target boundary를 inspect할 수 있습니다.

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

이들 중 어느 것도 reviewed-memory apply result나 rollback-capable effect record가 아닙니다.

## 결정

### 1. `rollback_ready_reviewed_memory_effect`의 exact 의미

`rollback_ready_reviewed_memory_effect`는 future reviewed-memory layer가 one later applied reviewed-memory effect를 explicit local operator action으로 되돌릴 수 있어야 한다는 뜻입니다.

의미하는 것:
- later reviewed-memory effect reversal
- later applied effect의 future influence stop
- explicit local operator-driven reversal trace

의미하지 않는 것:
- source-message `corrected_text` 되감기
- current `candidate_review_record` 삭제
- current `candidate_recurrence_key` 삭제
- `recurrence_aggregate_candidates` identity history 수정
- `reviewed_memory_boundary_draft` 자체 삭제를 canonical rollback으로 취급

### 2. first rollback target boundary

첫 rollback target은 current boundary draft가 아니라 one later applied reviewed-memory effect입니다.

고정 규칙:
- reviewed scope는 `same_session_exact_recurrence_aggregate_only`
- rollback target은 그 scope 안의 one later applied reviewed-memory effect only
- current `reviewed_memory_boundary_draft`는 scope draft이자 basis ref로 남고 rollback target이 아닙니다

rollback 이후 남아야 하는 것:
- `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- `reviewed_memory_boundary_draft`
- operator-visible audit trace

rollback 이후 비활성화될 수 있는 것:
- later applied reviewed-memory effect only
- 그 effect의 future influence only

### 3. disable과의 관계

rollback과 disable은 separate later machinery로 유지합니다.

- rollback = already-applied reviewed-memory effect reversal
- disable = later stop-apply machinery

따라서:
- rollback != delete
- disable != review reject
- disable != candidate dismissal
- current boundary draft는 rollback/disable state machine이 아닙니다

### 4. conflict / operator-audit와의 관계

rollback target contract는 conflict visibility와 operator audit보다 먼저, 또는 별도로 닫혀야 합니다. 먼저 “무엇을 되돌리는가”가 정의되어야 이후 conflict repair와 operator trace schema를 정직하게 설계할 수 있기 때문입니다.

하지만 rollback contract alone으로 unblock 되면 안 됩니다.

- `conflict_visible_reviewed_memory_scope`는 same reviewed scope 안에서 conflicting reviewed effects/signals를 보여주는 separate machinery입니다.
- `operator_auditable_reviewed_memory_transition`는 rollback/refire/disable/change를 explicit local trace로 남기는 separate machinery입니다.
- current append-only `task_log`는 audit mirror일 수 있어도 canonical reviewed-memory rollback store가 아닙니다.

## 현재 shipped rollback-contract shape

현재 가장 작은 shipped surface는 one read-only `reviewed_memory_rollback_contract`입니다.

current shape:
- `rollback_version = first_reviewed_memory_effect_reversal_v1`
- `reviewed_scope = same_session_exact_recurrence_aggregate_only`
- `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- `rollback_target_kind = future_applied_reviewed_memory_effect_only`
- `rollback_stage = contract_only_not_applied`
- `audit_trace_expectation = operator_visible_local_transition_required`
- `defined_at = aggregate.last_seen_at`

이 object는 still read-only contract입니다.

열지 않는 것:
- reviewed-memory store
- reviewed-memory apply result
- rollback state machine
- disable state machine
- cross-session scope

## cross-session boundary

rollback-ready reviewed-memory effect도 same-session-first로 유지합니다.

이유:
- first rollback target은 one current same-session aggregate identity와 its exact supporting refs에 묶입니다
- cross-session counting은 별도의 local store, stale-resolution, conflict-repair rules가 필요합니다
- rollback target이 정의되어도 cross-session counting은 자동으로 열리지 않습니다

따라서 same-session aggregate가 여전히 honest boundary입니다.

## confidence / threshold

- `confidence_marker = same_session_exact_key_match`는 현재 그대로 충분합니다
- rollback contract가 정의되어도 second conservative confidence level은 자동으로 열리지 않습니다
- threshold 2 grounded briefs도 그대로 유지합니다
- category별 threshold tuning은 later question입니다

## 추천 next slice

다음 구현 slice는 `disable_ready_reviewed_memory_effect` exact contract를 먼저 좁게 고정하는 쪽이 가장 작습니다.

이 slice가 먼저여야 하는 이유:
- rollback target contract는 이제 shipped 되었지만 stop-apply semantics는 여전히 닫혀 있습니다
- reviewed-memory apply, repeated-signal promotion, cross-session counting보다 훨씬 좁고 honest합니다
- rollback reversal과 disable stop-apply를 separate machinery로 유지해야 later state confusion을 막을 수 있습니다
