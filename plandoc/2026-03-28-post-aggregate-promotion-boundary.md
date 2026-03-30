# 2026-03-28 Post-Aggregate Promotion Boundary

## Status

- Document status: next-phase design contract
- Current shipped contract: local-first document assistant web MVP
- This document does not describe implemented repeated-signal promotion, reviewed-memory store, user-level memory, or cross-session counting

## Current Shipped Facts

- grounded-brief source messages already carry:
  - `artifact_id`
  - `source_message_id`
  - `original_response_snapshot`
  - `session_local_memory_signal`
  - `superseded_reject_signal`
  - `historical_save_identity_signal`
  - optional `session_local_candidate`
  - optional `candidate_confirmation_record`
  - optional `candidate_recurrence_key`
  - optional `durable_candidate`
  - optional `candidate_review_record`
- current session payloads may expose:
  - pending `review_queue_items`
  - same-session-only read-only `recurrence_aggregate_candidates`
- current review slice is:
  - `accept` only
  - reviewed-but-not-applied only
  - no reviewed-memory store
  - no user-level memory
- current `recurrence_aggregate_candidates` are:
  - same-session only
  - read-only
  - exact recurrence identity only
  - emitted only when at least two distinct grounded-brief anchors share that identity
  - `confidence_marker = same_session_exact_key_match`

## Contract Goal

Define the first boundary above shipped same-session aggregates without pretending that the repo already has repeated-signal promotion, reviewed memory, user-level memory, or cross-session counting.

## 1. Promotion Eligibility Choice

- Choose `Option A`.
- Current same-session `recurrence_aggregate_candidates` remain promotion-ineligible.
- Exact same-session aggregate identity is necessary, but still not sufficient, for any later promotion work.

Why this is the smallest honest choice:

- it stays local-first because current persisted session state is enough to explain the aggregate, but not enough to justify reviewed memory
- it stays approval-safe because no aggregate is silently upgraded into durable reviewed memory
- it stays audit-friendly because there is still no rollback / disable / conflict surface above the aggregate
- it avoids confusing same-session grouping with reviewed memory or user-level memory
- it keeps repeated-signal promotion later than the boundary that would need to govern mistaken grouping, disable, and rollback

## 2. Promotion Basis Boundary Above Aggregates

### Necessary Basis

- one current same-session `recurrence_aggregate_candidates` item
- one exact aggregate identity match:
  - `candidate_family`
  - `key_scope`
  - `key_version`
  - `derivation_source`
  - `normalized_delta_fingerprint`
- at least two distinct grounded-brief source-message anchors

### Confidence Support Only

- current `durable_candidate` only when it still matches the same source-message candidate version
- current `candidate_review_record` only when it still matches the same source-message candidate version
- current review acceptance only as confidence support carried by those exact source-message review refs

### Supporting Context Only

- `session_local_memory_signal`
- `superseded_reject_signal`
- `historical_save_identity_signal`
- approval-backed save support

### Never Basis

- `candidate_family` alone
- fixed statement text alone
- review acceptance alone
- queue presence alone
- approval-backed save alone
- historical adjunct alone
- task-log replay alone

## 3. First Reviewed-Memory Boundary

- future reviewed memory is not the same thing as current source-message review traces or current same-session aggregates
- future reviewed memory should mean:
  - explicit local memory above source-message and aggregate surfaces
  - rollbackable
  - disableable
  - conflict-visible
  - operator-auditable
- current `candidate_review_record` is narrower:
  - one source-message candidate version only
  - reviewed-but-not-applied only
  - no scope selection
  - no rollback / disable / conflict contract
- current `recurrence_aggregate_candidates` is also narrower:
  - same-session grouping only
  - no apply semantics
  - no reviewed-memory state

Why reviewed memory is still later:

- apply without rollback would overclaim durable personalization
- cross-source grouping mistakes need visible operator correction before any reviewed-memory apply can be trusted
- reviewed memory is still not user-level memory:
  - reviewed memory is one explicit local reviewed layer
  - user-level memory is a broader later reuse layer with wider persistence and scope behavior

## 4. Minimum Post-Aggregate Shape

- The current contract is now implemented as the smallest blocked marker only:
  - every current same-session aggregate stays blocked
  - no reviewed-memory candidate store opens
  - no repeated-signal promotion object opens

Current read-only aggregate-level marker shape:

- `aggregate_promotion_marker`
- `promotion_basis = same_session_exact_recurrence_aggregate`
- `promotion_eligibility = blocked_pending_reviewed_memory_boundary`
- `reviewed_memory_boundary = not_open`
- `marker_version = same_session_blocked_reviewed_memory_v1`
- `derived_at = last_seen_at`

Rules:

- do not overwrite `recurrence_aggregate_candidates`
- do not reuse `review_queue_items`
- do not create a second canonical store
- do not imply apply, promotion, or reviewed memory

## 5. Relationship To Current Review Layer

- `review_queue_items`
  - remain the pending-only source-message review surface
  - are not the aggregate surface
  - are not the post-aggregate promotion surface
- `candidate_review_record`
  - remains the reviewed-but-not-applied trace for one current source-message candidate version
  - may strengthen later aggregate-level confidence
  - must not replace aggregate identity
- `recurrence_aggregate_candidates`
  - remains the first same-session cross-source grouping surface
  - still stops before promotion and before reviewed memory

Why this comes before broader review actions:

- `edit` / `reject` / `defer` still operate on one source-message candidate version
- they do not solve the missing boundary above aggregate grouping
- the repo needs that boundary before repeated-signal promotion, broader durable promotion, or reviewed-memory work can be honest

## 6. Cross-Session Boundary

- cross-session counting is still closed
- same-session-only remains the honest current boundary because:
  - current persisted session state already explains the aggregate
  - no cross-session reviewed-memory or rollback store exists
  - no cross-session conflict resolution exists
  - no operator-visible correction surface exists for mistaken cross-session grouping

Cross-session work should remain later than:

- explicit local reviewed-memory/store choice
- rollback and disable behavior
- conflict handling across sessions
- stale or superseded-candidate treatment across reloads
- operator-visible audit and repair of mistaken grouping

## 7. Confidence Marker And Threshold

- current fixed `confidence_marker = same_session_exact_key_match` is enough for now
- reason:
  - it states only what is already proven
  - it does not pretend that review acceptance or save support already means reviewed memory
- later a second conservative level may be justified only if:
  - broader review vocabulary exists
  - reviewed-memory boundary rules exist
  - exact support conditions can be explained without overclaiming
- default recurrence threshold stays `2` for now
- category-specific threshold tuning remains later because the current repo still has only one shipped family and no reviewed-memory layer

## 8. Recommended Next Implementation Slice

- Recommend defining the exact rollback / disable / conflict / operator-audit preconditions that would be required before any same-session aggregate can stop being `blocked_pending_reviewed_memory_boundary`.

Why this is the smallest next slice:

- it stays smaller than reviewed-memory store or apply semantics
- it keeps current aggregates promotion-ineligible instead of pretending promotion is ready
- it defines the missing operator-safety boundary above the already-shipped blocked marker
- it comes before repeated-signal promotion, reviewed-memory store, and cross-session counting because those would all overclaim behavior the repo cannot yet roll back or audit

## Open Questions

1. Which exact rollback, disable, conflict, and operator-audit preconditions should be required before any same-session aggregate can stop being `blocked_pending_reviewed_memory_boundary`?
2. Which exact local store and reviewed-memory preconditions should be mandatory before any cross-session counting opens?
3. Should the current fixed `confidence_marker = same_session_exact_key_match` remain enough until broader review vocabulary lands, or should a later second conservative level be added?
4. Should later candidate families keep the same baseline threshold of two, or define stricter family-specific thresholds?
