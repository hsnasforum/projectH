# 2026-03-28 Reviewed-Memory Boundary Defined Contract

## Goal

Fix the exact meaning of `reviewed_memory_boundary_defined` before any same-session aggregate can leave `blocked_pending_reviewed_memory_boundary`.

This document does not describe implemented reviewed-memory store, reviewed-memory apply, repeated-signal promotion, user-level memory, or cross-session counting.

## Current Shipped Truth

- grounded-brief source messages remain the canonical source/content trace
- current source-message surfaces remain separate:
  - `session_local_candidate`
  - `durable_candidate`
  - `candidate_review_record`
  - `candidate_recurrence_key`
- current session payload may expose:
  - pending `review_queue_items`
  - same-session-only read-only `recurrence_aggregate_candidates`
- each current aggregate item may also expose:
  - `aggregate_promotion_marker`
    - `promotion_basis = same_session_exact_recurrence_aggregate`
    - `promotion_eligibility = blocked_pending_reviewed_memory_boundary`
    - `reviewed_memory_boundary = not_open`
  - `reviewed_memory_precondition_status`
    - `status_version = same_session_reviewed_memory_preconditions_v1`
    - `overall_status = blocked_all_required`
    - `all_required = true`
    - ordered fixed `preconditions`
    - `future_transition_target = eligible_for_reviewed_memory_draft`
    - `evaluated_at = last_seen_at`
  - `reviewed_memory_boundary_draft`
    - `boundary_version = fixed_narrow_reviewed_scope_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `aggregate_identity_ref`
    - exact supporting refs
    - `boundary_stage = draft_not_applied`
    - `drafted_at = last_seen_at`

## Decision

- Keep `Option A`.
- The first reviewed-memory boundary should open with one fixed narrow reviewed scope, not a small scope enum.
- The fixed first reviewed scope should be:
  - `same_session_exact_recurrence_aggregate_only`
- `reviewed_memory_boundary_defined` is foundational but still insufficient by itself:
  - it does not satisfy rollback, disable, conflict visibility, or operator-audit
  - it does not unblock the current aggregate by itself

## Why Fixed Narrow Scope Wins

- It is the smallest honest step after the current blocked-only marker/status pair.
- It stays local-first:
  - one current same-session aggregate is already derivable from current persisted session state
  - no second store and no cross-session rule is implied
- It stays approval-safe and audit-friendly:
  - the future boundary can point to one exact aggregate identity and exact current supporting refs
  - a small scope enum would imply broader scope choice, broader conflict handling, and broader audit semantics the repo does not yet implement
- It stays clearly smaller than user-level memory:
  - one fixed narrow reviewed scope is still only a boundary/draft layer above one same-session aggregate
  - it does not imply cross-session preference application

## Exact Meaning Of `reviewed_memory_boundary_defined`

`reviewed_memory_boundary_defined` means all of the following:

- one explicit local reviewed-memory persistence/apply boundary exists above current source-message traces and above the current same-session aggregate surface
- that later boundary is tied to one fixed narrow reviewed scope:
  - `same_session_exact_recurrence_aggregate_only`
- that later boundary makes explicit which aggregate identity and which current supporting refs are inside the future reviewed-memory draft
- that later boundary is still read-only and draft-level, not applied memory

`reviewed_memory_boundary_defined` does not mean any of the following:

- source-message correction history became reviewed memory
- current `candidate_review_record` became reviewed memory
- current `recurrence_aggregate_candidates` became a reviewed-memory store
- current `aggregate_promotion_marker` or `reviewed_memory_precondition_status` became a reviewed-memory record
- user-level memory opened
- `task_log` became the canonical reviewed-memory source

## Fixed Narrow Reviewed Scope

The first reviewed scope should stay fixed at:

- `same_session_exact_recurrence_aggregate_only`

This means:

- one current same-session `recurrence_aggregate_candidates` item is the outer grouping boundary
- the later reviewed-memory draft should point only to:
  - one `aggregate_identity_ref`
  - the current `supporting_source_message_refs`
  - the current `supporting_candidate_refs`
  - optional current `supporting_review_refs`
- the first boundary should not offer:
  - broader same-family scope
  - cross-session scope
  - user-level scope
  - a small reviewed-scope enum

## Boundary From Current Shipped Surfaces

- `candidate_review_record`
  - one source-message reviewed-but-not-applied trace
  - not a reviewed-memory boundary
- `review_queue_items`
  - source-message review queue only
  - not reviewed-memory scope selection
- `candidate_recurrence_key`
  - one source-message recurrence primitive
- `recurrence_aggregate_candidates`
  - one same-session cross-source grouping surface
  - not reviewed memory
- `aggregate_promotion_marker`
  - one current blocked-state marker
  - not a reviewed-memory draft
- `reviewed_memory_precondition_status`
  - one blocked-only read-only status object
  - not a reviewed-memory readiness tracker with partial satisfaction
- future reviewed-memory boundary
  - one later boundary/draft layer above all current surfaces
  - not a rename of any current shipped object

## Relationship To The Other Preconditions

`reviewed_memory_boundary_defined` is the first foundational precondition because the other four preconditions need a fixed object and a fixed scope to govern.

Even after it is defined:

- `rollback_ready_reviewed_memory_effect` is still separate:
  - it governs reversal of a later reviewed-memory effect
  - not the boundary definition itself
- `disable_ready_reviewed_memory_effect` is still separate:
  - it governs future stop-apply behavior
  - not the scope label itself
- `conflict_visible_reviewed_memory_scope` is still separate:
  - it governs how conflicting reviewed aggregates/signals become visible inside that reviewed scope
  - not the mere existence of the scope
- `operator_auditable_reviewed_memory_transition` is still separate:
  - it governs later transition traces above the blocked marker
  - not the boundary label alone

Therefore, defining the boundary does not unblock the current aggregate.

## Current Shipped Boundary-Draft Shape

The current shipped surface now includes:

- `reviewed_memory_boundary_draft`
  - `boundary_version = fixed_narrow_reviewed_scope_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - one `aggregate_identity_ref`
  - `supporting_source_message_refs`
  - `supporting_candidate_refs`
  - optional `supporting_review_refs`
  - `boundary_stage = draft_not_applied`
  - `drafted_at = last_seen_at`

Rules:

- keep `future_transition_target = eligible_for_reviewed_memory_draft`
- do not overwrite current `aggregate_promotion_marker`
- do not overwrite current `reviewed_memory_precondition_status`
- do not create reviewed-memory store/apply in this slice
- do not open per-precondition satisfaction tracking in this slice

## Relationship To Cross-Session Counting

- Cross-session counting remains later.
- Defining the reviewed-memory boundary does not automatically open cross-session counting.
- Cross-session counting still needs extra machinery:
  - explicit local store across session reloads
  - stale-resolution across sessions
  - cross-session conflict visibility
  - operator-visible repair for mistaken cross-session grouping
- The current honest boundary therefore remains:
  - same-session aggregate first
  - fixed narrow reviewed-memory boundary later
  - cross-session counting after that

## Confidence Marker And Threshold

- Current `confidence_marker = same_session_exact_key_match` remains enough for now.
- The fixed reviewed-memory boundary decision does not change that current marker.
- A later second conservative confidence level should still remain later than:
  - boundary definition
  - rollback / disable / conflict / operator-audit mechanics
- Default threshold stays `2` grounded briefs for now.
- Category-specific threshold tuning remains later.

## Recommended Next Implementation Slice

- keep the shipped read-only `reviewed_memory_boundary_draft` draft-only and do not widen it into readiness tracking, apply, or cross-session scope yet

Why this is the smallest next slice:

- the exact fixed narrow boundary is now materialized already
- the repo still cannot truthfully evaluate rollback / disable / conflict / audit satisfaction
- widening the draft before that machinery exists would overclaim reviewed-memory readiness

## Open Questions

1. Should the shipped `reviewed_memory_boundary_draft` keep repeating the fixed `reviewed_scope` label long term, or could a later normalization collapse it into `aggregate_identity_ref` plus supporting refs only?
2. Which extra local-store and stale-resolution rules should be mandatory before cross-session counting opens?
3. Should the current fixed `confidence_marker = same_session_exact_key_match` remain enough until rollback / disable / conflict / operator-audit mechanics exist, or should a later second conservative level be added after that?
