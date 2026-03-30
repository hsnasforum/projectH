# 2026-03-27 save identity corroboration contract

## 사실

- shipped `session_local_memory_signal.save_signal` is still the current-state-only save summary.
- shipped `historical_save_identity_signal` is a separate, source-message-anchored historical adjunct.
- the shipped helper currently replays only same-anchor `write_note` audit with non-empty `approval_id`.
- that choice is already implementation-truthful because `write_note` marks a persisted approval-backed save boundary, while `approval_granted` alone does not prove the note was actually written.
- the helper stays absent while the current `save_signal` still exposes `latest_approval_id`.
- broader save history, pending approval replay, and any cross-artifact aggregate remain out of scope.

## 결정

- `Option A` is the current recommendation.
- Keep the shipped `write_note`-only replay rule as sufficient for the current MVP.
- Do not open `approval_granted` corroboration in the immediate next slice unless a concrete insufficiency appears in focused operator use or regression.

## 이유

- The current helper is meant to replay one historical approval-backed save identity that was actually persisted.
- `write_note` already carries the narrowest truthful proof for that boundary:
  - same anchor
  - actual `approval_id`
  - actual `save_content_source`
  - actual `saved_note_path`
  - actual persisted write time
- Promoting `approval_granted` too early risks replaying granted-but-not-written approval state as though a save identity had already been persisted.
- Keeping the shipped rule avoids confusing:
  - current `save_signal`
  - historical save identity
  - pending approval history

## Current shipped boundary

- `save_signal` remains the current-state-only summary.
- `historical_save_identity_signal` remains the historical adjunct.
- The shipped helper still:
  - replays at most one latest historical approval-backed save identity
  - stays source-message-anchored
  - stays read-only
  - omits itself when the current `save_signal` still has `latest_approval_id`
  - omits itself when current save linkage and replay candidate disagree on save source or saved path
- The shipped helper still must not replay:
  - saved body copy
  - approval preview body copy
  - pending approval state
  - content verdict state
  - approval-friction relabeling
  - cross-artifact aggregate history
  - list/feed style save history

## Future corroboration target

- If corroboration is ever reopened later, it should stay narrower than a second replay source.
- `approval_granted` should be corroboration-only, not standalone replay.
- Minimum future rule:
  - same anchor only
  - same `approval_id` only
  - only for an already-selected `write_note` candidate
  - never enough by itself to emit `historical_save_identity_signal`
- A future corroboration slice should still not replay:
  - saved body text
  - approval preview text
  - pending approval replay
  - broader save-history lists
  - content verdict or approval-friction state

## Acceptance boundary

- Current acceptance remains the shipped `write_note`-only rule.
- If future corroboration is added, it should be additive:
  - it must not overwrite `save_signal`
  - it must not change the helper shape into a save-history viewer
  - it must not require a separate store
- Minimum future regression should verify:
  - `approval_granted` without matching `write_note` still does not emit the helper
  - same-approval corroboration only strengthens an existing `write_note` candidate
  - current `save_signal` and historical adjunct remain separate

## Open question

- What concrete operator ambiguity would justify reopening corroboration at all, given that the current helper already replays persisted save identity truthfully?
- If that ambiguity appears later, is same-approval `approval_granted` corroboration still enough, or would it only confirm what `write_note` already proves?
