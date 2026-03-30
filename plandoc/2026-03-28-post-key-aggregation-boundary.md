# 2026-03-28 Post-Key Aggregation Boundary

## Status

- Document status: next-phase design contract
- Current shipped contract: local-first document assistant web MVP
- This document does not describe implemented aggregation, repeated-signal promotion, reviewed memory, or user-level memory

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
- current session payloads may expose pending `review_queue_items`
- current review slice is:
  - `accept` only
  - reviewed-but-not-applied only
  - no reviewed-memory store
  - no user-level memory
- `candidate_recurrence_key` is already shipped as:
  - source-message anchored
  - read-only
  - derived only from the explicit original-vs-corrected pair
  - deterministic and local-only
- repeated-signal promotion is still blocked

## Contract Goal

Define the first post-key aggregation boundary that can group distinct grounded-brief source messages truthfully without pretending that the repo already has cross-session counting, reviewed memory, or user-level memory.

## 1. First Aggregation Boundary

- The first aggregation boundary is same-session only.
- The first aggregation unit is:
  - the same exact `candidate_recurrence_key` identity
  - across at least two distinct grounded-brief source-message anchors
  - inside one current session payload only
- The first materialization should be one optional top-level session read-only projection:
  - `recurrence_aggregate_candidates`

Why this is the smallest honest boundary:

- it keeps current source-message truth primary
- it stays local-first because current persisted session state is enough
- it stays approval-safe because it does not turn review or save traces into automatic promotion
- it stays audit-friendly because every supporting input still points back to distinct source-message anchors
- it avoids overclaiming cross-session recurrence before store / rollback / conflict rules exist

## 2. Aggregate Identity

One aggregate identity should require the same:

- `candidate_family`
- `key_scope`
- `key_version`
- `derivation_source`
- `normalized_delta_fingerprint`

These identity fields must come from current shipped source-message `candidate_recurrence_key` records only.

These are not aggregate identity:

- `source_candidate_id`
- `source_candidate_updated_at`

Those fields remain source-message candidate-version refs only.

## 3. Allowed Basis Vs Forbidden Basis

### Basis

- same exact `candidate_recurrence_key` identity
- distinct grounded-brief source-message anchors
- current `durable_candidate` only when it still matches the same source-message candidate version
- current `candidate_review_record` only when it still matches the same source-message candidate version, and only as confidence support

### Supporting Context Only

- `session_local_memory_signal`
- `superseded_reject_signal`
- `historical_save_identity_signal`
- approval-backed save support
- `candidate_review_record` as later confidence support only

### Never Basis

- `candidate_family` alone
- fixed statement text alone
- review acceptance alone
- queue presence alone
- approval-backed save alone
- task-log replay alone
- historical adjunct alone

## 4. Minimum Aggregate Shape

The first future envelope should stay additive, computed, and read-only.

Suggested item shape:

- `aggregate_key`
  - `candidate_family`
  - `key_scope`
  - `key_version`
  - `derivation_source`
  - `normalized_delta_fingerprint`
- `supporting_source_message_refs`
  - `artifact_id`
  - `source_message_id`
- `supporting_candidate_refs`
  - `candidate_id`
  - `candidate_updated_at`
- optional `supporting_review_refs`
  - `candidate_id`
  - `candidate_updated_at`
  - `review_action`
  - `review_status`
  - `recorded_at`
- `recurrence_count`
- `scope_boundary = same_session_current_state_only`
- `confidence_marker`
- `first_seen_at`
- `last_seen_at`

Rules:

- no second canonical store
- no overwrite of source-message `candidate_recurrence_key`
- no reuse of `review_queue_items` as the aggregate surface
- no promotion or application semantics in the aggregate object itself

## 5. Distinctness And Threshold

- The first threshold should stay conservative:
  - at least two distinct grounded briefs
- Distinctness is anchored by different:
  - `artifact_id`
  - `source_message_id`
- Repeated edits on one source message do not count as multi-brief recurrence.
- Two is the first honest baseline for `correction_rewrite_preference` because one explicit corrected pair still proves only one-brief evidence.
- Later candidate families may require:
  - higher thresholds
  - reviewed support
  - family-specific constraints

## 6. Session Boundary

- The first aggregate boundary should stay same-session only.
- Current persisted session state is sufficient to compute that first boundary truthfully.
- Cross-session counting should remain closed until a later contract exists for:
  - explicit local aggregation or reviewed-memory store choice
  - rollback and disable behavior
  - conflict handling across sessions
  - stale or superseded candidate-version treatment across session reloads
  - operator-visible audit and correction of mistaken grouping

Reason:

- cross-session aggregation is not just counting
- it starts to overlap with reviewed-memory persistence, retention, rollback, and user-level memory boundaries
- opening it now would overclaim what the current MVP can honestly explain or audit

## 7. Relationship To Current Review Layer

- `review_queue_items`
  - remain the pending-only surface for current eligible `durable_candidate` items
  - are not the aggregation surface
- `candidate_review_record`
  - remains the reviewed-but-not-applied trace for one current source-message candidate version
  - may strengthen later aggregate confidence
  - must not replace aggregate identity
- `durable_candidate`
  - remains the current source-message explicit-confirmation projection
  - does not become a cross-source aggregate by itself
- future aggregation layer
  - is the smallest later cross-source reasoning surface
  - still stops before reviewed memory or user-level memory

Why this comes before broader review actions:

- `edit` / `reject` / `defer` still operate on one current source-message candidate version
- they do not solve the missing cross-source grouping problem
- the repo needs the smallest truthful aggregation contract before broader review vocabulary, reviewed-history hints, or repeated-signal promotion can be honest

## 8. Implementation Status

- this same-session-only read-only `recurrence_aggregate_candidates` slice is now implemented

Current shipped shape:

- one optional top-level session read-only `recurrence_aggregate_candidates`
- identity basis = exact current source-message `candidate_recurrence_key` match only
- minimum threshold = at least two distinct grounded-brief `artifact_id` + `source_message_id` anchors in the same session
- `supporting_candidate_refs` and optional `supporting_review_refs` stay exact current-version joins
- `confidence_marker` currently stays fixed at `same_session_exact_key_match`
- no promotion, no second store, no cross-session counting

## Open Questions

1. Should the current fixed `confidence_marker = same_session_exact_key_match` remain enough until broader review vocabulary lands, or should a later second conservative level be added?
2. Which local store, rollback, and reviewed-memory preconditions should be mandatory before any cross-session aggregation opens?
3. Should later candidate families keep the same baseline threshold of two, or define stricter family-specific thresholds?
