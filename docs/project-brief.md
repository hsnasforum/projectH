# projectH Project Brief

## One-Line Current Product Definition

projectH is a **local-first document assistant web MVP** that reads private files, produces grounded summaries, and saves notes only through explicit approval.

## One-Line Long-Term North Star

Long term, projectH aims to become a **teachable local personal agent** that accumulates user corrections and preferences locally and later expands into approval-gated local program operation.

## Product Layer Split

### Current Contract
- The shipped contract is still a local-first document assistant.
- The web shell supports file summary, document search, general chat, approval-based save, reissue approval, evidence/source panels, summary-range metadata, response-origin badges, streaming cancel, PDF text-layer reading, and permission-gated web investigation (enabled/disabled/ask per session) with local JSON history, in-session reload, and history-card badges.
- Web investigation remains a **secondary mode** under the document-first guardrail, not the core product identity.
- The current phase is **not** model training and **not** general program control.

### Next Phase Design Target
- The next phase is a **correction / approval / preference memory** layer around one official artifact.
- The chosen artifact is the `grounded brief`.
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
- evidence/source panel and summary-range panel
- response-origin badges
- streaming progress and cancel
- response feedback capture
- PDF text-layer support with OCR-not-supported guidance
- permission-gated web investigation (enabled/disabled/ask per session) with local JSON history, in-session reload, and history-card badges (answer-mode, verification-strength, source-role trust)
- entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade
- claim coverage panel with status tags and actionable hints
- Playwright smoke coverage for core browser flows

### Not Implemented
- OCR
- overwrite approval execution
- `grounded brief` artifact identity
- structured correction-memory schema
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
