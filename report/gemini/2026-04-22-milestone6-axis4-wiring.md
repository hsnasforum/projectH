# 2026-04-22 Milestone 6 Axis 4 - Content Reason Label Wiring

## Context
- Milestone 6 Axis 3 (seq 795) added the UI chips for `ContentReasonLabel` in `MessageBubble.tsx`, but the functional wiring to the backend and storage was deferred to Axis 4.
- A significant number of changes (seqs 779–795) are currently in a dirty state, covering Milestone 6 Axis 1 (reason fields/outcome linkage), Axis 2 (stale reject note surface), and Axis 3 (label chips UI).

## Decision
- Complete the wiring for `ContentReasonLabel` as a focused Axis 4 slice. This ensures the content rejection feature loop is fully closed and functional before finalizing the Milestone 6 base bundle.
- Defer the `commit_push` of the entire Milestone 6 bundle until Axis 4 is verified.

## Recommended Slice (Axis 4)
- **Storage:** Implement `record_content_reason_label_for_message` in `storage/session_store.py` to persist selected labels in `content_reason_record`.
- **Backend:** Add `submit_content_reason_label` in `app/handlers/feedback.py` and register the `POST /api/content-reason-label` route in `app/web.py`.
- **Frontend API:** Add `postContentReasonLabel` in `app/frontend/src/api/client.ts`.
- **Frontend Wiring:** Implement `handleContentReasonLabel` in `App.tsx` and propagate it through `ChatArea.tsx` to the `MessageBubble.tsx` chips.

## Commit Strategy
- Once Axis 4 is verified, commit and push the unified Milestone 6 bundle (seqs 779–797).
- This bundle will stabilize the "Secondary-Mode Investigation Hardening" and "Grounded Brief Contract" enhancements before moving to the next major milestone.
