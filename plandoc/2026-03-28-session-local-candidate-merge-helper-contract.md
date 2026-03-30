# 2026-03-28 session-local candidate merge-helper contract

## 사실

- shipped grounded-brief source messages already expose:
  - source-message-anchored `session_local_memory_signal`
  - optional `superseded_reject_signal`
  - optional `historical_save_identity_signal`
  - optional source-message `session_local_candidate`
- the shipped first candidate family is still only `correction_rewrite_preference`.
- the shipped first candidate statement is still fixed and deterministic.
- approval-backed save remains supporting evidence only and still does not act as the primary basis for the candidate.
- `durable_candidate`, review queue, and user-level memory are still future scope.

## 결정

- Choose `Option A`.
- Repeated same-session `correction_rewrite_preference` drafts should remain per-source-message for now.
- Do not open a same-session merge helper in the current MVP slice.

## 이유

- The shipped candidate envelope is currently too broad to merge truthfully by family alone:
  - `candidate_family` is still one broad family label
  - the statement is still one fixed deterministic sentence
  - the current `supporting_signal_refs` set records basis/support linkage, not a same-preference merge key
- Opening a merge helper now would therefore force one of two bad outcomes:
  - merge every same-family correction draft together, which overstates sameness
  - introduce a rewrite-summary or signature helper first, which this stage still intentionally defers
- Keeping drafts per-source-message is more:
  - local-first, because no broader session aggregate is inferred yet
  - approval-safe, because approval-backed save does not get promoted into a merge basis
  - audit-friendly, because each candidate still points back to one explicit original-vs-corrected pair
- This also keeps the boundary clearer:
  - source-message candidate = one explicit corrected pair
  - future merge helper = still absent
  - future `durable_candidate` = later reviewed/promotion candidate, still separate

## 현재 contract

- repeated same-session drafts stay per-source-message
- no session-level merge helper is emitted now
- no merge by `candidate_family` alone
- no merge by:
  - `superseded_reject_signal`
  - `historical_save_identity_signal`
  - approval-backed save support
  - approval friction
  - content reject history
  - save history

## Reopen 조건

- Reopen only if a truthful merge key exists beyond family alone.
- That future merge key must come from the explicit corrected pair itself, not from:
  - family label alone
  - approval-backed save support
  - historical adjuncts
  - task-log replay alone
- Until that exists, a merge helper would be less truthful than the current per-source-message drafts.

## If Reopened Later

- the narrowest acceptable helper should be one optional top-level session-local read-only adjunct:
  - `session_candidate_family_signal`
- minimum shape:
  - `signal_scope = session_local`
  - `candidate_family = correction_rewrite_preference`
  - `statement`
  - `merged_candidate_ids`
  - `supporting_artifact_ids`
  - `supporting_source_message_ids`
  - `status`
  - timestamps
- minimum rules:
  - same session only
  - same family only
  - at least two distinct source-message candidates
  - merge key derived from the explicit corrected pair itself
  - do not overwrite source-message `session_local_candidate`
  - do not imply `durable_candidate`
  - do not become a list/feed viewer in the first reopen slice

## Recommended Next Slice

- Define the minimum promotion guardrail from shipped source-message `session_local_candidate` to future `durable_candidate`.
- This is a better next slice than a merge helper because:
  - the current candidate contract is now stable enough to reason about promotion boundaries
  - the repo still lacks a truthful same-preference merge key
  - promotion rules can stay document-first and scope-safe without widening the serialized session surface

## Open Question

- If a later merge-helper reopen happens, what is the smallest truthful merge key that can be derived from the explicit corrected pair without introducing a broader rewrite-summary helper or another inferred taxonomy?
