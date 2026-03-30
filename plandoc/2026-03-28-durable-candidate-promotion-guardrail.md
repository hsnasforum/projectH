# 2026-03-28 durable-candidate promotion guardrail

> This note still captures the promotion guardrail decision.
> The follow-up next-slice recommendation is now superseded by [2026-03-28-durable-candidate-projection-contract](./2026-03-28-durable-candidate-projection-contract.md) after `candidate_confirmation_record` shipped.

## 사실

- shipped grounded-brief source messages already expose:
  - source-message-anchored `session_local_memory_signal`
  - optional `superseded_reject_signal`
  - optional `historical_save_identity_signal`
  - optional source-message `session_local_candidate`
- the shipped first candidate family is still only `correction_rewrite_preference`.
- the shipped first statement is still the fixed deterministic sentence `explicit rewrite correction recorded for this grounded brief`.
- approval-backed save is still supporting evidence only.
- repeated same-session drafts remain per-source-message because the current repo still does not have a truthful recurrence key beyond `candidate_family` alone.
- `durable_candidate`, review queue, and user-level memory are still future scope.

## 결정

- choose `Option A`.
- current shipped `correction_rewrite_preference` drafts remain promotion-ineligible.
- future promotion eligibility should begin only after one future primary basis exists:
  - one candidate-linked explicit confirmation signal
  - or one trace-complete repeated-signal basis backed by a truthful recurrence key derived from the explicit corrected pair itself

## 왜 이 선택이 현재 MVP에 맞는가

- local-first:
  - current shipped candidate still points to one explicit source-message pair instead of inferring a broader session or user rule
  - the contract does not invent a cross-message memory object before a truthful basis exists
- approval-safe:
  - approval-backed save stays supporting evidence only and cannot shortcut promotion
  - save acceptance, approval friction, and content correction remain separate axes
- audit-friendly:
  - promotion remains blocked until the future basis is explicit and candidate-linked
  - task-log replay, historical adjuncts, and `candidate_family` alone cannot silently become memory promotion inputs
- confusion reduction:
  - source-message `session_local_candidate` stays one explicit corrected-pair draft
  - future `durable_candidate` stays a later eligibility-reviewed record
  - future reviewed memory stays later still
- why before merge helper:
  - the repo still lacks a truthful same-preference merge key
  - closing the promotion boundary first is safer than aggregating source-message drafts into a broader helper

## Promotion Basis Boundary

### explicit original-vs-corrected pair

- same grounded-brief source message keeps `original_response_snapshot.draft_text`
- same source message keeps explicit user-submitted `corrected_text`
- same source message keeps `corrected_outcome.outcome = corrected`
- normalized original draft and normalized corrected text are not identical

### repeated signal across grounded briefs

- current shipped MVP cannot treat repeated signal as truthful yet
- future repeated signal becomes eligible only when:
  - at least two distinct grounded-brief source messages each emit their own `session_local_candidate`
  - those candidates share the same recurrence key derived from the explicit corrected pair itself
  - supporting artifacts on both sides still preserve snapshot, evidence, and reason trace completeness

### explicit user confirmation

- future explicit confirmation must be one candidate-linked positive reuse-confirmation signal
- it must stay separate from:
  - save approval
  - approval reject / reissue
  - no-save behavior
  - retry
  - feedback `incorrect`
  - reject-note input
- it must say the user wants this rewrite preference reused later, not merely that the current save path was acceptable

### approval-backed save와 historical adjunct의 경계

- approval-backed save stays supporting evidence only:
  - never sole promotion basis
  - never implicit content confirmation
  - never broader-scope justification
- `historical_save_identity_signal` is not promotion basis because it replays save identity, not reusable rewrite preference
- `superseded_reject_signal` is not promotion basis because it replays superseded reject history, not reusable rewrite preference
- replay helper and task-log replay stay supporting context only

## Minimum Future `durable_candidate` Contract

- this is a future contract, not a current shipped field
- minimum shape:
  - `candidate_id`
  - `candidate_scope = durable_candidate`
  - `candidate_family`
  - `statement`
  - `supporting_artifact_ids`
  - `supporting_source_message_ids`
  - `supporting_signal_refs`
  - `evidence_strength`
  - `has_explicit_confirmation`
  - `promotion_basis = explicit_confirmation | repeated_signal_trace_complete`
  - `promotion_eligibility = eligible_for_review`
  - `created_at`
  - `updated_at`

### guardrail rules

- do not emit any `durable_candidate` until one primary promotion basis exists
- do not put suggested scope into this first guardrail contract
- keep scope suggestion deferred until the later review queue layer
- only `promotion_eligibility = eligible_for_review` may feed a future review queue
- promotion still does not mean reviewed memory or user-level memory

## Acceptance And Risk Boundary

### current acceptance 유지

- shipped `session_local_candidate` semantics stay unchanged:
  - same source-message candidate
  - fixed deterministic statement
  - `explicit_single_artifact`
  - approval-backed save support only
- current payloads should still not serialize:
  - `durable_candidate`
  - `promotion_basis`
  - `promotion_eligibility`
  - `has_explicit_confirmation`

### guardrail이 없으면 남는 한계

- operator cannot tell whether a current candidate is only a source-message draft or a reusable future promotion input
- approval-backed save may be over-read as implicit confirmation
- future merge helper, review queue, or user-level memory wording becomes easier to overstate

### guardrail을 너무 일찍 넓히면 생기는 혼동

- `candidate_family` alone merge would over-claim sameness
- approval-backed save would blur content preference with save acceptability
- historical adjuncts would blur replay context with promotion basis
- review queue or suggested scope would appear before any eligible durable candidate exists

### later implementation 전에 필요한 최소 regression

- focused service or web-app regression first
- minimum future checks:
  - explicit confirmation support remains distinguishable from approval-backed save support
  - approval-backed save alone does not create promotion eligibility
  - `superseded_reject_signal` and `historical_save_identity_signal` do not create promotion eligibility
  - repeated same-family candidates do not become eligible by `candidate_family` alone
  - review queue and user-level memory remain absent

### why not merge helper first / review queue first / user-level memory first

- not merge helper first:
  - truthful recurrence key is still missing
  - merge by family alone would be less truthful than current per-source-message drafts
- not review queue first:
  - there are still no eligible `durable_candidate` records to review
  - queue semantics would arrive before eligibility semantics
- not user-level memory first:
  - review, scope, conflict, and rollback rules are still future work
  - current MVP would lose audit clarity if user-level memory arrived before those controls

## Recommended Next Slice

- implement one source-message-anchored `durable_candidate` projection that consumes the shipped `candidate_confirmation_record`
- why:
  - the primary confirmation trace is already shipped, so the next smallest slice is to consume it without mutating `session_local_candidate`
  - it stays local-first and audit-friendly
  - it keeps `session_local_candidate` semantics unchanged while opening the narrowest future eligibility path

## OPEN QUESTION

1. What is the narrowest future explicit confirmation signal shape that stays candidate-linked without being mistaken for save approval?
2. What truthful recurrence key can later prove repeated `correction_rewrite_preference` across grounded briefs without reopening a broader merge helper first?
