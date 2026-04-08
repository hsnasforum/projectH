# Product Proposal

## Status

- Document status: active proposal aligned to the current repository and the 2026-03-26 staged roadmap
- Current shipped contract: local-first document assistant web MVP
- This document separates:
  - current contract
  - next phase design target
  - long-term north star

## One-Line Definitions

### Current Product

projectH is a **local-first document assistant web MVP** for turning private working documents into grounded summaries and approval-gated notes.

### Long-Term North Star

projectH aims to become a **teachable local personal agent** that stores user corrections and preferences locally and later expands into approval-gated local action.

## Decision Frame

### Facts
- The repository already supports local file reading, summarization, document search, general chat, follow-up Q&A in document context, approval-gated save, evidence panels, feedback capture, and local session/log storage.
- Web investigation is a permission-gated secondary mode (enabled/disabled/ask per session) under the document-first guardrail, with local JSON history, in-session reload, history-card badges, entity-card / latest-update answer-mode distinction, and claim-coverage panel already shipped.
- The current phase is not model training and not program operation.

### Recommendation
- Keep the product identity fixed on the **document assistant** until the document workflow, approval policy, evidence policy, and eval structure are stable.

## Why The Current Product Must Stay A Document Assistant

- The current implementation is strongest when one local document can be read, summarized, questioned, and saved with visible evidence.
- A document workflow has a clearer success condition than broad chat: the user can inspect the source, review the evidence, and decide whether the output is save-worthy.
- The current approval system is already well matched to note saving, while broader action flows would require new safety surfaces.
- Web investigation helps when local context is insufficient, but it remains noisier and less deterministic than single-document grounding.

## Current Contract

### Primary Workflow
1. Open one local file or one browser-picked document.
2. Generate a grounded summary with visible evidence and source spans.
3. Ask follow-up questions in the same document context.
4. Save the resulting note only through explicit approval.
5. Keep evidence, approval events, and feedback local for later review.

### Implemented Product Surface
- local web shell on `127.0.0.1`
- recent sessions and conversation timeline
- file summary / document search / general chat modes
- active document context for follow-up questions
- approval-based save and save-path reissue
- evidence/source panel and summary-range panel
- response-origin badge
- streaming progress and cancel
- response feedback capture
- PDF text-layer support with OCR-not-supported guidance
- permission-gated web investigation (enabled/disabled/ask per session) with local JSON history, in-session reload, and history-card badges (answer-mode, verification-strength, source-role trust)
- entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade
- claim coverage panel with status tags and actionable hints

### Core Product Boundaries
- Core product: local document assistant
- Secondary mode: permission-gated web investigation (enabled/disabled/ask per session) under document-first guardrail
- Safety baseline: approval-based writes and auditable local traces
- Vendor stance: model/runtime interchangeable, product identity vendor-neutral

## Chosen Official Artifact

The first official artifact is the `grounded brief`.

### Why `grounded brief`
- It matches the current code path that already produces a summary-first note body and approval preview.
- It can carry evidence snippets, summary chunks, source paths, and save outcomes without needing a second artifact type.
- It is broad enough to work across proposals, specs, notes, and PDFs, while still being concrete enough for approval and correction review.

### Why Not The Other Options
- `memo` is too style-specific for the current repository's summary-first behavior.
- `action-item note` is too narrow because the current product often needs summary and evidence even when actions are secondary.

## Why The Next Phase Must Be Correction / Approval / Preference Memory

- A teachable product needs a reliable record of what the user accepted, corrected, rejected, and preferred.
- The current MVP already captures useful traces such as approvals, evidence, and feedback, but it does not yet turn them into reusable preference memory.
- This phase is the minimum bridge between a static assistant and a teachable assistant.
- It creates measurable assets for future personalization without pretending that a personalized model already exists.

## Next Phase Design Target

### Goal

Turn the current document assistant into a **learning-ready document assistant** that can remember correction and preference signals locally and use them in later responses.

### Minimum Contract
- one `grounded brief` artifact identity per save-worthy document result
- original response snapshot linked to message, evidence, summary chunks, and source paths
- corrected outcome linked to the same artifact
- approval trail linked to the same artifact
- preference signal candidates extracted from repeated corrections and approvals
- session-local memory separated from durable memory candidates

### Next 3 Implementation Priorities
1. Standardize the `grounded brief` as the single save-worthy document artifact.
2. Design the local schema for correction pairs, approval outcomes, rejection reasons, and preference signals around that artifact.
3. Build an eval loop that checks whether preference memory reduces repeated mistakes on recurring document tasks.

## Why Program Operation Comes Later

- Program operation is a higher-risk extension than document note generation.
- Before actions are added, the system needs proof that it can preserve user intent and working style in a stable, auditable way.
- Any later operator surface must support observation, approval, rollback thinking, and traceability beyond the current save flow.
- The first operator surface remains an `OPEN QUESTION` and should not be prematurely fixed in this round.

## Long-Term North Star

### Product Shape
- a teachable local personal agent
- durable local preference and workflow memory
- approval-gated local tool or program operation
- auditable and reversible risky behavior

### What This Is Not Today
- not current shipped UI contract
- not implemented program control
- not autonomous background behavior
- not an already-learning personalized model

## Data Assets To Accumulate For That Path

### Already Available In The Current MVP
- source document references
- evidence items and summary chunks
- approval request / approval outcome traces
- response feedback labels and reasons
- session history and active context
- web investigation local JSON history and history-card badge traces when secondary mode is used

### Needed Next
- grounded-brief artifact snapshots
- corrected output pairs
- durable preference-rule candidates
- artifact-linked rejection reasons
- eval fixtures for repeated document jobs

## What Not To Build Now

- generic web-chatbot positioning
- web-search-first product packaging
- model training described as current functionality
- broad desktop or program automation
- cloud-first collaboration or account systems
- autonomous background agents

## OPEN QUESTION

1. How should preference signals be scoped so they remain useful without becoming noisy?
2. What evidence is required before a session-level correction becomes durable local preference memory?
3. How should rejected or reissued approvals carry normalized reasons without freezing the taxonomy too early?
4. Which first operator surface would be narrow enough to add later without breaking the approval-first safety model?
