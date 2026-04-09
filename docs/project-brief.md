# projectH Project Brief

## One-Line Current Product Definition

projectH is a **local-first document assistant web MVP** that reads private files, produces grounded summaries, saves notes only through explicit approval, and ships the first reviewed-memory slice (review queue, aggregate apply trigger, and active-effect path).

## One-Line Long-Term North Star

Long term, projectH aims to become a **teachable local personal agent** that accumulates user corrections and preferences locally and later expands into approval-gated local program operation.

## Product Layer Split

### Current Contract
- The shipped contract is still a local-first document assistant with the first reviewed-memory slice (review queue, aggregate apply trigger, and active-effect path).
- The web shell supports file summary, document search, general chat, approval-based save, reissue approval, evidence/source panel, structured search result preview panel, summary source-type labels, summary span / applied-range panel, response-origin badges, applied-preferences badge, response feedback capture, grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, artifact-linked reject/reissue reason traces, review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), reviewed-memory active-effect path, streaming progress + cancel, PDF text-layer reading, and permission-gated web investigation (disabled/approval/enabled per session) with local JSON history, in-session reload, history-card badges (answer-mode, verification-strength, source-role trust), entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade, and a claim-coverage panel with status tags, actionable hints, and focus-slot reinvestigation explanation.
- Web investigation remains a **secondary mode** under the document-first guardrail, not the core product identity.
- The current phase is **not** model training and **not** general program control.

### Current Reviewed-Memory Boundary
- The first reviewed-memory slice is shipped: review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility.
- The chosen artifact is the `grounded brief`.

### Next Phase Design Target
- The next phase extends the shipped reviewed-memory boundary into broader **structured correction memory** and **durable preference memory**.
- Cross-session memory and user-level memory remain later.
- This phase is about building **learning-ready local assets**, not claiming that the model already learns by itself.

### Long-Term North Star
- The long-term product is a teachable local personal agent.
- It should preserve durable working style and preference memory locally.
- It may later expand from document work into constrained local tool or program operation.
- Risky actions must remain observable, auditable, approval-gated, and reversible.

### Later Than The Memory Layer
- A personalized local model layer or proprietary model layer only makes sense **after** high-quality correction, approval, preference, and action traces exist.

## Chosen First Official Artifact

The first official artifact is the `grounded brief`.

### Why It Fits The Current Codebase
- The repository already creates summary-first note bodies from one document or one document-search result set.
- Evidence snippets, summary chunks, source paths, and approval previews already gather around the same unit.
- It is easier to standardize than a memo, and less narrow than an action-item note.

### Why It Fits Correction Memory
- One brief can carry the original response, corrected response, approval outcome, and evidence trace without splitting the user job across multiple records.
- Tone, format, evidence sufficiency, and follow-up usefulness can all be reviewed at the brief level.

## Why The Current Phase Must Stay A Document Assistant

- The current repository is strongest at single-document grounding, evidence display, approval-safe saving, and local trace retention.
- Document work has bounded inputs and clearer outputs than broad chat or program control, which makes the product contract easier to evaluate.
- A document-first loop is safer because the main risky write is understandable, previewable, and already approval-gated.
- The current product can already produce a reusable artifact from one document, while broader action loops are not yet implemented.

## Why The Next Phase Must Be Correction / Approval / Preference Storage

- The product needs a reliable way to remember what the user accepted, rejected, and corrected before it tries to act more autonomously.
- Preference memory is the bridge between a useful document assistant and a truly teachable agent.
- Structured correction and approval traces create the first reusable eval assets for future personalization.
- Without this layer, program operation would expand behavior before the system can prove it understands the user's working style.

## Why Program Operation Comes Later

- Program operation has a higher safety bar than document summarization.
- It requires action planning, risk classification, approval UX, rollback expectations, and action-result logging that are stricter than the current save flow.
- The first operator surface is still an `OPEN QUESTION` and should stay at design-goal level for now.

## Current Implementation Facts

### Implemented
- local web shell on `127.0.0.1`
- recent sessions and conversation timeline
- file summary / document search / general chat
- active document context for follow-up questions
- approval-based save and reissue approval
- evidence/source panel with source-role trust labels
- structured search result preview panel
- summary source-type labels (`문서 요약` / `선택 결과 요약`)
- summary span / applied-range panel
- response-origin badges
- applied-preferences badge (`선호 N건 반영`)
- streaming progress + cancel
- response feedback capture
- PDF text-layer support with OCR-not-supported guidance
- permission-gated web investigation (disabled/approval/enabled per session) with local JSON history, in-session reload, and history-card badges (answer-mode, verification-strength, source-role trust)
- entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade
- claim coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved)
- Playwright smoke coverage for core browser flows

### Already Shipped Foundations
- `grounded brief` artifact identity (`artifact_id`, `artifact_kind`, `source_message_id` trace anchors)
- original-response snapshot and corrected-outcome capture (`original_response_snapshot`, `corrected_outcome`, `save_content_source`)
- artifact-linked reject / reissue reason traces (`approval_reason_record`, `content_reason_record`)
- corrected-save linkage on the same source anchor

### Not Implemented
- OCR
- overwrite approval execution
- structured correction-memory schema (beyond current trace foundations)
- durable preference memory
- approval-gated local tool or program operation
- personalized local model training or proprietary model training

## Next 3 Implementation Priorities

1. Fix the `grounded brief` as the single official artifact for document work.
2. Design the storage structure for corrected outputs, approval/rejection outcomes, and reusable preference signals around that artifact.
3. Define an eval loop that measures whether stored corrections and preferences actually improve the next response.

## Data Assets To Accumulate Now

### Already Being Collected
- source document references
- evidence snippets and summary chunks
- saved note approvals and rejection events
- response feedback labels and reasons
- session history and active document context
- web investigation local JSON history and history-card badge traces when the secondary mode is used

### Should Be Added In The Next Phase
- artifact-scoped original response snapshots
- corrected brief outcomes
- approval / rejection reason records tied to the artifact
- extracted preference rules with scope and confidence
- regression-style eval fixtures for repeat document tasks

## Do Not Build Now

- generic web-chatbot positioning
- web-search-first product framing
- program control described as if already shipped
- model learning described as if already implemented
- cloud-first collaboration or account-heavy architecture
- autonomous background agents

## OPEN QUESTION

1. What is the smallest durable preference unit: tone rule, formatting rule, evidence rule, or task-specific rule?
2. When should a correction stay session-local versus being promoted into durable local preference memory?
3. How should rejection reasons be normalized without overfitting to a premature taxonomy?
4. What should be the first tightly bounded operator surface after the memory layer is stable?
