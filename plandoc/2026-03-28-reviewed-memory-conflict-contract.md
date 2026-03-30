# 2026-03-28 reviewed-memory conflict contract

## 배경

같은 세션의 `recurrence_aggregate_candidates`는 이제 read-only `aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`를 함께 노출합니다. 이번 문서의 conflict contract와 그 first read-only surface도 이제 shipped 되었고, current payload에서 conflict-visible scope boundary를 inspect할 수 있습니다.

현재 shipped contract는 여전히 document-first MVP이며, reviewed-memory store/apply, repeated-signal promotion, cross-session counting, user-level memory는 열지 않습니다.

## 현재 사실

- `candidate_review_record`는 one source-message reviewed-but-not-applied trace입니다.
- `review_queue_items`는 source-message review queue입니다.
- `candidate_recurrence_key`는 one source-message recurrence primitive입니다.
- `recurrence_aggregate_candidates`는 same-session cross-source grouping surface입니다.
- `aggregate_promotion_marker`는 blocked promotion marker입니다.
- `reviewed_memory_precondition_status`는 blocked-only precondition surface입니다.
- `reviewed_memory_boundary_draft`는 fixed narrow reviewed scope를 가리키는 future boundary draft입니다.
- `reviewed_memory_rollback_contract`는 same aggregate 위의 future rollback-target contract입니다.
- `reviewed_memory_disable_contract`는 same aggregate 위의 future stop-apply-target contract입니다.
- `reviewed_memory_conflict_contract`는 same aggregate 위의 future conflict-visible-scope contract입니다.

이들 중 어느 것도 reviewed-memory apply result, conflict resolver, conflict store, cross-session scope가 아닙니다.

## 결정

### 1. `conflict_visible_reviewed_memory_scope`의 exact 의미

`conflict_visible_reviewed_memory_scope`는 one reviewed scope 안에서 competing reviewed-memory targets를 operator가 later apply 전에 read-only로 볼 수 있어야 한다는 뜻입니다.

의미하는 것:
- same reviewed scope 안의 competing reviewed-memory targets visibility
- same-session aggregate identity와 its exact supporting refs 위에서 충돌을 숨기지 않는 later machinery
- apply 전에 visible conflict surface를 보장하는 contract

의미하지 않는 것:
- source-message `corrected_text` diff viewer
- current `candidate_review_record` 자체를 conflict object로 승격
- `candidate_recurrence_key` 삭제 또는 재계산
- `recurrence_aggregate_candidates` identity history 수정
- current boundary/rollback/disable contracts를 곧바로 conflict resolver로 취급

### 2. first conflict target boundary

첫 conflict-visible scope는 `same_session_exact_recurrence_aggregate_only`로 고정합니다.

첫 visible conflict categories:
- `future_reviewed_memory_candidate_draft_vs_applied_effect`
- `future_applied_reviewed_memory_effect_vs_applied_effect`

고정 규칙:
- one current aggregate identity plus its exact supporting refs에 묶입니다
- current `reviewed_memory_boundary_draft`, current `reviewed_memory_rollback_contract`, current `reviewed_memory_disable_contract`는 basis ref 또는 neighboring contract로 남고 conflict object가 아닙니다
- conflict visibility는 auto-resolve, auto-disable, auto-rollback, auto-apply를 포함하지 않습니다

conflict visibility 이후에도 남아야 하는 것:
- `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- `reviewed_memory_boundary_draft`
- `reviewed_memory_rollback_contract`
- `reviewed_memory_disable_contract`
- operator-visible audit trace expectation

### 3. rollback / disable과의 관계

conflict visibility는 rollback, disable과 separate later machinery로 유지합니다.

- rollback = already-applied reviewed-memory effect reversal
- disable = already-applied reviewed-memory effect stop-apply without reversal
- conflict visibility = same reviewed scope 안의 competing targets를 operator가 볼 수 있게 하는 read-only surface

따라서:
- conflict visibility != rollback
- conflict visibility != disable
- conflict visibility != review reject
- conflict visibility != candidate dismissal
- current boundary/rollback/disable contracts는 conflict state machine이 아닙니다

### 4. operator-audit와의 관계

conflict contract는 operator-audit보다 먼저, 또는 별도로 닫혀야 합니다. 먼저 “무엇이 conflict로 보이는가”가 정의되어야 이후 transition audit schema가 정직해지기 때문입니다.

하지만 conflict contract alone으로 unblock 되면 안 됩니다.

- `operator_auditable_reviewed_memory_transition`는 conflict visibility 이후의 transition trace를 explicit local 기록으로 남기는 separate machinery입니다.
- current append-only `task_log`는 audit mirror일 수 있어도 canonical reviewed-memory conflict store가 아닙니다.

## 현재 shipped conflict-contract shape

현재 가장 작은 shipped surface는 one read-only `reviewed_memory_conflict_contract`입니다.

current shape:
- `conflict_version = first_reviewed_memory_scope_visibility_v1`
- `reviewed_scope = same_session_exact_recurrence_aggregate_only`
- `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- `conflict_target_categories`
  - `future_reviewed_memory_candidate_draft_vs_applied_effect`
  - `future_applied_reviewed_memory_effect_vs_applied_effect`
- `conflict_visibility_stage = contract_only_not_resolved`
- `audit_trace_expectation = operator_visible_local_transition_required`
- `defined_at = aggregate.last_seen_at`

이 object는 still read-only contract입니다.

열지 않는 것:
- reviewed-memory store
- reviewed-memory apply result
- conflict resolver
- operator repair
- cross-session scope

## cross-session boundary

conflict-visible reviewed-memory scope도 same-session-first로 유지합니다.

이유:
- first conflict-visible scope는 one current same-session aggregate identity와 its exact supporting refs에 묶입니다
- cross-session counting은 별도의 local store, stale-resolution, conflict-repair rules가 더 필요합니다
- conflict visibility가 정의되어도 cross-session counting은 자동으로 열리지 않습니다

따라서 same-session aggregate가 여전히 honest boundary입니다.

## confidence / threshold

- `confidence_marker = same_session_exact_key_match`는 현재 그대로 충분합니다
- conflict-visible contract가 정의되어도 second conservative confidence level은 자동으로 열리지 않습니다
- threshold 2 grounded briefs도 그대로 유지합니다
- category별 threshold tuning은 later question입니다

## 추천 next slice

다음 구현 slice는 `operator_auditable_reviewed_memory_transition` exact contract를 먼저 좁게 고정하는 쪽이 가장 작습니다.

이 slice가 먼저여야 하는 이유:
- boundary draft, rollback contract, disable contract, conflict contract는 모두 shipped 되었지만 operator-visible transition trace contract는 아직 없습니다
- reviewed-memory apply, repeated-signal promotion, cross-session counting보다 훨씬 좁고 honest합니다
- conflict-visible scope를 먼저 고정해야 later operator-audit contract도 과장 없이 닫을 수 있습니다
