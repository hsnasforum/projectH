# 2026-03-27 superseded reject replay helper contract

## Current shipped truth

- `session_local_memory_signal` is already shipped.
- It is a read-only, source-message-anchored current-state summary keyed by:
  - `artifact_id`
  - `source_message_id`
- It keeps three axes separate:
  - `content_signal`
  - `approval_signal`
  - `save_signal`
- It is derived from current persisted session state, not from a separate memory store.
- If later explicit correction submit or explicit save supersedes `rejected`, stale `content_reason_record` and optional reject-note may disappear from the source message and therefore from the shipped signal.
- Those superseded traces can still remain in `task_log.jsonl` as audit history.

## Decision

- Choose `Option B`.
- Ship one narrow `superseded_reject_signal` helper before any `durable_candidate` or review-queue work.

## Why Option B Fits The Current MVP

- Current-state-only `session_local_memory_signal` is still the right shipped default because it is small, local-first, and easy to reason about.
- But durable-candidate work should not start from a summary that has already dropped the latest explicit content-side reject / reject-note after later correction or save supersession.
- A narrow replay helper is smaller and safer than:
  - full task-log history replay
  - cross-artifact aggregation
  - early durable-candidate normalization
  - review queue work
- This keeps the current MVP document-first and approval-safe:
  - no new UI is required
  - no task-log canonicalization is required
  - no user-level memory claim is introduced

## Boundary

### Keep current-state signal unchanged

- `session_local_memory_signal` remains:
  - current-state-only
  - read-only
  - source-message-anchored
- It must continue to summarize only what is still recoverable from current persisted session state.

### Replay helper is a separate historical adjunct

- The replay helper should not mutate `session_local_memory_signal.content_signal`.
- It should be a separate optional historical adjunct on the same serialized grounded-brief source message.
- Recommended first name:
  - `superseded_reject_signal`

## What it should replay

- Only the latest superseded content-side reject on the same source-message anchor.
- Optional latest reject-note attached to that superseded reject.

### Minimum shape

```json
{
  "superseded_reject_signal": {
    "artifact_id": "...",
    "source_message_id": "...",
    "replay_source": "task_log_audit",
    "corrected_outcome": {
      "outcome": "rejected",
      "recorded_at": "..."
    },
    "content_reason_record": {
      "reason_scope": "content_reject",
      "reason_label": "explicit_content_rejection",
      "reason_note": "... optional ...",
      "recorded_at": "..."
    }
  }
}
```

### First-slice limits

- at most one latest superseded reject entry
- no list or feed of multiple past rejects
- no replay of saved file bodies
- no replay of approval preview bodies
- no approval-friction relabeling
- no inferred preference statement
- no cross-artifact aggregate
- no top-level session summary

## Source contract

- Canonical source of truth for current state remains current persisted session state.
- The replay helper is an audit-derived adjunct only.
- In the first replay slice, it may read only same-anchor task-log records such as:
  - `content_verdict_recorded`
  - `content_reason_note_recorded`
- It should not promote task-log into the canonical current-state source.
- It should stay source-message-anchored in serialization and should not become a separate store.

## Why approval/save history should stay out

- Approval friction is already separated into `approval_signal`.
- Save history is already partially visible through `save_signal` and saved response messages.
- Pulling approval/save history into the replay helper would blur:
  - current content verdict
  - approval friction
  - save history
- That would turn a narrow adjunct into a mini review/history layer too early.

## Acceptance boundary

- If current `content_signal.latest_corrected_outcome.outcome == rejected`, `superseded_reject_signal` should be absent.
- If current `content_signal` no longer shows `rejected` but same-anchor audit history includes one superseded reject, the helper may expose exactly one replayed reject object.
- The helper must never overwrite the current verdict shown in `content_signal`.
- The helper must remain read-only and serialization-only in the first slice.
- If same-anchor note association is ambiguous, the helper should omit the optional replayed note instead of guessing.

## Separate open question

- `save_signal.latest_approval_id` may still fall out after later explicit actions.
- That save-axis limitation should remain a separate question and should not be bundled into the first superseded reject replay helper.

## Shipped minimal slice

- Source-message serialization may now expose one optional `superseded_reject_signal`.
- It resolves from same-anchor task-log audit only when:
  - current `content_signal` no longer shows `rejected`
  - same-anchor audit contains a prior explicit reject
- It stays additive, read-only, and regression-testable.

## Recommended next implementation slice

- Decide separately whether the remaining save-axis `latest_approval_id` loss needs its own narrow adjunct.
- Do not widen the shipped content-side replay helper into save history replay or mini-history feeds.
