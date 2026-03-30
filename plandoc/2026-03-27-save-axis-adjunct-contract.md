# 2026-03-27 save-axis adjunct contract

## 사실

- shipped `session_local_memory_signal.save_signal` is current-state-only and source-message-anchored.
- shipped `superseded_reject_signal` already covers the content-side gap where a later explicit action clears stale `rejected` / reject-note state from the source message.
- save-axis still has a narrower remaining gap:
  - later explicit correction or other explicit content-side movement can clear `corrected_outcome.approval_id` from the source message
  - the current `save_signal` can still keep `latest_save_content_source` and `latest_saved_note_path`
  - but `latest_approval_id` can fall out even though the earlier approval-backed save really happened
- current canonical source of truth remains the current persisted session state.
- task-log remains audit-only by default and must not become the new canonical current-state store.

## 결정

- `Option B` was implemented.
- Before any durable-candidate or user-level memory work, one save-axis adjunct now covers approval-backed save identity loss without widening `save_signal` itself.
- This stays smaller and more truthful than turning task-log into a broad replay layer.

## 이유

- The current operator limitation is specific and narrow:
  - the current session can still show that a save happened
  - but later explicit actions can drop the approval identity that backed that save
- This is still useful local audit context, especially because save in the current MVP is approval-gated.
- Keeping the helper separate prevents current save state from being confused with historical save identity.
- This also avoids overloading the already shipped content-side `superseded_reject_signal`.

## 최소 contract

- Implemented helper name: `historical_save_identity_signal`
- Placement:
  - optional adjunct under the same serialized grounded-brief source message
  - separate from `session_local_memory_signal.save_signal`
- Scope:
  - one same-anchor historical approval-backed save identity only
  - no list/feed history in the first slice
- Suggested fields:
  - `artifact_id`
  - `source_message_id`
  - `replay_source = task_log_audit`
  - optional `approval_id`
  - optional `save_content_source`
  - optional `saved_note_path`
  - optional `recorded_at`

## 표시 조건

- The adjunct should stay absent when the current `save_signal` still exposes `latest_approval_id`.
- The adjunct may appear only when all of the following are true:
  - the current source-message anchor is known
  - the current `save_signal` no longer exposes `latest_approval_id`
  - same-anchor audit still shows one approval-backed save identity worth replaying
- The adjunct must not overwrite or relabel the current `save_signal`.

## replay source

- The canonical current-state source stays the current persisted session state.
- The adjunct itself is audit-derived only in the shipped first slice.
- The shipped replay source is:
  - same-anchor `write_note` records that still include `approval_id`
- `approval_granted` corroboration is intentionally not required in the first slice because the helper is meant to replay persisted save identity, not granted-but-not-written approval state.
- Do not reuse:
  - approval-friction traces
  - content verdict traces
  - saved body text
  - approval preview text

## 절대 replay하지 말아야 할 것

- saved body copy
- approval preview body copy
- content verdict replay
- approval-friction relabeling
- cross-artifact aggregate
- inferred preference statements
- multi-entry save history list

## acceptance boundary

- `save_signal` remains the current-state-only summary and does not become historical.
- `historical_save_identity_signal` remains helper-only and historical.
- Regression for the first implementation slice should verify at least:
  - the adjunct appears only when `save_signal.latest_approval_id` has fallen out
  - it restores at most one latest historical approval-backed save identity
  - it does not overwrite `save_signal`
  - it does not replay saved body text or approval preview text

## open question

- Whether a later slice should add optional `approval_granted` corroboration beyond the shipped `write_note`-only replay.
- Whether a later slice needs anything broader than one historical approval-backed save identity.
