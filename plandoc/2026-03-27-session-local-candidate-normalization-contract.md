# 2026-03-27 session-local candidate normalization contract

## 사실

- shipped grounded-brief source messages already expose:
  - `session_local_memory_signal`
  - optional `superseded_reject_signal`
  - optional `historical_save_identity_signal`
- shipped grounded-brief source messages now also expose one optional computed `session_local_candidate`
- those shipped fields remain source-message-anchored and read-only.
- they are still not normalized candidates:
  - they summarize current or narrowly replayed trace state
  - they do not carry one reusable statement
  - they do not carry support strength
  - they do not distinguish candidate status from later review or promotion state
- review queue, `durable_candidate`, and user-level memory are still future scope.

## 결정

- The first normalization layer is now one shipped `session_local_candidate`, not another replay helper.
- The first candidate family remains `correction_rewrite_preference`.
- This remains narrower and more truthful than starting from approval friction, broad save history, or inferred user-level preference.

## 이유

- Explicit correction already gives the strongest current user-authored trace:
  - original grounded-brief draft snapshot
  - explicit `corrected_text`
  - explicit `corrected_outcome = corrected`
- That pair is more truthful as a first candidate basis than:
  - approval friction, which is still save-surface friction
  - content reject alone, which marks non-acceptance but not yet a reusable rewrite rule
  - save support alone, which remains supporting evidence only
- This choice also keeps:
  - content correction
  - approval friction
  - save support
  as separate axes instead of flattening them into one label.

## 최소 envelope

- `candidate_id`
- `candidate_scope = session_local`
- `candidate_family`
- `statement`
- `supporting_artifact_ids`
- `supporting_source_message_ids`
- `supporting_signal_refs`
- `evidence_strength`
- `status = session_local_candidate`
- `created_at`
- `updated_at`

## Current signal과의 경계

- `session_local_memory_signal` is still:
  - one source-message-scoped current-state summary
  - no reusable statement
  - no candidate-family intent
  - no evidence-strength field
- `superseded_reject_signal` and `historical_save_identity_signal` are still:
  - narrow historical adjuncts
  - helper-only replay context
  - not candidate records
- `session_local_candidate` should therefore sit above those fields instead of replacing them.

## First candidate family

- `candidate_family = correction_rewrite_preference`
- Primary basis:
  - same source message keeps `original_response_snapshot.draft_text`
  - same source message keeps explicit `corrected_text`
  - same source message keeps `corrected_outcome.outcome = corrected`
- The candidate statement should:
  - describe only the reusable rewrite preference
  - avoid copying the full corrected body as the candidate itself
  - avoid re-labeling approval friction or save acceptance as content preference

## First extraction rule

- one eligible source message may emit one `session_local_candidate` draft
- primary extraction source:
  - current source-message `content_signal`
  - same source-message original-vs-corrected pair
- replay helpers may contribute only supporting context:
  - `superseded_reject_signal` should not be the primary extraction source
  - `historical_save_identity_signal` should not be the primary extraction source
- the current shipped candidate keeps this even narrower:
  - `session_local_memory_signal.content_signal` is always the primary basis
  - `session_local_memory_signal.save_signal` may appear only when the same current anchor still exposes `latest_approval_id`
  - the shipped candidate does not yet reference the historical adjuncts at all
- approval-backed save remains supporting evidence only:
  - it may strengthen the candidate when the same anchor later carries save support
  - it must not be the sole basis for extraction
  - it must not act like explicit confirmation
  - it must not justify broader scope by itself

## Evidence strength

- first slice should stay factual:
  - `explicit_edit`
  - `explicit_edit_plus_save_support`
- stronger confirmation levels remain future scope.

## Later boundary

- `session_local_candidate` is still not:
  - `durable_candidate`
  - reviewed memory
  - user-level memory
- promotion still requires:
  - repeated normalized support across grounded briefs
  - or explicit confirmation
  - plus later review / scope / rollback contracts

## Recommended next refinement slice

- Decide whether the shipped deterministic statement should remain fixed or move to one narrower rewrite-summary helper.
- Decide whether repeated same-session `correction_rewrite_preference` drafts should remain per-source-message or gain one small merge helper before any `durable_candidate` work.
- Keep follow-up scope additive:
  - no separate store
  - no review queue
  - no new UI
  - no broad taxonomy

## Open question

- Should the first candidate statement be produced by a tiny deterministic rewrite-summary helper, or by a narrower structured diff that avoids natural-language abstraction?
- When the same session contains multiple correction pairs, should repeated same-family candidates remain separate drafts until later normalization, or should there be one same-session merge helper before any `durable_candidate` work?
