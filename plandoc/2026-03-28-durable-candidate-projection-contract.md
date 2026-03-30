# 2026-03-28 durable-candidate projection contract

## 사실

- shipped grounded-brief source messages already expose:
  - source-message-anchored `session_local_memory_signal`
  - optional `superseded_reject_signal`
  - optional `historical_save_identity_signal`
  - optional `session_local_candidate`
  - optional `candidate_confirmation_record`
- the shipped first candidate family is still only `correction_rewrite_preference`.
- the shipped first statement is still the fixed deterministic sentence `explicit rewrite correction recorded for this grounded brief`.
- approval-backed save is still supporting evidence only.
- repeated same-session drafts still remain per-source-message because the repo still does not have a truthful recurrence key beyond `candidate_family` alone.
- the first source-message-anchored read-only `durable_candidate` projection is now implemented on serialized grounded-brief source messages only.
- review queue, reviewed memory, and user-level memory are still future scope.

## 결정

- the first shipped `durable_candidate` is one optional computed projection on the serialized grounded-brief source message.
- that projection consumes the shipped same-source-message `candidate_confirmation_record`.
- that projection is intentionally narrow:
  - not a new store
  - not a review queue item
  - not reviewed memory
  - not user-level memory

## Minimum Contract

- shipped first `durable_candidate` shape:
  - `candidate_id`
  - `candidate_scope = durable_candidate`
  - `candidate_family`
  - `statement`
  - `supporting_artifact_ids`
  - `supporting_source_message_ids`
  - `supporting_signal_refs`
  - `supporting_confirmation_refs`
  - `evidence_strength`
  - `has_explicit_confirmation`
  - `promotion_basis = explicit_confirmation`
  - `promotion_eligibility = eligible_for_review`
  - `created_at`
  - `updated_at`
- minimum `supporting_confirmation_refs` item:
  - `artifact_id`
  - `source_message_id`
  - `candidate_id`
  - `candidate_updated_at`
  - `confirmation_label`
  - `recorded_at`

## First Explicit-Confirmation Path

- reuse the consumed source-message `session_local_candidate` values for:
  - `candidate_family`
  - `statement`
  - `supporting_artifact_ids`
  - `supporting_source_message_ids`
  - `supporting_signal_refs`
  - `evidence_strength`
- add one `supporting_confirmation_refs` item from the matching `candidate_confirmation_record`.
- current first slice reuses the source-message `session_local_candidate.candidate_id` while the projection stays source-message-anchored.
- set:
  - `has_explicit_confirmation = true`
  - `promotion_basis = explicit_confirmation`
  - `promotion_eligibility = eligible_for_review`
  - `created_at = candidate_confirmation_record.recorded_at`
  - `updated_at = candidate_confirmation_record.recorded_at`

## Promotion Basis Boundary

### explicit original-vs-corrected pair

- provides the current source-message `session_local_candidate` draft basis only
- means:
  - same source message keeps `original_response_snapshot.draft_text`
  - same source message keeps explicit `corrected_text`
  - same source message keeps `corrected_outcome.outcome = corrected`
  - normalized original draft and normalized corrected text are not identical
- does not by itself open promotion eligibility

### candidate_confirmation_record

- provides one candidate-linked positive reuse confirmation
- must stay:
  - on the same source message
  - tied to the same `candidate_id`
  - tied to the same `candidate_updated_at`
  - separate from save approval, approval reject / reissue, no-save, retry, feedback `incorrect`, and reject-note input
- one matching record is enough to materialize one `eligible_for_review` projection draft

### approval-backed save

- stays supporting evidence only
- may remain inside `supporting_signal_refs` through `session_local_memory_signal.save_signal`
- never becomes:
  - the sole promotion basis
  - implicit content confirmation
  - a broader-scope shortcut

### historical adjuncts

- `session_local_memory_signal` stays the current-state working summary and source-message candidate basis
- `historical_save_identity_signal` replays save identity, not reusable rewrite intent
- `superseded_reject_signal` replays superseded reject identity, not reusable rewrite intent
- task-log replay remains audit-only and must not become the canonical projection basis

### repeated signal

- still blocked until the repo has a truthful recurrence key derived from the explicit corrected pair itself
- `candidate_family` alone is not that key

## Projection Surface And Source Contract

- first projection surface:
  - current optional `durable_candidate` on serialized grounded-brief source messages only
- canonical source:
  - current persisted session state on that same source message
  - same-message sibling traces:
    - `session_local_candidate`
    - `candidate_confirmation_record`
- join rule:
  - same `artifact_id`
  - same `source_message_id`
  - same `candidate_id`
  - same `candidate_updated_at`
- later review queue should consume this projection after it exists; it should not be the first surface that invents it.

## Acceptance And Risk Boundary

### current acceptance 유지

- current shipped payloads still keep:
  - `session_local_candidate`
  - `candidate_confirmation_record`
- current shipped payloads still do not serialize:
  - `durable_candidate`
  - `promotion_basis`
  - `promotion_eligibility`
  - `has_explicit_confirmation`

### 지금 projection contract가 없으면 남는 한계

- operator cannot cleanly distinguish:
  - source-message draft only
  - explicit-confirmation-backed future review input
- approval-backed save is easier to over-read as implicit promotion support
- later review queue wording is easier to overstate before any eligible projection exists

### why not merge helper first / review queue first / user-level memory first

- not merge helper first:
  - truthful recurrence key is still missing
  - merge by family alone would over-claim sameness
- not review queue first:
  - there are still no projected `eligible_for_review` records to review
  - queue semantics would arrive before projection semantics
- not user-level memory first:
  - review, scope, conflict, and rollback rules still do not exist
  - current MVP would lose audit clarity if user-level memory arrived before those controls

## Recommended Next Slice

- implement one local read-only review queue surface that consumes current source-message `durable_candidate` records
- keep the slice narrow:
  - reuse current source-message `durable_candidate`
  - no new store
  - no apply / rollback
  - no user-level memory
  - no user-level memory
- likely implementation surface:
  - `app/web.py`
  - `tests/test_smoke.py`
  - `tests/test_web_app.py`

## OPEN QUESTION

1. If `durable_candidate` later leaves the source-message surface, should it keep reusing the current source-message candidate id or mint a new durable-scope id at that boundary?
2. What exact pair-derived recurrence key can later justify the repeated-signal path without reopening family-only merge logic?
