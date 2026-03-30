# 2026-03-28 reviewed-memory operator-audit contract

## 배경

같은 세션의 `recurrence_aggregate_candidates`는 이제 read-only `aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`, `reviewed_memory_transition_audit_contract`를 함께 노출합니다. boundary, rollback, disable, conflict contract에 이어 operator-audit contract와 그 first read-only surface도 이제 shipped 되었고, current payload에서 canonical transition-identity boundary를 inspect할 수 있습니다.

현재 shipped contract는 여전히 document-first MVP이며, reviewed-memory store/apply, repeated-signal promotion, cross-session counting, user-level memory는 열지 않습니다.

## 현재 사실

- `candidate_review_record`는 one source-message reviewed-but-not-applied trace입니다.
- `review_queue_items`는 source-message review queue입니다.
- `candidate_recurrence_key`는 one source-message recurrence primitive입니다.
- `recurrence_aggregate_candidates`는 same-session cross-source grouping surface입니다.
- `aggregate_promotion_marker`는 blocked promotion marker입니다.
- `reviewed_memory_precondition_status`는 blocked-only precondition surface입니다.
- `reviewed_memory_boundary_draft`는 future boundary draft입니다.
- `reviewed_memory_rollback_contract`는 future rollback-target contract입니다.
- `reviewed_memory_disable_contract`는 future stop-apply-target contract입니다.
- `reviewed_memory_conflict_contract`는 future conflict-visible-scope contract입니다.
- `reviewed_memory_transition_audit_contract`는 future canonical transition-identity contract입니다.

이들 중 어느 것도 canonical reviewed-memory transition record, reviewed-memory apply result, transition state machine, cross-session scope가 아닙니다.

## 결정

### 1. `operator_auditable_reviewed_memory_transition`의 exact 의미

`operator_auditable_reviewed_memory_transition`는 one later reviewed-memory layer transition이 explicit local operator-visible trace와 canonical transition identity를 남겨야 한다는 뜻입니다.

의미하는 것:
- later reviewed-memory transition마다 one canonical local transition identity
- operator가 transition reason, target, scope, timing을 local-first로 inspect할 수 있는 trace
- apply / stop-apply / reversal / conflict-visible transition 같은 later state change를 canonical vocabulary로 남기는 contract

의미하지 않는 것:
- current append-only `task_log` alone을 canonical reviewed-memory transition store로 승격
- current `candidate_review_record`를 transition record로 재해석
- `candidate_recurrence_key` 삭제 또는 재계산
- `recurrence_aggregate_candidates` identity history 수정
- current boundary / rollback / disable / conflict contracts를 transition result로 승격
- approval-backed save support, historical adjuncts, review acceptance, queue presence, and task-log replay alone로 canonical transition state를 만드는 것

### 2. first transition target boundary

first operator-audit scope는 `same_session_exact_recurrence_aggregate_only`로 고정합니다.

first transition action vocabulary:
- `future_reviewed_memory_apply`
- `future_reviewed_memory_stop_apply`
- `future_reviewed_memory_reversal`
- `future_reviewed_memory_conflict_visibility`

고정 규칙:
- one current aggregate identity plus its exact supporting refs에 묶입니다
- current `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`는 basis refs 또는 neighboring contracts로 남고 transition result가 아닙니다
- operator audit는 auto-apply, auto-disable, auto-rollback, auto-resolve, auto-repair를 포함하지 않습니다

transition 이후에도 남아야 하는 것:
- `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- `reviewed_memory_boundary_draft`
- `reviewed_memory_rollback_contract`
- `reviewed_memory_disable_contract`
- `reviewed_memory_conflict_contract`

### 3. `task_log`와의 관계

`task_log`는 audit mirror일 수 있어도 canonical reviewed-memory transition source가 아니어야 합니다.

이유:
- current append-only log alone으로 later transition state를 authoritative하게 복원하면 current state와 audit mirror를 섞게 됩니다
- operator-visible trace requirement는 exact transition identity, action vocabulary, reason boundary를 분리된 canonical contract로 남겨야 합니다
- `task_log` replay alone으로 reviewed-memory transition state를 복원하는 설계는 stale-resolution과 later conflict-repair를 과장하게 만듭니다

따라서:
- canonical transition record는 future reviewed-memory layer에 별도 존재해야 합니다
- current `task_log`는 mirror / export / appendix 역할만 가질 수 있습니다

### 4. rollback / disable / conflict와의 관계

operator audit는 rollback, disable, conflict와 separate later machinery로 유지합니다.

- rollback = already-applied reviewed-memory effect reversal target semantics
- disable = already-applied reviewed-memory effect stop-apply target semantics
- conflict visibility = same reviewed scope 안의 competing targets visibility semantics
- operator audit = those later transitions의 canonical local trace semantics

따라서:
- operator audit != rollback
- operator audit != disable
- operator audit != conflict resolution
- operator audit != review reject
- current boundary / rollback / disable / conflict contracts는 transition state machine이 아닙니다

## 현재 shipped operator-audit shape

현재 가장 작은 shipped surface는 one read-only `reviewed_memory_transition_audit_contract`입니다.

current shape:
- `audit_version = first_reviewed_memory_transition_identity_v1`
- `reviewed_scope = same_session_exact_recurrence_aggregate_only`
- `aggregate_identity_ref`
- `supporting_source_message_refs`
- `supporting_candidate_refs`
- optional `supporting_review_refs`
- `transition_action_vocabulary`
  - `future_reviewed_memory_apply`
  - `future_reviewed_memory_stop_apply`
  - `future_reviewed_memory_reversal`
  - `future_reviewed_memory_conflict_visibility`
- `transition_identity_requirement = canonical_local_transition_id_required`
- `operator_visible_reason_boundary = explicit_reason_or_note_required`
- `audit_stage = contract_only_not_emitted`
- `audit_store_boundary = canonical_transition_record_separate_from_task_log`
- `post_transition_invariants = aggregate_identity_and_contract_refs_retained`
- `defined_at = aggregate.last_seen_at`

이 object는 still read-only contract입니다.

열지 않는 것:
- reviewed-memory store
- reviewed-memory apply result
- transition state machine
- conflict resolver
- cross-session scope

## cross-session boundary

operator-auditable reviewed-memory transition도 same-session-first로 유지합니다.

이유:
- first operator-audit scope는 one current same-session aggregate identity와 its exact supporting refs에 묶입니다
- cross-session counting은 별도의 local store, stale-resolution, conflict-repair rules가 더 필요합니다
- operator-audit contract가 정의되어도 cross-session counting은 자동으로 열리지 않습니다

따라서 same-session aggregate가 여전히 honest boundary입니다.

## confidence / threshold

- `confidence_marker = same_session_exact_key_match`는 현재 그대로 충분합니다
- operator-audit contract가 정의되어도 second conservative confidence level은 자동으로 열리지 않습니다
- threshold 2 grounded briefs도 그대로 유지합니다
- category별 threshold tuning은 later question입니다

## 추천 next slice

다음 widening은 emitted transition record나 reviewed-memory apply가 아니라, same-session unblock semantics를 다시 문서로 좁게 고정하는 쪽이 가장 정직합니다.

이 slice가 먼저여야 하는 이유:
- boundary draft, rollback contract, disable contract, conflict contract, transition-audit contract까지는 모두 shipped 되었지만 canonical emitted transition record나 apply state는 아직 없습니다
- reviewed-memory apply, repeated-signal promotion, cross-session counting보다 훨씬 좁고 honest합니다
- operator audit contract를 shipped 한 뒤에도 precondition satisfaction widening을 바로 열면 blocked-only contract들을 과장하게 됩니다
