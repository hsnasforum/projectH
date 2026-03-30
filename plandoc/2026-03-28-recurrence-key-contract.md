# 2026-03-28 Recurrence Key Contract

## Status

- Document status: next-phase design contract
- Current shipped contract: local-first document assistant web MVP
- This document does not describe implemented repeated-signal promotion

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
  - optional `durable_candidate`
  - optional `candidate_review_record`
- current session payloads may expose pending `review_queue_items`
- current queue is:
  - read-only plus `accept` only
  - reviewed-but-not-applied only
  - not user-level memory
- repeated-signal promotion is still blocked
- current docs already fix that `candidate_family` alone is not a truthful recurrence key

## Contract Goal

Define the first truthful recurrence-key primitive that later repeated-signal promotion may consume without pretending that the repo already has a semantic classifier, reviewed-memory store, or user-level memory system.

## 1. Meaning

- The first truthful recurrence key is the identity of one deterministic rewrite-transformation class within one candidate family.
- For the current shipped family, `correction_rewrite_preference`, it should answer only:
  - did two distinct grounded briefs produce the same normalized rewrite-delta signature from their explicit original-vs-corrected pair?
- It should not claim:
  - a broad semantic preference ontology
  - a model-generated intent summary
  - a user-level reusable memory rule

## 2. Why Family Alone Is Not Enough

- `candidate_family = correction_rewrite_preference` only says the candidate belongs to the rewrite-preference family.
- The current fixed statement, `explicit rewrite correction recorded for this grounded brief`, only says an explicit rewrite happened.
- Neither field identifies which rewrite transformation repeated across grounded briefs.
- Queue presence, explicit confirmation, or reviewed acceptance also do not identify the recurring transformation. They only say something about one candidate instance.

## 3. Minimum Contract

The first contract is one optional source-message-anchored `candidate_recurrence_key`.

### Minimum Envelope

- `candidate_family`
- `key_scope = correction_rewrite_recurrence`
- `key_version = explicit_pair_rewrite_delta_v1`
- `derivation_source = explicit_corrected_pair`
- `source_candidate_id`
- `source_candidate_updated_at`
- `normalized_delta_fingerprint`
- optional `rewrite_dimensions`
- `stability = deterministic_local`
- `derived_at`

### Identity Rule

The identity-bearing part of the key is:

- `candidate_family`
- `key_version`
- `normalized_delta_fingerprint`

`source_candidate_id` and `source_candidate_updated_at` are source-message version references, not cross-source identity.

## 4. Allowed Inputs

The first derivation input must stay recoverable from current shipped state only:

- normalized `original_response_snapshot.draft_text`
- normalized explicit `corrected_text`
- current `candidate_family`

No hidden classifier, no remote service, and no model-written summary should be required to emit the key.

## 5. Optional `rewrite_dimensions`

The first contract may expose only deterministic text-shape fields that can be recovered locally from the explicit pair without semantic inference.

Examples of acceptable dimensions:

- length-direction style metadata
- structure-shift style metadata
- coarse edit-density bands

These dimensions are explanatory only. They do not replace `normalized_delta_fingerprint` as the actual identity field.

## 6. When No Key Should Exist

The key should be omitted when:

- there is no valid explicit original-vs-corrected pair
- normalized original and corrected text collapse to the same content
- the candidate family is unsupported by the current derivation version
- the repo cannot derive a deterministic normalized rewrite-delta fingerprint without falling back to:
  - free-form model summary
  - task-log replay
  - review outcome alone
  - approval-backed save alone

When the key is omitted, repeated-signal promotion must stay blocked.

## 7. Allowed Basis Vs Forbidden Basis

### Basis Candidates

- explicit original-vs-corrected pair
- explicit reviewed-but-not-applied trace only as strengthening evidence after a key exists
- same candidate family only together with the stricter recurrence key

### Supporting Context Only

- `session_local_memory_signal`
- `superseded_reject_signal`
- `historical_save_identity_signal`
- approval-backed save support

### Never Basis

- `candidate_family` alone
- fixed statement text alone
- queue presence alone
- `candidate_review_record` alone
- task-log replay alone
- approval-backed save alone
- historical adjunct alone

## 8. Relationship To Current Durable / Review Layers

- `session_local_candidate`
  - remains the current per-source-message candidate draft
  - remains unchanged
- `durable_candidate`
  - remains the current same-source explicit-confirmation projection
  - remains unchanged
- `candidate_review_record`
  - remains the current reviewed-but-not-applied trace for one durable candidate version
  - may strengthen recurrence evidence later
  - must not replace the recurrence key itself
- `review_queue_items`
  - remain the pending-only surface for current eligible `durable_candidate` items
  - must not act as recurrence evidence by themselves

This ordering matters:

- current queue/review surfaces operate on one current source-message candidate version
- recurrence key is the first cross-source identity primitive needed before same-family merge or repeated-signal promotion can be honest

## 9. Threshold And Distinctness

- The first repeated-signal baseline should remain conservative:
  - at least two distinct grounded briefs must expose the same recurrence key
- Distinctness is anchored by different:
  - `artifact_id`
  - `source_message_id`
- Repeated edits on one source message do not count as multi-brief recurrence.
- Two is the first honest baseline for `correction_rewrite_preference` because one explicit pair proves only one-brief evidence.
- This should not be treated as a permanent universal rule for every future candidate family. Later families may require:
  - higher thresholds
  - review support
  - additional family-specific constraints

## 10. Session Boundary

- The key itself is source-message-anchored and session-agnostic.
- The first future aggregation that consumes the key is now fixed separately as a conservative same-session-only boundary.
- The recurrence-key shape itself still remains session-agnostic, even though the first aggregation that consumes it is same-session only.
- Cross-session aggregation remains later than that first same-session boundary and needs explicit local-store, rollback, conflict, and reviewed-memory rules.

## 11. Why This Comes Before More Review Actions

- `edit` / `reject` / `defer` still operate on one current reviewed candidate version.
- They do not solve the missing cross-source identity problem.
- Without a truthful recurrence key, any same-family merge, broader durable promotion, or category-specific weighting would still overclaim.
- Therefore the recurrence-key primitive should land before:
  - multi-source repeated-signal promotion
  - same-family merge helper reopen
  - broader review-history surface
  - broader review-action vocabulary

## 12. Implemented Slice

The recommended first slice is now implemented as:

- add one optional source-message-anchored read-only `candidate_recurrence_key` draft derived only from the explicit original-vs-corrected pair

Why this remains the smallest honest implemented slice:

- it reuses current shipped source-message fields only
- it does not require multi-source aggregation yet
- it does not reopen review UI or review vocabulary
- it keeps `session_local_candidate`, `durable_candidate`, `candidate_review_record`, and `review_queue_items` unchanged
- it provides the missing primitive that later repeated-signal promotion, same-family merge, and broader durable promotion all depend on

## Open Questions

1. Which deterministic `rewrite_dimensions` are stable enough to expose in `explicit_pair_rewrite_delta_v1` without overclaiming semantic intent?
2. Which exact local store, rollback, and reviewed-memory preconditions should be required before any cross-session recurrence aggregation opens after the first same-session boundary?
