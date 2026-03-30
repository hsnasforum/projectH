# 2026-03-28 review action contract

## 목적

shipped read-only `review_queue_items` 위에 올라갈 first review-action contract를 current MVP 범위에서 가장 작고 truthful하게 고정합니다.

이 문서는 아래를 구분합니다.
- current shipped contract
- next implementation target
- still-later reviewed memory / user-level memory

## Current Shipped Facts

- current source-message anchor already separates:
  - `session_local_candidate`
  - `candidate_confirmation_record`
  - `durable_candidate`
- current session payload already exposes:
  - read-only `review_queue_items`
- current queue surface already means:
  - one pending inspection surface with `accept` only
  - reviewed-but-not-applied only
  - no edit
  - no reject
  - no defer
- canonical source already remains:
  - current persisted session state
- task-log already remains:
  - audit-only
- approval-backed save already remains:
  - supporting evidence only
  - never explicit confirmation
  - never durable promotion shortcut

## First Review-Action Set

Contract vocabulary should define all four actions now:
- `accept`
- `edit`
- `reject`
- `defer`

The first implementation slice is now shipped as:
- implement `accept` only

Why this is the right first slice:
- it closes the smallest missing boundary between:
  - unreviewed `durable_candidate`
  - reviewed-but-not-applied outcome
- it does not require:
  - statement-edit UI
  - dismissal taxonomy
  - deferred bucket UI
  - scope suggestion
  - rollbackable user-level memory
- it stays local-first and approval-safe because:
  - it records one local review trace only
  - it does not auto-apply future memory
  - it does not widen the current queue into a workspace or dashboard

## Meaning Of Each Action

### `accept`

Means:
- the current source-message `durable_candidate` was explicitly reviewed as reusable
- the outcome is now reviewed, not merely eligible

Does not mean:
- user-level memory was already applied
- future scope was already chosen
- source-message `corrected_text` was edited
- `durable_candidate` itself mutated in place

### `edit`

Means:
- a later review can adjust the reusable reviewed statement through one review-time field such as `reviewed_statement`

Does not mean:
- the original-vs-corrected pair was rewritten
- the source-message `corrected_text` changed
- the source-message `durable_candidate.statement` should be mutated

### `reject`

Means:
- the current source-message `durable_candidate` was dismissed as a reviewed candidate

Does not mean:
- content reject
- approval reject
- save omission
- retry
- feedback `incorrect`

### `defer`

Means:
- later revisit is needed for the current source-message `durable_candidate`

Does not mean:
- the explicit corrected pair became invalid
- the explicit confirmation trace was revoked
- the current source-message candidate basis should be deleted

## First Review Trace Contract

The first review-outcome trace should reuse the current source-message anchor:
- name: `candidate_review_record`

Minimum fields:
- `candidate_id`
- `candidate_updated_at`
- `artifact_id`
- `source_message_id`
- `review_scope = source_message_candidate_review`
- `review_action = accept | edit | reject | defer`
- `review_status = accepted | edited | rejected | deferred`
- `recorded_at`
- optional `reviewed_statement` only when `review_action = edit`

Why this trace is anchored on the source message:
- current `durable_candidate` is still source-message-anchored
- current queue items are derived from those source-message records
- reusing the same anchor avoids:
  - second durable store
  - second review store
  - task-log canonicalization

What stays out:
- no top-level review-store object
- no reviewed-memory store
- no user-level-memory store
- no scope suggestion fields in the first trace

## Queue State Transition Rule

`review_queue_items` should remain the pending-only inspection surface.

Queue inclusion rule after review actions exist:
- current source message must still expose current `durable_candidate`
- that `durable_candidate` must still keep `promotion_eligibility = eligible_for_review`
- no matching current `candidate_review_record` may exist on:
  - same `artifact_id`
  - same `source_message_id`
  - same `candidate_id`
  - same `candidate_updated_at`

Queue exit rule:
- after any matching `accept | edit | reject | defer` record is present for the current candidate version, the item leaves the pending queue

Why this is the right first transition:
- current `검토 후보` section stays small
- no second section for accepted / edited / rejected / deferred items is required yet
- actioned items remain discoverable through the source-message anchor and audit log until a later read-only history surface exists

## Basis Boundary

Review action basis may come from:
- current source-message `durable_candidate`
- shipped `candidate_confirmation_record`
- explicit original-vs-corrected pair already consumed by that `durable_candidate`

Supporting context only:
- `session_local_memory_signal`
- `save_signal`
- `superseded_reject_signal`
- `historical_save_identity_signal`

Never basis:
- approval-backed save alone
- `candidate_family` alone
- task-log replay alone

Why approval-backed save stays secondary:
- it may still appear in `supporting_signal_refs`
- it may help explain why the candidate mattered on the same source message
- but it is not explicit confirmation and cannot create reviewability or reviewed outcome by itself

## Reviewed Outcome Vs Future Memory

Keep these layers separate:

- `durable_candidate`
  - unreviewed, source-message-anchored, eligible-only
- `review_queue_items`
  - read-only pending inspection surface
- `candidate_review_record`
  - first local review-outcome trace
- future reviewed memory
  - later reviewed projection or store that may consume `durable_candidate` + `candidate_review_record`
- future user-level memory
  - later applied memory layer after scope, conflict, and rollback rules exist

Key guardrail:
- reviewed candidate != user-level memory

Why user-level memory must stay later:
- current repo still has no rollback rule
- current repo still has no scope-selection contract
- current repo still has no conflict-resolution contract
- auto-apply after review would be too broad and hard to reverse

## Implemented First Slice

- one queue item can now record one source-message `candidate_review_record`
- `review_action = accept`
- `review_status = accepted`
- the matching item leaves pending `review_queue_items`
- `session_local_candidate`, `candidate_confirmation_record`, and `durable_candidate` shapes stay unchanged
- the result remains reviewed-but-not-applied:
  - no edit
  - no reject
  - no defer
  - no reviewed-memory apply
  - no user-level memory
  - no scope suggestion
  - no second queue/dashboard

## Open Questions

1. Once `candidate_review_record` exists, should actioned items remain source-message-only until a later reviewed-history surface, or should one tiny read-only action-history summary appear in the existing shell first?
2. If `durable_candidate` later stops reusing the source-message candidate id, should `candidate_review_record` follow that later durable id or keep the current source-message candidate id lineage?
3. When `edit` opens later, is `reviewed_statement` alone sufficient, or will a separate review-note field become necessary for truthful audit?
