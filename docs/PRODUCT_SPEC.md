# Product Spec

## Status

- Document status: current implementation spec with staged product framing
- Current shipped contract: local-first document assistant web MVP
- Current release-candidate scope: `python3 -m app.web` browser shell
- Internal/operator tooling such as `controller.server`, `pipeline_gui/`, `windows-launchers/`, and `_data/` pipeline helpers remains outside the current release gate
- This document separates:
  - current contract
  - next phase design target
  - long-term north star

## One-Line Definitions

### Current Product

projectH is a **local-first document assistant web MVP** that reads local files, produces grounded responses with visible evidence, and saves notes only through explicit approval.

### Long-Term North Star

Long term, projectH aims to become a **teachable local personal agent** with durable local preference memory and later approval-gated local action.

## Current Contract

### Product Framing
- The current MVP is a local-first document assistant.
- Web investigation is a secondary mode, not the core product identity.
- The current phase is not model training.
- The current phase is not local tool or program operation.
- The current release candidate is scoped to the document-assistant browser shell rather than repo-internal operator tooling.

### Primary Workflow Contract
1. Read one local document by path or browser picker.
2. Produce a grounded summary with visible evidence.
3. Keep the document as active context for follow-up questions.
4. Save the resulting note only through explicit approval.

### Current Implementation Coverage
- implemented:
  - local file ingest by path or browser picker
  - document summary with evidence and summary chunks
  - chunked long-document summary reduction that rewrites per-chunk notes into one final Korean summary instead of only echoing isolated lines
  - source-type-aware short-summary, per-chunk, and reduce prompt split plus source-type-aware `summary_chunks` selection heuristics that keep local file or uploaded-document summaries narrative-friendly and document-oriented while keeping selected local search-result summaries on source-backed synthesis; all three prompts further distinguish multi-result summaries (shared facts, meaningful differences, actions, and conclusion) from single-result summaries (non-comparative wording focused on main facts, actions, and grounded conclusion without cross-result comparison)
  - narrative/fiction summary guidance that prioritizes characters, key events, conflict changes, and ending state over memorable wording, with a strict source-anchored faithfulness rule (no fabricated events, no term substitution, no conclusions beyond what the text shows)
  - active document context for follow-up Q&A
  - approval-gated save of summary notes with default notes directory shown in the save-path placeholder
  - response feedback capture
  - grounded-brief trace anchors on summary responses, save approvals, and relevant trace logs
  - small grounded-brief correction editor seeded with the current draft text
  - explicit correction submit with source-message `corrected_text` persistence
  - minimum `accepted_as_is` / `corrected` / `rejected` corrected-outcome capture on grounded-brief source messages
  - one distinct response-card `내용 거절` content-verdict action with same-card optional reject-note updates on `content_reason_record`
  - one small candidate-linked response-card action such as `이 수정 방향 재사용 확인` that appears only when the current source message exposes `session_local_candidate`
  - one separate source-message `candidate_confirmation_record` for that same positive reuse confirmation, kept outside save approval and outside the candidate object itself
  - one optional source-message-anchored read-only `candidate_recurrence_key` draft derived only from the explicit original-vs-corrected pair when the same current source message still exposes a matching current `session_local_candidate`
  - one optional source-message-anchored read-only `durable_candidate` projection computed only when the same current source message still exposes both a matching `session_local_candidate` and `candidate_confirmation_record`
  - one local `review_queue_items` session projection plus one compact existing-shell `검토 후보` section fed only by current `durable_candidate` items with `promotion_eligibility = eligible_for_review`, plus one `accept`-only reviewed-but-not-applied action that records source-message `candidate_review_record`
  - one optional top-level session read-only `recurrence_aggregate_candidates` projection derived only from current same-session serialized source-message `candidate_recurrence_key` records and emitted only when at least two distinct grounded-brief source-message anchors share the same exact recurrence identity
  - one separate existing-shell aggregate-level `검토 메모 적용 후보` section fed only by current `recurrence_aggregate_candidates`, rendered adjacent to `검토 후보` only when one or more aggregates exist; the `검토 메모 적용 시작` submit boundary is now enabled when `capability_outcome = unblocked_all_required` and the user has entered a non-empty reason note (visible but disabled while blocked or while note is empty); clicking the enabled submit now emits one `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` and persists it under `reviewed_memory_emitted_transition_records`; after emission the same aggregate card shows `검토 메모 적용 실행`, and clicking that apply boundary POSTs to `/api/aggregate-transition-apply` which changes `record_stage` to `applied_pending_result` with `applied_at` added; after the apply boundary the card shows `결과 확정`, and clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint
- each current `recurrence_aggregate_candidates` item may now also expose one read-only `aggregate_promotion_marker`, one read-only `reviewed_memory_precondition_status`, one read-only `reviewed_memory_boundary_draft`, one read-only `reviewed_memory_rollback_contract`, one read-only `reviewed_memory_disable_contract`, one read-only `reviewed_memory_conflict_contract`, one read-only `reviewed_memory_transition_audit_contract`, one read-only `reviewed_memory_unblock_contract`, one read-only `reviewed_memory_capability_status`, and one additive read-only `reviewed_memory_planning_target_ref`, all kept deterministic and narrower than emitted transition/apply semantics
  - minimum `approval_reason_record` capture on grounded-brief reject / reissue approval traces
  - explicit `save_content_source = original_draft | corrected_text` plus `source_message_id` on current save-note approvals and related save/write traces
  - minimum corrected-save bridge action that issues a fresh approval from recorded `corrected_text` with `save_content_source = corrected_text`
- partially supporting:
  - memo/action-item style follow-up answers in document context
  - claim-coverage-based web investigation quality hardening
- not implemented:
  - separate grounded-brief artifact store
  - structured correction-memory schema
  - durable preference memory
  - approval-gated local program operation
  - workflow-level eval harness for teachability
- still intentionally minimal:
  - fixed-label `explicit_content_rejection` remains a truthful reject baseline even when no note is attached
  - the first reject-reason contract stays narrow: `reason_scope = content_reject`, `reason_label = explicit_content_rejection`

### Primary Target User
- assumption:
  - a document-heavy solo professional who repeatedly reviews local files and wants grounded notes without default cloud dependence

### Repeated Job
- read one file
- extract the core point
- inspect evidence
- ask a few follow-up questions
- save a reusable note

### Core Input Document Types
- Markdown files
- text files
- text-layer PDFs
- local folders searched through the document-search flow

### Current Outputs
- summary text (visible final Korean summary body for local file/uploaded document/readable PDF, visible summary body for selected search results in search-plus-summary path, source-anchored faithfulness rule)
- evidence/source panel with source-role trust labels
- summary span/applied-range panel showing which chunks were used
- active context metadata (`active_context` session field for follow-up answers, updated by correction-submit `summary_hint`)
- approval preview with request-time snapshot, requested save path, and overwrite warning when target already exists
- saved summary note path (`saved_note_path`) returned after approval, linked in response detail for user confirmation
- response feedback records with label + optional reason, linked via `response_feedback_recorded` audit event
- structured search result preview panel (ordered label with full-path tooltip, match type badge, content snippet)
- summary source-type label (`문서 요약`, `선택 결과 요약`) in quick meta and transcript meta
- response origin badge (`WEB`, answer-mode badge, verification label, source-role trust badges) for web investigation responses
- claim coverage panel with status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`), actionable hints for weak or unresolved slots, a color-coded fact-strength summary bar, and a dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved) for web investigation responses

### Approval Points
- note save approval (approval object with request-time snapshot, requested save path, overwrite warning when target already exists)
- save-path reissue approval (new approval object issued when save path is changed after initial approval)
- web-search permission gate for permission-gated secondary-mode web investigation (disabled/approval/enabled per session)

### Stored Evidence, Logs, And Feedback
- session JSON with messages, `active_context` (follow-up context updated by correction-submit `summary_hint`), `pending_approvals`, `permissions` (`{web_search, web_search_label}`), timestamps
- response metadata including evidence/source with trust labels, summary chunks with applied-range, response origin (badge/answer-mode/verification/source-role), claim coverage with status tags and fact-strength summary, feedback with label + optional reason, and optional source-message `candidate_confirmation_record` / `candidate_recurrence_key` / `durable_candidate` / `candidate_review_record` / grounded-brief trace fields
- current session payload can also expose one computed top-level `recurrence_aggregate_candidates` list derived from current same-session serialized source-message `candidate_recurrence_key` records
- current session payload can also expose one computed top-level `review_queue_items` list derived from eligible current source-message `durable_candidate` records
- additive JSONL task log for requests, approvals, writes, rejects, reissues, cancels, feedback, corrections, verdicts, candidate events, stream-cancel (`stream_cancel_requested`), permission updates (`web_search_permission_updated`, `permissions_updated`), OCR guidance (`ocr_not_supported`), web-search history reload (`web_search_record_loaded`), web-search retry (`web_search_retried`), active-context follow-up (`answer_with_active_context`), reviewed-memory transitions (`reviewed_memory_transition_emitted`, `reviewed_memory_transition_applied`, `reviewed_memory_transition_result_confirmed`, `reviewed_memory_transition_stopped`, `reviewed_memory_transition_reversed`, `reviewed_memory_conflict_visibility_checked`), and response finalization (`agent_response`); save-note actions (`approval_requested`, `approval_granted`, `approval_rejected`, `approval_reissued`, `write_note`) carry per-action detail with core fields `artifact_id`, `source_message_id`, `save_content_source` plus action-specific keys and optional mode addenda such as `source_path` or `search_query` (see ARCHITECTURE for full detail shapes); feedback/correction/verdict actions (`response_feedback_recorded`, `correction_submitted`, `corrected_outcome_recorded`, `content_verdict_recorded`, `content_reason_note_recorded`) carry per-action detail with `message_id`, `artifact_id`, `artifact_kind` core fields (see ARCHITECTURE for full detail shapes)
- local web-search history JSON with answer-mode/verification/source-role badges when the secondary mode is used

### Why The Current Phase Must Stay Document-First
- The document loop is the most grounded and auditable workflow in the current codebase.
- It already has a visible evidence path and an approval-gated write path.
- It is easier to evaluate and safer to stabilize than broad chat or future action flows.
- It produces a reusable artifact, while current general chat remains intentionally lightweight.

## Product Modes

### 1. File Summary
- summarize a local file chosen by path or browser picker
- for short documents, the current short-summary prompt stays document-oriented and may keep narrative-friendly flow reconstruction when the source is a local file or uploaded document
- for long documents, reduce chunk notes into one final summary while keeping summary chunks visible as evidence anchors
- the current long-summary chunk-note and reduce prompts stay document-oriented and may keep narrative-friendly flow reconstruction when the source is a local file or uploaded document
- attach evidence and summary-range metadata
- optionally request approval-gated save

### 2. Document Search
- search a local folder or browser-picked folder
- search responses include a structured search result preview panel; each card shows the matched file's ordered label (with full path tooltip), a match type badge (`파일명 일치` / `내용 일치`), and a content snippet; both search-only and search-plus-summary responses carry the same `search_results` data; search-only responses hide the redundant text body in both the transcript and the response detail box, letting the preview cards serve as the primary surface; search-only responses also show a `선택 경로 복사` button that copies the selected path list to clipboard with a `선택 경로를 복사했습니다` notice; search-plus-summary responses show the visible summary body alongside preview cards in both the response detail and the transcript
- summarize selected results
- when multiple selected results are short enough to avoid chunking, the current short-summary prompt stays search-result-oriented and prioritizes shared facts, meaningful differences, key actions or decisions, and grounded conclusion over narrative retelling; when only a single result is selected, the short-summary prompt uses non-comparative wording focused on main facts, actions, and grounded conclusion without cross-result comparison
- when multiple selected results are long enough to trigger chunking and reduce, the reduce prompt stays search-result-oriented and prioritizes shared facts, meaningful differences, key actions or decisions, and grounded conclusion over narrative retelling; when only a single result triggers chunking, the reduce prompt uses non-comparative wording focused on main facts, actions, and grounded conclusion without cross-result comparison
- when chunking is triggered, per-chunk chunk-note prompts follow the same result-count split: multi-result chunk notes prioritize source-backed facts and meaningful differences, while single-result chunk notes use non-comparative wording focused on main facts, actions, and grounded takeaway without cross-result comparison
- attach evidence and summary-range metadata
- optionally request approval-gated save

### 3. General Chat
- lightweight conversation and follow-up
- may reuse active context when appropriate

### 4. Web Investigation
- permission-gated read-only external search (disabled/approval/enabled per session)
- stores local JSON history with in-session reload and history-card display (answer-mode, verification-strength, source-role trust badges)
- supports entity-card and latest-update answer-mode distinction with separate verification labels, source-role surfaces, claim coverage panel (status tags, actionable hints, fact-strength summary bar, focus-slot reinvestigation explanation), and entity-card strong-badge downgrade
- remains a **secondary mode** with document-first guardrail rather than the main product identity

## Local Web Shell

### Implemented
- local-only web shell on `127.0.0.1`
- current shipped browser entry is `/app`; `/` redirects to `/app`
- the shipped browser shell currently serves the existing template/static UI (`app/templates/index.html` + `/static/app.js`)
- the React build remains preview-only at `/app-preview`, and `/assets/*` serves the matching preview build assets
- when the web shell runs inside WSL, the server binds to `0.0.0.0` by default and prints a Windows fallback browser URL using the current WSL IPv4 address
- recent session list
- conversation timeline with per-message timestamps
- one compact `검토 후보` section inside the current session shell for eligible current `durable_candidate` items, plus one `accept`-only reviewed-but-not-applied action
- advanced settings for provider/runtime/session/search permission
- browser file picker and browser folder picker
- streaming progress box and cancel interaction

### Outside The Current Release Gate
- `controller.server` pipeline dashboard and its Windows fallback helpers
- `pipeline_gui/` desktop launcher and token-maintenance paths
- `windows-launchers/` wrappers and packaged `.exe` flow
- `_data/` pipeline/token collector runtime helpers

### Open Question
- How much more should the web shell expose for low-confidence web investigation suggestions without shifting product identity away from document work?

## Approval Rules

### Implemented
- write actions are approval-gated
- save requests return an approval object
- approval can be approved, rejected, or reissued with a new path
- overwrite is rejected by default; when the save target already exists, the pending approval carries `overwrite: true` and the UI shows an overwrite warning; the user can explicitly approve the overwrite, which executes the write with `allow_overwrite` and replaces the existing file

### Current Approval Object
- `approval_id`
- `artifact_id` when the approval belongs to a grounded brief
- `source_message_id` when the approval belongs to a grounded brief save trace
- `kind`
- `requested_path`
- `overwrite`
- `preview_markdown`
- `source_paths`
- `created_at`
- `save_content_source = original_draft | corrected_text` for the current shipped save-note flow
- optional `approval_reason_record` on reissued approvals

### Current Approval Request Paths
- `approved_approval_id`
- `rejected_approval_id`
- `reissue_approval_id`

### Not Implemented
- non-note operator approvals
- richer user-entered reject / reissue reason capture beyond the current minimum normalized labels

## Session Schema

### Current Session Fields
- `schema_version`
- `session_id`
- `title`
- `messages`
- `pending_approvals` — list of serialized approval objects (see Approval section for field shape)
- `permissions` — `{web_search, web_search_label}` where `web_search` is `disabled` / `approval` / `enabled` and `web_search_label` is `차단 · 읽기 전용 검색` / `승인 필요 · 읽기 전용 검색` / `허용 · 읽기 전용 검색`
- `active_context` — `{kind, label, source_paths, summary_hint, suggested_prompts, record_path, claim_coverage_progress_summary}`; updated by correction-submit `summary_hint`
- `created_at`
- `updated_at`

### Current Computed Session Payload Fields
- `recurrence_aggregate_candidates`
  - read-only same-session recurrence projection only
  - derived only from current serialized grounded-brief source messages that already expose exact-match `candidate_recurrence_key`
  - emitted only when at least two distinct `artifact_id` + `source_message_id` anchors share the same exact recurrence identity in the current session
  - current items may also expose one read-only `aggregate_promotion_marker`, one read-only `reviewed_memory_precondition_status`, one read-only `reviewed_memory_boundary_draft`, one read-only `reviewed_memory_rollback_contract`, one read-only `reviewed_memory_disable_contract`, one read-only `reviewed_memory_conflict_contract`, one read-only `reviewed_memory_transition_audit_contract`, one read-only `reviewed_memory_unblock_contract`, one read-only `reviewed_memory_capability_status`, and one additive read-only `reviewed_memory_planning_target_ref`
  - the existing shell may render one separate aggregate-level `검토 메모 적용 후보` section from this list only when one or more aggregates exist; blocked items keep the action disabled with no active note input; unblocked items show one mandatory note textarea plus one enabled submit boundary; clicking the enabled submit emits one `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` and persists it under `reviewed_memory_emitted_transition_records`; after emission the same card may show `검토 메모 적용 실행`, and clicking that apply boundary changes `record_stage` to `applied_pending_result` with `applied_at` added; after the apply boundary the card shows `결과 확정`, and clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint
  - not persisted as a separate store field
- `review_queue_items`
  - read-only pending-review session projection only
  - derived from current serialized grounded-brief source messages
  - not persisted as a separate store field

### Current Permission Fields
- `permissions.web_search`
  - `disabled`
  - `approval`
  - `enabled`
- `permissions.web_search_label`
  - `차단 · 읽기 전용 검색`
  - `승인 필요 · 읽기 전용 검색`
  - `허용 · 읽기 전용 검색`

### Current Message Fields
- required:
  - `message_id`
  - `role`
  - `text`
  - `created_at`
- optional:
  - `artifact_id`
  - `artifact_kind`
  - `original_response_snapshot`
  - `response_origin` — `{provider, badge, label, model, kind, answer_mode, source_roles, verification_label}`
  - `evidence` — list of `{label, source_name, source_path, snippet, source_role}`
  - `summary_chunks` — list of `{chunk_id, chunk_index, total_chunks, source_path, source_name, selected_line}`
  - `claim_coverage` — list of slot objects, each containing `slot`, `status`, `status_label`, `value`, `support_count`, `candidate_count`, `source_role`, `rendered_as` (`fact_card` / `uncertain` / `not_rendered`); during reinvestigation, slots also carry `previous_status`, `previous_status_label`, `progress_state` (`improved` / `regressed` / `unchanged`), `progress_label`, and `is_focus_slot`
  - `claim_coverage_progress_summary` — plain-language Korean sentence summarizing the focus-slot reinvestigation outcome (empty string on first investigation)
  - `web_search_history` — list of recent search record summaries (up to 8), each containing `record_id`, `query`, `created_at`, `result_count`, `page_count`, `record_path`, `summary_head`, `answer_mode` (`entity_card` / `latest_update` / `general`), `verification_label`, `source_roles` (list of role strings), `claim_coverage_summary` (`strong` / `weak` / `missing` counts), and `pages_preview` (list of `{title, url, excerpt, text_preview, char_count}`)
  - `feedback`
  - `corrected_text`
  - `corrected_outcome`
  - `content_reason_record`
  - `session_local_memory_signal`
  - `superseded_reject_signal`
  - `historical_save_identity_signal`
  - `session_local_candidate`
  - `candidate_confirmation_record`
  - `candidate_recurrence_key`
  - `durable_candidate`
  - `candidate_review_record`
  - `selected_source_paths`
  - `saved_note_path`
  - `save_content_source`
  - `note_preview`
  - `approval_reason_record`
  - `source_message_id`
  - approval metadata

## Response Panels And UI Metadata

### Implemented
- evidence/source panel with source-role trust labels on each evidence item
- summary source-type label (`문서 요약` for local document summary, `선택 결과 요약` for selected search results) in both quick-meta bar and transcript message meta; single-source responses show basename-based `출처 <filename>` in both surfaces, multi-source responses show count-based `출처 N개` instead of raw filenames; general chat responses carry no source-type label
- summary span / applied-range panel
- response origin badge with separate answer-mode badge for web investigation (`설명 카드` / `최신 확인`), source-role trust labels, and verification strength tags in origin detail
- copy-to-clipboard buttons: `본문 복사`, `저장 경로 복사`, `승인 경로 복사`, `검색 기록 경로 복사`, `경로 복사` (selected source paths panel); all share one helper that shows clipboard-specific failure notice on both success-path rejection and fallback failure
- claim verification / coverage panel where applicable, with status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`) leading each slot line, actionable hints for weak or unresolved slots, source role with trust level labels, a color-coded fact-strength summary bar above the response text, and entity-card verification badge downgrade from strong when no claim slot has cross-verified status
- web search history panel with source previews, answer-mode badges, color-coded verification-strength badges, and color-coded source-role trust badges in history cards
- progress box and cancel button during streaming
- verified-vs-uncertain explanation: response-body section headers annotated with matching status tags (`확인된 사실 [교차 확인]`, `단일 출처 정보 [단일 출처]`, `확인되지 않은 항목 [미확인]`), claim-coverage panel hint maps tags to explanations
- slot-level reinvestigation UX: claim-coverage panel shows a dedicated plain-language explanation line for each `is_focus_slot` slot, telling the user whether the slot was reinforced, regressed, is still single-source, or is still unresolved after reinvestigation; non-focus slots keep the lighter status/hint rendering

## PDF Handling

### Implemented
- text-layer PDFs are read and produce a visible summary body with `문서 요약` label and PDF filename in context box/quick meta/transcript meta
- scanned/image-only PDFs return visible OCR-not-supported guidance with exact strings `요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`
- uploaded folder search returns a count-only partial-failure notice when some files cannot be read, while retaining readable-file result preview with ordered label, full-path tooltip, match badge, and snippet; search-only path preserves selected path/copy, hidden response body, transcript preview, and transcript body hidden; search-plus-summary path preserves visible summary body alongside preview cards in both response detail and transcript (separate from OCR-not-supported guidance)

### Not Implemented
- OCR

## Web Investigation Rules

### Implemented
- read-only external search with permission-gated execution (disabled/approval/enabled per session)
- local JSON record storage with in-session history reload and history-card display (answer-mode, verification-strength, source-role trust badges in header)
- response origin with `WEB` badge, answer-mode badge, color-coded verification-strength badge, and color-coded source-role trust badges in origin detail
- entity-card / latest-update answer-mode distinction with separate verification labels and source-role surfaces; entity-card verification badge downgraded from strong (`설명형 다중 출처 합의`) when no claim slot has cross-verified status
- claim coverage panel with status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`), actionable hints for weak or unresolved slots, color-coded fact-strength summary bar, and dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved)
- entity-card agreement-over-noise baseline: multi-source consensus items preferred before single-source claims, noisy single-source items capped
- weak-slot reinvestigation baseline: weak/missing slots targeted first in reinvestigation suggestions, weak slots rendered as uncertain rather than stable facts, progress and focus-slot state recorded
- verified-vs-uncertain explanation: response-body sections annotated with status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`) matching claim-coverage panel statuses

### In Progress
- (Current shipped baseline covers agreement-over-noise and weak-slot reinvestigation; see `docs/TASK_BACKLOG.md` Current Phase In Progress for future quality-improvement direction.)

### Open Question
- How much automatic reinvestigation should happen before the system stops and reports uncertainty?

## Next Phase Design Target

### Phase Definition

The next phase is a **correction / approval / preference memory** layer for the document assistant. It is a design target, not a shipped contract.

### Chosen Official Artifact

The first official artifact is the `grounded brief`.

### Why `grounded brief` Fits Best
- The current code already produces a summary-first draft note body from one file or one selected search result set.
- Approval preview, evidence, summary chunks, source paths, and feedback are already closest to a brief-style unit.
- It is easier to reuse across document-heavy work than a memo and less narrow than an action-item note.

### First Implementation Slice

#### One-Line Definition
- The first implementation slice is now implemented as `artifact_id generation plus message/session/task-log linkage` for each grounded brief.
- The next additive slices are now also implemented on that same anchor: normalized original-response snapshot, minimum `accepted_as_is` / `corrected` content-outcome capture, explicit corrected-text submit on the grounded-brief response surface, and minimum approval-linked reject / reissue reason capture.

#### Why This Is The Smallest Valuable Start
- The current assistant message already persists most of the original-response snapshot:
  - response text
  - source paths
  - response origin
  - summary chunks
  - evidence
  - note preview and saved path when present
- The current task log already persisted approval and feedback events, and the first slice now links grounded-brief save and feedback traces through one stable artifact anchor.
- This means the first missing primitive is not a new review surface or a new memory store, but a stable artifact-level linkage key.
- Before this slice landed:
  - approval trail cannot be linked cleanly to the same brief
  - corrected outcome storage would not have a stable source artifact to point to
  - eval-ready eligibility cannot be assessed across message, approval, write, and feedback traces

#### Goal
- Keep one additive trace anchor in place so the current raw trace bundle can behave like the first grounded-brief artifact seed.

#### Non-Goals
- no separate artifact store in the first slice
- no corrected-save auto-rebase or unsaved-editor save path in the first slice
- no content-level `rejected` outcome capture in that initial artifact slice
- no review queue
- no future user-level memory
- no UI expansion requirement

#### Minimum Additive Fields
- assistant message:
  - `artifact_id`
  - `artifact_kind = grounded_brief`
- approval record / approval payload when present:
  - `artifact_id`
- task-log detail when applicable:
  - `artifact_id`

#### Existing Trace Reuse Points
- assistant message remains the first raw snapshot surface
- current `message_id` remains the closest existing response pointer
- approval objects and pending approvals remain the current approval surface
- append-only task-log events remain the current audit surface
- response feedback remains attached to the assistant message, and `response_feedback_recorded` now logs the resolved `artifact_id` directly for audit reuse

#### Slice-Completion Outcomes
- one grounded brief can be followed across:
  - assistant message
  - approval request
  - approval outcome
  - write note event
  - feedback-linked trace when present
- later richer corrected / rejected outcome capture, corrected-save reconciliation, reason linkage, and eval-ready work can target one stable artifact anchor instead of inferring linkage heuristically

#### Still Not Possible After This Slice
- a fully eval-ready artifact
- corrected output pairs
- reviewed vs unreviewed candidate tracking
- rollbackable reviewed memory
- cross-session user-level memory application

### Current Trace Foundation After Four Small Slices
- implemented now:
  - `artifact_id` and `artifact_kind = grounded_brief`
  - normalized `original_response_snapshot` on original grounded-brief assistant messages
  - explicit `corrected_text` submit on the grounded-brief response surface
  - minimum `corrected_outcome` capture for `accepted_as_is | corrected | rejected`
  - one source-message `content_reason_record` for explicit `내용 거절` plus optional same-card reject-note updates
  - minimum `approval_reason_record` capture for `approval_reject` and `approval_reissue`
  - minimum corrected-save bridge action that creates a fresh approval from recorded `corrected_text`
- the normalized snapshot currently keeps:
  - `artifact_id`
  - `artifact_kind`
  - `draft_text`
  - `source_paths`
  - `response_origin` — same shape as message-level `response_origin` (`{provider, badge, label, model, kind, answer_mode, source_roles, verification_label}`)
  - `summary_chunks_snapshot` — same shape as message-level `summary_chunks`
  - `evidence_snapshot` — same shape as message-level `evidence`
- the assistant message remains the raw source-of-truth surface
- the normalized snapshot lives on the same assistant message and is reused by response/session serialization
- the minimum corrected outcome also lives on that same original grounded-brief assistant message:
  - `outcome = accepted_as_is | corrected`
  - `recorded_at`
  - `artifact_id`
  - `source_message_id`
  - optional `approval_id`
  - optional `saved_note_path`
- explicit correction submit on the grounded-brief response now also persists:
  - `corrected_text`
  - `corrected_outcome.outcome = corrected`
- direct approved save responses can expose the same `corrected_outcome` only because that response is itself the original grounded-brief source message
- approval-execute system responses keep anchor linkage and saved-path status, but do not become the corrected-outcome source-of-truth surface
- correction-submit responses and session serialization expose the updated `corrected_text` on that same original grounded-brief source message
- correction submit also updates the current session `active_context.summary_hint` to the corrected text (truncated to 240 chars), so subsequent same-session follow-up responses and re-summaries use the corrected version as their basis rather than the original draft
- unchanged correction submit is rejected as validation; it must not be auto-upgraded into `accepted_as_is`
- save approval remains a separate flow
- current pending approval previews stay based on the save target snapshot captured when that approval was requested
- correction submit never mutates an already-issued pending approval
- current reconciliation policy is `Option B`:
  - current original-draft save approval remains valid as-is
  - corrected text becomes a save target only through a separate explicit corrected-save bridge action
  - automatic rebasing of an existing pending approval stays forbidden
- current shipped save-note approvals now expose the same explicit save-target contract across both paths:
  - `save_content_source = original_draft | corrected_text`
  - the same `source_message_id` anchor reused by approval/write traces
- approval and task-log traces continue to follow the artifact anchor only; they do not duplicate the full snapshot
- reject / reissue approval traces now persist one normalized `approval_reason_record` on approval-linked surfaces:
  - `reason_scope`
  - `reason_label`
  - optional `reason_note`
  - `recorded_at`
  - `artifact_id`
  - `artifact_kind`
  - `source_message_id`
  - `approval_id`
- current truthful labels stay intentionally narrow until a real reason-input surface exists:
  - `approval_reject -> explicit_rejection`
  - `approval_reissue -> path_change`
- the original grounded-brief assistant message remains the content source of truth; approval reason records live on approval/system responses, reissued pending approvals, and task-log entries instead
- no separate artifact store or corrected-text store was introduced in this round, and the later read-only review queue still stays outside the canonical source-message durable record

### Minimum Correction / Approval / Preference Memory Contract

#### 1. Artifact Identity
- implemented base anchor:
  - `artifact_id`
  - `artifact_kind = grounded_brief`
- still not implemented as a separate record:
  - `session_id`
  - `created_at`
- one save-worthy document result maps to one artifact identity
- multiple approval events may point to the same artifact

#### 2. Original Response Snapshot
- implemented minimum contract on original grounded-brief assistant messages:
  - nested `original_response_snapshot`
  - `artifact_id`
  - `artifact_kind`
  - `draft_text`
  - `source_paths`
  - `response_origin` — same shape as message-level `response_origin`
  - `summary_chunks_snapshot` — same shape as message-level `summary_chunks`
  - `evidence_snapshot` — same shape as message-level `evidence`
- current source of truth:
  - the assistant message still holds the raw response text, evidence, summary chunks, and source-path fields
  - the normalized snapshot is a companion object persisted on that same message and exposed again in response/session serialization
- backward-compatibility rule:
  - legacy grounded-brief messages with artifact linkage plus evidence or summary chunks can be normalized into the same snapshot contract on session load
- still not implemented in that initial artifact slice:
  - a separate artifact record with `assistant_message_id`
  - review records or rollback records
- approval and task-log traces should keep anchor linkage only instead of copying the full snapshot into every downstream event

#### 3. Corrected Outcome
- implemented minimum contract now:
  - `outcome = accepted_as_is | corrected | rejected`
  - `recorded_at`
  - `artifact_id`
  - `source_message_id`
  - optional `approval_id`
  - optional `saved_note_path`
- explicit correction submit also persists:
  - `corrected_text`
- explicit content verdict also persists:
  - `content_reason_record`
- current source of truth:
  - the original grounded-brief assistant message that already owns the artifact anchor and normalized original-response snapshot
  - direct approved save responses may mirror the same object because they are that same source message
  - correction-submit responses and session payloads expose `corrected_text` and `corrected_outcome` from that same source message
  - explicit reject responses and session payloads expose `corrected_outcome = rejected` plus `content_reason_record` from that same source message
  - approval payloads and task-log entries keep linkage only and do not copy the full corrected-outcome blob
- truthful current coverage:
  - `accepted_as_is` is recorded only when save completion is explicit and successful
  - `corrected` is recorded only when the user explicitly submits edited replacement text for the grounded brief
  - `rejected` is recorded only when the user explicitly triggers `내용 거절` on that grounded-brief response surface
  - optional reject-note updates are recorded only through the same response-card content-verdict box while the latest outcome remains `rejected`
  - blank reject-note submit remains invalid and must not be reinterpreted as manual clear
  - unchanged correction submits fail validation instead of creating a synthetic outcome
  - approval reject is not the same as content rejection
- still later:
  - a possible manual reject-note clear refinement, but only if it remains note-only and separate from verdict revocation
  - richer reject taxonomy beyond the first fixed label
- truthful current contract:
  - the correction editor is one multiline control on the grounded-brief response and is seeded with the current draft text
  - that same editor supports partial edits, full rewrite, or pasted replacement text without requiring multiple correction modes
  - correction submit remains separate from save approval and does not auto-run a save
- reconciliation contract now shipped in the first bridge slice:
  - choose `Option B`
  - keep original-draft save approval unchanged unless the user explicitly asks to save the corrected text
  - the response card content-edit area now always exposes a separate action such as `이 수정본으로 저장 요청`
  - when no recorded `corrected_text` exists, that bridge action stays disabled and the correction-area helper copy explains that the user must record a correction first
  - if the editor is changed again after a correction was recorded, the UI must explain that the bridge action still uses the last recorded correction until `수정본 기록` is submitted again
  - that bridge action consumes the latest recorded `corrected_text` on the source message; unsaved editor text is not bridged implicitly
  - that bridge action creates a fresh approval snapshot from `corrected_text`; it must not silently rewrite an already-issued approval preview
  - the first corrected-save slice uses `approval_id` plus the frozen approval body as the immutable snapshot identity
- truthful current reject contract:
  - `rejected` is recorded only when the user explicitly triggers the distinct content-verdict action `내용 거절` on the grounded-brief response card
  - that action remains separate from `수정본 기록`, corrected-save bridge, and approval-surface approve / reject / reissue controls
  - that action records content verdict immediately on the source-message path; it does not create or cancel a save approval
  - approval reject, save omission, retry, or feedback `incorrect` must not be mapped into `rejected`
  - the current source-of-truth contract stays on the original grounded-brief assistant message by widening the existing content-outcome envelope:
    - `corrected_outcome.outcome = accepted_as_is | corrected | rejected`
    - `recorded_at`
    - `artifact_id`
    - `source_message_id`
    - `approval_id` and `saved_note_path` remain optional and are normally absent on the reject-only path
  - the current first reject-reason contract stays intentionally narrow:
    - `reason_scope = content_reject`
    - `reason_label = explicit_content_rejection`
    - optional `reason_note` can stay absent, or be recorded only through the same response-card note surface
  - the current source message also stores one `content_reason_record` alongside the reject outcome:
    - `reason_scope = content_reject`
    - `reason_label = explicit_content_rejection`
    - `recorded_at`
    - `artifact_id`
    - `artifact_kind = grounded_brief`
    - `source_message_id`
    - optional `reason_note`
  - fixed-label baseline and shipped optional-note rule:
    - clicking `내용 거절` alone remains sufficient to record a truthful `rejected` verdict
    - optional reject-note submit must not block or delay that baseline record
    - the absence of `reason_note` does not make the reject verdict incomplete or provisional
  - the current smallest truthful reject-note UX is:
    - one short inline textarea plus one explicit secondary note-submit action
    - shown only inside the same response-card content-verdict box
    - available only when the latest outcome on that same source message is still `rejected`, including reload of an already-rejected message
    - separate from the correction editor, corrected-save bridge, and approval controls
    - blank note submit stays disabled in the shipped slice and must not double as a clear affordance
  - when a reject note is recorded:
    - update the existing `content_reason_record` on that same source message in place
    - fill or replace `content_reason_record.reason_note`
    - refresh `content_reason_record.recorded_at` to the latest reason-record update time
    - keep `corrected_outcome.recorded_at` as the timestamp for when the reject verdict itself was recorded
    - append a separate content-linked task-log event, currently `content_reason_note_recorded`, rather than replaying approval-reject or initial verdict semantics
  - deferred manual clear contract:
    - current MVP recommendation remains `Option B`: keep the shipped disabled-blank-submit behavior and do not pull manual clear into the next refinement slice yet
    - if a later manual clear is introduced, it should stay in the same response-card content-verdict box as one tiny secondary action visible only when a non-empty reject note already exists
    - that future clear must remove only `content_reason_record.reason_note`; it must not revoke `corrected_outcome.outcome = rejected` or the fixed-label `explicit_content_rejection` baseline
    - the same `content_reason_record` should remain on the source message with `reason_scope`, `reason_label`, and trace anchors intact while only the optional `reason_note` field is removed
    - that future clear should refresh `content_reason_record.recorded_at` to the clear time while keeping `corrected_outcome.recorded_at` as the original reject-verdict timestamp
    - that future clear should append its own content-linked task-log event, for example `content_reason_note_cleared`, instead of overloading `content_reason_note_recorded`
  - later explicit correction submit, explicit original-draft save, or corrected-save approval may overwrite the latest `corrected_outcome` on that same source message; when that happens, stale `content_reason_record` including any `reason_note` should clear from the source message while the audit log preserves prior reject and note traces separately
  - if an explicit original-draft save already completed, a later `내용 거절` still updates only the latest content verdict on the source message; the earlier saved note body and saved path remain as historical explicit-save output and must not be rewritten or deleted automatically
  - if a corrected-save already completed, later `내용 거절` or a later explicit correction submit still move only the latest source-message verdict / corrected text; the earlier saved corrected snapshot body and path remain historical explicit-save output until a new explicit save runs
- minimum MVP recommendation:
  - keep the shipped `corrected` and `rejected` surfaces small and audit-friendly
  - reconcile corrected-save only through one explicit save-request action, not through automatic preview rebasing
  - keep the shipped optional reject-note surface narrow: same response-card box, non-empty submit only, and keep manual clear deferred until a repeated operator need justifies a second micro-action
  - keep richer reject taxonomy beyond the first fixed label for later slices
  - keep corrected/rejected content outcomes on the original grounded-brief source message rather than moving them onto approval-linked traces

#### 4. Approval Trail
- each artifact may have an approval trail with:
  - `approval_id`
  - `outcome = approved | rejected | reissued`
  - `requested_path`
  - `overwrite`
  - `created_at`
- current first corrected-save bridge slice reuses the same artifact anchor rather than inventing a second artifact:
  - same `artifact_id`
  - same `source_message_id`
  - a separate approval request / approval outcome path when the user explicitly asks to save the corrected text
  - a separate approval snapshot built from the recorded corrected text visible at request time
  - the same `save_content_source` field expanded from `original_draft` to `corrected_text`
- immutable corrected-save approval rule:
  - the corrected-save bridge action now creates one fresh approval object whose `preview_markdown` and internal `note_text` are both captured from the recorded corrected-text snapshot visible at request time
  - after that approval is issued, later correction submits must not rewrite that approval snapshot
  - if the corrected text changes again, the user must trigger a new corrected-save bridge action to create a new approval
  - approval-card helper copy and corrected-save save-result wording should explicitly label that body as the request-time snapshot so the user understands that the latest source-message `corrected_text` may later differ
  - the first corrected-save slice should treat `approval_id` itself as the immutable snapshot identity; it should not add a separate `snapshot_id` unless approval records stop carrying the saved-body snapshot
- corrected-save approval execution keeps the original grounded-brief source message as the content source of truth:
  - `corrected_outcome.outcome` stays `corrected`
  - the same source message may later add optional `approval_id` and `saved_note_path`
  - the saved approval snapshot is still read from the frozen approval body, not from the current `corrected_text` field
- reissue should preserve the same artifact identity while linking old and new approval objects
- current implemented approval-linked reason trace:
  - nested `approval_reason_record`
  - canonical session source: the assistant system message created for reject / reissue
  - approval convenience copy: the active reissued approval object when reissue creates a new pending approval
  - audit mirror: `approval_rejected`, `approval_reissued`, and `agent_response` task-log detail — `agent_response` detail includes `{status, actions, requires_approval, proposed_note_path, saved_note_path, selected_source_paths, has_note_preview, approval_id, artifact_id, artifact_kind, source_message_id, save_content_source, approval_reason_record, active_context_label, evidence_count, summary_chunk_count}`
- current implemented content-verdict audit trace:
  - explicit reject action log: `content_verdict_recorded`
  - generic content-outcome mirror: `corrected_outcome_recorded`
  - both traces point back to the same `artifact_id` / `source_message_id` anchor on the original grounded-brief source message

#### 5. Shared Reason Fields And Distinct Label Sets
- minimum design target:
  - `reason_scope = correction | content_reject | approval_reject | approval_reissue`
  - `reason_label`
  - `reason_note`
- correction reasons should stay closest to the current feedback reasons:
  - `factual_error`
  - `irrelevant_result`
  - `context_miss`
  - `awkward_tone`
  - `format_preference`
- approval reject reasons should remain separate from correction reasons:
  - current implemented minimum: `explicit_rejection`
  - richer labels such as `content_needs_fix`, `save_not_needed`, and `path_not_acceptable` remain future until the UI can truthfully collect that intent
- approval reissue reasons should remain separate from reject reasons:
  - current implemented minimum: `path_change`
  - richer labels such as `filename_preference` and `directory_preference` remain future until the UI can truthfully distinguish them
- content-level `rejected` reasons now start from one explicit label tied to the content-verdict action itself:
  - `content_reject -> explicit_content_rejection`
  - optional `reason_note` is recorded only through the same response-card reject-note surface and may stay absent
- content-level `rejected` reasons must not reuse approval-reject labels because approval friction and content verdict are separate axes
- current implementation already stores response feedback as label + optional reason; the next phase should wrap that into shared reason fields instead of replacing it
- a shared envelope with distinct label sets is preferable to a fully unified taxonomy because eval can compare counts within scope without mixing content repair with save-path changes

#### 6. First Session-Local Memory Signal
- the first `session_local` memory signal should mean one **read-only working summary** of explicit user actions around one grounded-brief artifact inside the current session
- it does **not** mean:
  - the model learned a reusable preference
  - a durable candidate already exists
  - a user-level memory profile exists
  - a training or personalization artifact is ready
- the canonical unit should stay source-message-anchored:
  - one `artifact_id`
  - one `source_message_id`
  - one original grounded-brief source message as the content anchor
- the first signal should summarize only the current explicit traces that remain truthfully recoverable from persisted session state:
  - latest `corrected_outcome`
  - whether current `corrected_text` exists on that source message
  - current `content_reason_record` when the latest outcome is still `rejected`
  - latest approval-linked `approval_reason_record` tied to the same `artifact_id` / `source_message_id` when present
  - latest save linkage when present:
    - `approval_id`
    - `saved_note_path`
    - `save_content_source = original_draft | corrected_text`
- the first signal should keep its axes separate instead of collapsing them into one preference statement:
  - `content_signal`
  - `approval_signal`
  - `save_signal`
- the first signal should stay thin and linkage-oriented:
  - it should point back to the canonical `corrected_text` on the source message rather than copying large edited bodies
  - it should point back to save linkage rather than copying saved file bodies
  - it should point back to approval-linked reason trace rather than rewriting approval history as content judgment
- the first signal should **not** include:
  - inferred preference category or reusable statement
  - cross-artifact or cross-session aggregation
  - automatic promotion to `durable_candidate`
  - user-level scope or profile application
  - full history replay reconstructed only from task log
- current truthful limitation:
  - if later explicit correction submit or explicit save supersedes `rejected`, the source message clears stale `content_reason_record`
  - in that first slice, a superseded reject or reject-note may remain audit-only in task-log rather than being replayed back into the signal summary
- current implementation:
  - serialized grounded-brief source messages now expose one computed optional `session_local_memory_signal`
  - the projection stays source-message-anchored and read-only:
    - `signal_scope = session_local`
    - `artifact_id`
    - `source_message_id`
  - `content_signal` currently includes:
    - `latest_corrected_outcome`
    - `has_corrected_text`
    - optional current `content_reason_record`
  - `approval_signal` currently includes:
    - optional `latest_approval_reason_record` resolved from matching approval-linked session messages and pending approvals in the same session
  - `save_signal` currently includes:
    - optional `latest_save_content_source`
    - optional `latest_approval_id`
    - optional `latest_saved_note_path`
  - the first slice still avoids a separate memory store and still does not copy saved file bodies or approval preview bodies into the signal itself
  - serialized grounded-brief source messages may now also expose one optional `superseded_reject_signal`
  - that adjunct remains separate from `session_local_memory_signal.content_signal`
  - it replays only the latest superseded content-side `rejected` verdict plus its optional reject-note for the same `artifact_id` / `source_message_id`
  - it appears only when the current content signal no longer shows `rejected`
  - it remains audit-derived and narrow:
    - `replay_source = task_log_audit`
    - no saved body copy
    - no approval preview body copy
    - no approval-friction relabeling
    - no inferred preference statement
    - no cross-artifact aggregate
    - no list of many historical entries in the first replay slice
  - canonical source of truth still remains the current persisted session state for the current signal
  - the replay adjunct itself is derived only from same-anchor task-log records such as `content_verdict_recorded` and `content_reason_note_recorded`, without promoting task-log to the canonical current-state source
  - if note association is ambiguous, the helper should omit the optional replayed note instead of guessing
  - serialized grounded-brief source messages may now also expose one optional `historical_save_identity_signal`
  - that adjunct remains separate from `session_local_memory_signal.save_signal`
  - it should appear only when:
    - the current `save_signal` no longer exposes `latest_approval_id`
    - the same anchor still has visible save linkage worth preserving as current-state context
    - same-anchor save audit still preserves one earlier approval-backed save identity
  - the adjunct remains narrow and read-only:
    - `artifact_id`
    - `source_message_id`
    - `replay_source = task_log_audit`
    - optional `approval_id`
    - optional `save_content_source`
    - optional `saved_note_path`
    - optional `recorded_at`
  - the first shipped save-axis adjunct replays at most one latest historical approval-backed save identity
  - the first shipped slice uses same-anchor `write_note` audit with non-empty `approval_id` as the replay source because it already represents the actual persisted save boundary
  - if the current save linkage and the audit candidate disagree on save source or saved path, the helper should omit the replayed identity instead of guessing
  - the current MVP should keep that `write_note`-only replay rule as sufficient until a concrete insufficiency appears in operator use or focused regression
  - future `approval_granted` corroboration, if reopened, should stay additive and narrower than a second replay source:
    - it should only corroborate a same-anchor `write_note` candidate that already carries the same `approval_id`
    - it should never emit `historical_save_identity_signal` on `approval_granted` alone when no matching persisted `write_note` exists
    - it should not widen the helper into pending-approval replay or a broader save-history surface
  - it should not replay:
    - saved body copy
    - approval preview body copy
    - content verdict state
    - approval-friction relabeling
    - cross-artifact aggregate history
    - inferred preference statements
  - canonical current-state source still remains the current persisted session state, and task-log remains only the audit source for this narrow adjunct
  - later `approval_granted` corroboration remains a deferred refinement target, not a shipped replay requirement

#### 7. First Normalized `session_local_candidate`
- serialized grounded-brief source messages may now also expose one optional computed `session_local_candidate`, not a broader review or durable-memory surface
- the candidate must remain separate from:
  - the current source-message-anchored `session_local_memory_signal`
  - the historical adjuncts `superseded_reject_signal` and `historical_save_identity_signal`
  - future `durable_candidate`
  - future reviewed memory or user-level memory
- the minimum envelope should now be:
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
- the current signal itself should not be reused as the candidate because:
  - one source-message signal is still only a current-state working summary
  - the signal has no normalized reusable statement
  - the signal may legitimately drop superseded state after later explicit actions
  - the signal does not yet express support strength or candidate-family intent
- the shipped first candidate family stays narrow:
  - `candidate_family = correction_rewrite_preference`
  - the current first statement is the narrow deterministic string `explicit rewrite correction recorded for this grounded brief`
  - the statement should describe only the reusable rewrite preference signal, not copy the entire corrected body as the candidate itself
- the shipped first extraction rule stays conservative:
  - primary basis:
    - same source message with `content_signal.latest_corrected_outcome.outcome = corrected`
    - `content_signal.has_corrected_text = true`
    - same source message still keeps the original response snapshot needed to compare the original draft and the explicit correction
  - one eligible artifact may emit only one `session_local_candidate` draft in the current slice
  - that draft stays `session_local_candidate`, not `durable_candidate`
  - `supporting_signal_refs` should point back to source-message-anchored projections rather than copying their bodies into the candidate
  - the current shipped `supporting_signal_refs` set is intentionally narrower than the full contract:
    - `session_local_memory_signal.content_signal` is always the primary basis
    - `session_local_memory_signal.save_signal` may appear only when the same current anchor still exposes `latest_approval_id`
  - replay adjuncts remain supporting-context-only follow-up territory:
    - `superseded_reject_signal` does not become a primary extraction source
    - `historical_save_identity_signal` does not become a primary extraction source
    - the current shipped candidate does not reference those historical adjuncts yet
  - approval-backed save should remain supporting evidence only:
    - it may add current save support on the same anchor through `session_local_memory_signal.save_signal`
    - it should not be the sole basis for extracting the candidate
    - it should not turn the candidate into content confirmation or broader scope justification
- the shipped first candidate evidence-strength policy stays narrow:
  - `explicit_single_artifact` for one explicit corrected pair on one source message
  - current save support may add `session_local_memory_signal.save_signal` to `supporting_signal_refs`, but it does not raise `evidence_strength` in the first slice
  - future explicit confirmation may later define a stronger level, but that is not part of the first slice
- serialized grounded-brief source messages may now also expose one optional `candidate_confirmation_record`, still separate from `session_local_candidate`
- the current confirmation trace stays source-message-anchored and narrow:
  - `candidate_id`
  - `candidate_family = correction_rewrite_preference`
  - `candidate_updated_at`
  - `artifact_id`
  - `source_message_id`
  - `confirmation_scope = candidate_reuse`
  - `confirmation_label = explicit_reuse_confirmation`
  - `recorded_at`
- the current shipped response-card surface for that trace also stays narrow:
  - one small utility action such as `이 수정 방향 재사용 확인`
  - shown only when the current source message already exposes `session_local_candidate`
  - positive reuse confirmation only
  - separate from save approval, approval reject, approval reissue, no-save, retry, feedback `incorrect`, and reject-note input
- the current shipped candidate semantics remain unchanged even when confirmation is recorded:
  - `session_local_candidate` still keeps the same fixed statement and support refs
  - explicit confirmation stays a sibling trace, not a candidate field
  - `session_local_candidate` itself still does not serialize `has_explicit_confirmation`, `promotion_basis`, or `promotion_eligibility`
  - any `durable_candidate` remains a separate sibling projection on that same serialized source message
- approval-backed save remains supporting evidence only and must stay distinct from explicit confirmation:
  - save support alone must not create `candidate_confirmation_record`
  - explicit confirmation does not rewrite `supporting_signal_refs` or `evidence_strength`
- if a later explicit correction submit or non-`corrected` outcome supersedes the current pair on the same source message, stale `candidate_confirmation_record` should clear from current session state while append-only audit keeps the earlier `candidate_confirmation_recorded` event separately
- repeated same-session `correction_rewrite_preference` drafts should currently remain per-source-message in the MVP:
  - the current shipped candidate envelope is too broad to merge by family alone because `candidate_family`, the fixed statement, and the current `supporting_signal_refs` set do not yet identify which rewrite preference actually repeated
  - the current MVP should therefore not expose a session-level merge helper yet
- the first post-key aggregation boundary is now implemented as the current smallest cross-source read-only surface:
  - one optional top-level session read-only `recurrence_aggregate_candidates`
  - same-session only and derived from current session serialization only
  - separate from source-message `session_local_candidate`
  - separate from source-message `durable_candidate`
  - separate from `review_queue_items`
  - emitted only when at least two distinct grounded-brief source-message anchors in the same session share the same exact recurrence-key identity derived from the explicit corrected pair itself
  - same-source-message repeated updates count at most once because distinctness stays anchored by `artifact_id` + `source_message_id`
  - never emitted from `candidate_family` alone
  - never emitted from approval-backed save support, `superseded_reject_signal`, `historical_save_identity_signal`, queue presence, or review acceptance alone
  - kept read-only, non-promoting, and separate from reviewed-memory or user-level-memory semantics in the current first aggregation slice

#### 8. First Shipped `durable_candidate` Projection Contract
- current shipped boundary:
  - current `correction_rewrite_preference` `session_local_candidate` drafts remain narrow source-message candidate drafts and their object shape stays unchanged
  - the same serialized grounded-brief source message may now also expose one optional sibling `durable_candidate`
  - the same session payload may now also expose one top-level read-only `review_queue_items` projection derived from those current source-message `durable_candidate` records
  - no separate durable-candidate store, review API, reviewed memory, or user-level memory surface is introduced in this slice
- current promotion basis boundary:
  - explicit original-vs-corrected pair provides the current source-message candidate draft basis only:
    - the same grounded-brief source message still keeps `original_response_snapshot.draft_text`
    - the same source message keeps explicit user-submitted `corrected_text`
    - the same source message keeps `corrected_outcome.outcome = corrected`
    - normalized original draft and normalized corrected text are not identical
    - this is enough to emit one `session_local_candidate`, but not enough by itself to emit `durable_candidate`
  - `candidate_confirmation_record` adds one candidate-linked positive reuse confirmation for that same current draft:
    - it stays on the same source message
    - it stays keyed to the same `candidate_id`
    - it stays keyed to the same `candidate_updated_at`
    - it is explicit that the user wants later reuse of that rewrite direction
    - it is the first shipped primary promotion basis for the read-only projection
  - approval-backed save remains supporting evidence only:
    - it may remain inside `supporting_signal_refs` through current `session_local_memory_signal.save_signal`
    - it is never the primary promotion basis
    - it is never implicit content confirmation
    - it is never enough to materialize `durable_candidate` by itself
  - `session_local_memory_signal`, `historical_save_identity_signal`, and `superseded_reject_signal` remain supporting context only:
    - `session_local_memory_signal` stays the current-state working summary and source-message candidate basis
    - `historical_save_identity_signal` replays save identity, not reusable rewrite intent
    - `superseded_reject_signal` replays superseded reject history, not reusable rewrite intent
    - task-log replay alone must not be upgraded into a promotion basis
  - `candidate_family` alone is not a recurrence key:
    - it names a category, not the exact rewrite preference
    - the fixed statement and current `supporting_signal_refs` still do not identify what repeated across grounded briefs
- current projection surface and source contract:
  - the first materialization is one optional computed `durable_candidate` on the serialized grounded-brief source message only
  - canonical source remains current persisted session state on that same source message plus its same-message sibling traces:
    - `session_local_candidate`
    - `candidate_confirmation_record`
  - the join rule stays exact:
    - same `artifact_id`
    - same `source_message_id`
    - same `candidate_id`
    - same `candidate_updated_at`
  - stale or ambiguous confirmation matches omit the current `candidate_confirmation_record` serialization and therefore also omit `durable_candidate`
  - task-log remains audit-only and must not become the canonical source for the projection
- current shipped `durable_candidate` contract:
  - `candidate_id`
  - `candidate_scope = durable_candidate`
  - `candidate_family`
  - `statement`
  - `supporting_artifact_ids`
  - `supporting_source_message_ids`
  - `supporting_signal_refs`
  - `supporting_confirmation_refs`
  - `evidence_strength`
  - `has_explicit_confirmation = true`
  - `promotion_basis = explicit_confirmation`
  - `promotion_eligibility = eligible_for_review`
  - `created_at`
  - `updated_at`
  - current first slice reuses the source-message `session_local_candidate.candidate_id` while the projection stays source-message-anchored
- current first explicit-confirmation path stays minimal:
  - reuse the consumed source-message `session_local_candidate` values for:
    - `candidate_family`
    - `statement`
    - `supporting_artifact_ids`
    - `supporting_source_message_ids`
    - `supporting_signal_refs`
    - `evidence_strength`
  - add exactly one `supporting_confirmation_refs` item derived from the matching `candidate_confirmation_record`
  - set `created_at` and `updated_at` from `candidate_confirmation_record.recorded_at`
- minimum `supporting_confirmation_refs` item carries:
  - `artifact_id`
  - `source_message_id`
  - `candidate_id`
  - `candidate_updated_at`
  - `confirmation_label`
  - `recorded_at`
- current eligibility and guardrail rules:
  - one matching `candidate_confirmation_record` is enough to materialize one source-message-anchored `durable_candidate`
  - repeated same-session signals without a truthful recurrence key remain insufficient even when `candidate_family` matches
  - the current read-only review queue may surface that eligible record for inspection, but reviewed memory and user-level memory still remain closed
  - no suggested scope fields are emitted at this step
  - promotion still does not mean reviewed memory or user-level memory
- first truthful recurrence-key contract is now implemented and remains separate from the shipped `durable_candidate` / review surfaces:
  - the current contract name is one source-message-anchored `candidate_recurrence_key`
  - this key should mean the identity of one deterministic rewrite-transformation class recovered from the explicit original-vs-corrected pair for the current candidate family
  - for the current shipped family, this means:
    - same `candidate_family = correction_rewrite_preference`
    - same normalized rewrite-delta fingerprint derived from `original_response_snapshot.draft_text` plus explicit `corrected_text`
    - no claim of a broader semantic classifier or model-generated preference summary
  - `candidate_family` alone is still too broad:
    - it names only the family
    - it does not identify which rewrite direction repeated
  - the current fixed statement alone is still too broad:
    - `explicit rewrite correction recorded for this grounded brief` proves only that one explicit rewrite exists
    - it does not identify which rewrite transformation repeated
  - the current first `candidate_recurrence_key` draft is now implemented as one optional source-message-anchored read-only sibling on serialized grounded-brief source messages
  - the current envelope stays deterministic and local-only:
    - `candidate_family`
    - `key_scope = correction_rewrite_recurrence`
    - `key_version = explicit_pair_rewrite_delta_v1`
    - `derivation_source = explicit_corrected_pair`
    - `source_candidate_id`
    - `source_candidate_updated_at`
    - `normalized_delta_fingerprint`
    - optional `rewrite_dimensions`
    - `stability = deterministic_local`
    - `derived_at`
  - the identity-bearing part of the key is:
    - `candidate_family`
    - `key_version`
    - `normalized_delta_fingerprint`
  - the current derivation input stays narrow:
    - normalized `original_response_snapshot.draft_text`
    - normalized explicit `corrected_text`
    - the current source-message candidate family
  - the current omission rule stays strict:
    - if the repo cannot derive a deterministic normalized rewrite-delta fingerprint from that explicit pair without falling back to free-form summary or raw task-log replay, the key is omitted
    - if the current explicit pair is missing, unchanged after normalization, or no longer tied to the current source-message candidate version, the key is omitted
  - `candidate_review_record` may later strengthen recurrence evidence when it exists, but it does not replace the key itself:
    - reviewed-but-not-applied acceptance may help rank or trust a repeated key later
    - it does not make two same-family candidates equivalent by itself
  - approval-backed save and historical adjuncts remain supporting context only:
    - approval-backed save may support confidence, but never creates the key
    - `session_local_memory_signal`, `superseded_reject_signal`, and `historical_save_identity_signal` remain context only
    - queue presence alone, review acceptance alone, and task-log replay alone are never recurrence basis
  - the first repeated-signal threshold should stay conservative:
    - at least two distinct grounded briefs must expose candidates with the same recurrence key
    - distinctness is anchored by different `artifact_id` + `source_message_id`
    - repeated edits on one source message do not count as multi-brief recurrence
    - two is the first honest baseline for `correction_rewrite_preference`, but later families may require a stricter threshold or extra review support
- the first post-key aggregation boundary is now implemented as one current session-level read-only `recurrence_aggregate_candidates` projection:
  - same-session only:
    - current persisted session state is enough to derive the first aggregate surface without inventing a second canonical store
    - cross-session counting remains later than explicit local-store, rollback, conflict, and reviewed-memory boundary rules
  - one aggregate identity should require the same:
    - `candidate_family`
    - `key_scope`
    - `key_version`
    - `derivation_source`
    - `normalized_delta_fingerprint`
  - `source_candidate_id` and `source_candidate_updated_at` remain supporting refs only:
    - they keep the aggregate tied to current source-message candidate versions
    - they do not become the cross-source identity themselves
  - the current aggregate envelope stays narrow and read-only:
    - `aggregate_key`
    - `supporting_source_message_refs`
    - `supporting_candidate_refs`
    - optional `supporting_review_refs`
    - `aggregate_promotion_marker`
    - `reviewed_memory_precondition_status`
    - `reviewed_memory_boundary_draft`
    - `reviewed_memory_rollback_contract`
    - `reviewed_memory_disable_contract`
    - `reviewed_memory_conflict_contract`
    - `reviewed_memory_transition_audit_contract`
    - `reviewed_memory_unblock_contract`
    - `recurrence_count`
    - `scope_boundary = same_session_current_state_only`
    - `confidence_marker = same_session_exact_key_match`
    - `first_seen_at`
    - `last_seen_at`
  - `supporting_candidate_refs` and `supporting_review_refs` stay exact current-version joins on `artifact_id`, `source_message_id`, `candidate_id`, and `candidate_updated_at`
  - current `candidate_review_record` may surface only as optional support when it still matches the same current source-message candidate version
  - current `durable_candidate` remains supporting context only and is not repackaged as a second aggregate-ref list in this slice
  - approval-backed save, `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, queue presence, fixed statement text, `candidate_family` alone, and task-log replay alone must stay outside aggregate identity
  - the first aggregate surface must not overwrite source-message `candidate_recurrence_key`, must not reuse `review_queue_items` as its UI/storage surface, and must not imply repeated-signal promotion by itself
- the first post-aggregate promotion boundary is now fixed above that shipped aggregate surface:
  - choose `Option A` for the current MVP:
    - current same-session `recurrence_aggregate_candidates` remain promotion-ineligible
    - exact same-session aggregate identity is necessary, but still not sufficient, for any later promotion work
  - current reviewed-but-not-applied traces remain narrower than any later reviewed-memory layer:
    - source-message `candidate_review_record` remains one reviewed-but-not-applied trace for one current source-message candidate version
    - current `recurrence_aggregate_candidates` remains one same-session cross-source grouping surface
    - future reviewed memory remains a later rollbackable, disableable, conflict-visible, operator-auditable layer above both
  - current aggregate identity and current source-message version joins remain the only valid future basis inputs:
    - exact aggregate identity from current `recurrence_aggregate_candidates`
    - distinct grounded-brief source-message anchors only
    - current `durable_candidate` only when it still matches the same source-message candidate version
    - current `candidate_review_record` only as confidence support when it still matches the same source-message candidate version
  - review acceptance, approval-backed save, and historical adjuncts remain outside promotion identity:
    - review acceptance may strengthen later confidence, but it does not replace aggregate identity
    - approval-backed save remains supporting evidence only
    - `session_local_memory_signal`, `superseded_reject_signal`, and `historical_save_identity_signal` remain context only
    - queue presence alone, fixed statement text alone, `candidate_family` alone, and task-log replay alone remain outside promotion basis
  - the current contract now emits the smallest blocked marker only inside each current aggregate item:
    - `aggregate_promotion_marker`
    - `promotion_basis = same_session_exact_recurrence_aggregate`
    - `promotion_eligibility = blocked_pending_reviewed_memory_boundary`
    - `reviewed_memory_boundary = not_open`
    - `marker_version = same_session_blocked_reviewed_memory_v1`
    - `derived_at = last_seen_at`
  - the current contract now also emits one read-only blocked-only precondition status object inside each current aggregate item:
    - `reviewed_memory_precondition_status`
    - `status_version = same_session_reviewed_memory_preconditions_v1`
    - `overall_status = blocked_all_required`
    - `all_required = true`
    - ordered `preconditions`:
      - `reviewed_memory_boundary_defined`
      - `rollback_ready_reviewed_memory_effect`
      - `disable_ready_reviewed_memory_effect`
      - `conflict_visible_reviewed_memory_scope`
      - `operator_auditable_reviewed_memory_transition`
    - `evaluated_at = last_seen_at`
  - the current contract now also emits one read-only boundary draft object inside each current aggregate item:
    - `reviewed_memory_boundary_draft`
    - `boundary_version = fixed_narrow_reviewed_scope_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `aggregate_identity_ref`
    - `supporting_source_message_refs`
    - `supporting_candidate_refs`
    - optional `supporting_review_refs`
    - `boundary_stage = draft_not_applied`
    - `drafted_at = last_seen_at`
  - the current contract now also emits one read-only rollback-contract object inside each current aggregate item:
    - `reviewed_memory_rollback_contract`
    - `rollback_version = first_reviewed_memory_effect_reversal_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `aggregate_identity_ref`
    - `supporting_source_message_refs`
    - `supporting_candidate_refs`
    - optional `supporting_review_refs`
    - `rollback_target_kind = future_applied_reviewed_memory_effect_only`
    - `rollback_stage = contract_only_not_applied`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - `defined_at = last_seen_at`
  - the current contract now also emits one read-only disable-contract object inside each current aggregate item:
    - `reviewed_memory_disable_contract`
    - `disable_version = first_reviewed_memory_effect_stop_apply_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `aggregate_identity_ref`
    - `supporting_source_message_refs`
    - `supporting_candidate_refs`
    - optional `supporting_review_refs`
    - `disable_target_kind = future_applied_reviewed_memory_effect_only`
    - `disable_stage = contract_only_not_applied`
    - `effect_behavior = stop_apply_without_reversal`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - `defined_at = last_seen_at`
  - the current blocked marker stays truthful only while every reviewed-memory boundary precondition is still missing:
    - `reviewed_memory_boundary_defined`
      - future reviewed memory must have its own explicit local persistence/apply boundary above source-message and aggregate traces
      - the first reviewed scope should be fixed and narrow:
        - `same_session_exact_recurrence_aggregate_only`
        - tied to one current same-session aggregate identity plus its exact current supporting refs
        - not a small reviewed-scope enum in the first boundary slice
      - this is not source-message correction history, not `candidate_review_record`, not `recurrence_aggregate_candidates`, and not user-level memory
    - `rollback_ready_reviewed_memory_effect`
      - later reviewed-memory effect must be reversible without rewriting source-message traces, `candidate_recurrence_key`, or aggregate evidence
      - the first rollback target must stay fixed at one later applied reviewed-memory effect inside `same_session_exact_recurrence_aggregate_only`
      - the current `reviewed_memory_boundary_draft` remains a scope draft and basis ref, not the rollback target itself
      - rollback means explicit local operator-driven reversal of that later applied effect and stop of that effect's future influence
      - this is rollback of future reviewed-memory effect, not rollback of explicit corrected-text history
      - this must not delete `candidate_review_record`, delete `candidate_recurrence_key`, rewrite aggregate identity history, or treat boundary-draft deletion as canonical rollback
      - after rollback, aggregate identity, supporting refs, the current boundary draft, and operator-visible audit trace should remain while only the later applied effect may deactivate
    - `disable_ready_reviewed_memory_effect`
      - later reviewed-memory effect must support explicit local stop-apply without deleting source-message candidates, aggregate evidence, the current boundary draft, or the current rollback contract
      - the first disable target must stay fixed at one later applied reviewed-memory effect inside `same_session_exact_recurrence_aggregate_only`
      - disable means future influence stop without claiming reversal of that already-applied effect
      - this is not candidate deletion, not approval reject, not source-message review dismissal, and not rollback of explicit corrected-text history
      - after disable, aggregate identity, supporting refs, the current boundary draft, the current rollback contract, and operator-visible audit trace should remain while only the later applied effect may become inactive for future apply
    - `conflict_visible_reviewed_memory_scope`
      - future reviewed-memory layer must keep competing reviewed-memory targets visible inside one reviewed scope before any later apply
      - the first conflict-visible scope should stay fixed at `same_session_exact_recurrence_aggregate_only`
      - the first visible conflict categories should stay fixed and narrow:
        - `future_reviewed_memory_candidate_draft_vs_applied_effect`
        - `future_applied_reviewed_memory_effect_vs_applied_effect`
      - the visibility contract is tied to one current aggregate identity plus its exact current supporting refs
      - this is not a `corrected_text` diff viewer, not `candidate_review_record` promotion into a conflict object, not `candidate_recurrence_key` recalculation, and not aggregate identity-history rewrite
      - this must not auto-resolve, auto-disable, auto-rollback, or auto-apply anything
    - `operator_auditable_reviewed_memory_transition`
      - any later reviewed-memory transition above the blocked marker must leave one explicit local operator-visible trace with canonical transition identity
      - the first transition action vocabulary should stay fixed and narrow:
        - `future_reviewed_memory_apply`
        - `future_reviewed_memory_stop_apply`
        - `future_reviewed_memory_reversal`
        - `future_reviewed_memory_conflict_visibility`
      - operator-facing trace must keep reviewed scope, aggregate identity, exact basis refs, transition timing, and explicit local reason or note boundary visible
      - this is not `candidate_review_record`, not `candidate_recurrence_key`, not aggregate history rewrite, and not promotion of current boundary / rollback / disable / conflict contracts into transition results
      - current append-only `task_log` may mirror that trace, but it does not become the canonical reviewed-memory transition store
      - approval-backed save support, historical adjuncts, review acceptance, queue presence, and task-log replay alone must not create canonical transition state
  - current shipped contract objects still mean only `contract exists`:
    - the shipped `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`, `reviewed_memory_transition_audit_contract`, `reviewed_memory_unblock_contract`, and `reviewed_memory_capability_status` describe the reviewed-memory boundary family for the current aggregate
    - none of those read-only objects counts as `satisfied` by itself
    - approval-backed save support, historical adjuncts, review acceptance, queue presence, and `task_log` mirror existence must remain outside satisfaction basis
  - all listed preconditions are mandatory before the marker vocabulary can widen:
    - the first same-session unblock threshold stays binary and conservative:
      - current shipped `reviewed_memory_unblock_contract.unblock_status = blocked_all_required`
      - current shipped `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`
    - partial satisfaction, even if later inspectable, must stay blocked-only in the current phase
    - same-session unblock must not emit reviewed memory, apply, repeated-signal promotion, cross-session counting, or user-level memory
  - the first unblocked target remains narrower than apply:
    - keep `reviewed_memory_planning_target_ref.target_label = eligible_for_reviewed_memory_draft_planning_only`
    - interpret that target label as reviewed-memory draft planning only for one exact same-session aggregate
    - it does not mean emitted transition record already exists
    - it does not mean reviewed-memory apply already happened
    - it does not mean repeated-signal promotion, cross-session counting, or user-level memory opened
    - the current aggregate item now also emits one additive shared planning-target ref:
      - one read-only `reviewed_memory_planning_target_ref`
      - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
      - `target_label = eligible_for_reviewed_memory_draft_planning_only`
      - `target_scope = same_session_exact_recurrence_aggregate_only`
      - `target_boundary = reviewed_memory_draft_planning_only`
      - `defined_at = last_seen_at`
    - the shipped additive ref is now the canonical planning-target source
    - the first cleanup contract is now fixed and remains structural-only:
      - the one compatibility release window is now complete
      - the current shipped payload removes all three duplicated target echo fields together
      - docs, payload, and tests now read planning-target meaning only from `reviewed_memory_planning_target_ref`
      - do not reintroduce one or two fallback target strings
      - do not widen meaning into satisfaction, emitted transition record, or apply
  - the marker remains read-only and blocked:
    - no repeated-signal promotion
    - no reviewed-memory candidate store
    - no reviewed-memory apply path
    - no cross-session counting
  - the status object remains equally conservative:
    - `overall_status = blocked_all_required` remains the only current shipped status
    - no per-precondition satisfied / unsatisfied booleans yet
    - no partial-unblock workflow
    - no eligibility transition
    - no widening of current read-only contract objects into satisfied markers
  - the current contract now also emits one read-only conflict-contract object inside each current aggregate item:
    - `reviewed_memory_conflict_contract`
    - `conflict_version = first_reviewed_memory_scope_visibility_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `aggregate_identity_ref`
    - exact supporting refs
    - fixed `conflict_target_categories`:
      - `future_reviewed_memory_candidate_draft_vs_applied_effect`
      - `future_applied_reviewed_memory_effect_vs_applied_effect`
    - `conflict_visibility_stage = contract_only_not_resolved`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - `defined_at = last_seen_at`
    - no auto-resolve, no auto-disable, no auto-rollback, and no auto-apply
  - the current contract now also emits one read-only transition-audit object inside each current aggregate item:
    - `reviewed_memory_transition_audit_contract`
    - `audit_version = first_reviewed_memory_transition_identity_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `aggregate_identity_ref`
    - exact supporting refs
    - fixed `transition_action_vocabulary`:
      - `future_reviewed_memory_apply`
      - `future_reviewed_memory_stop_apply`
      - `future_reviewed_memory_reversal`
      - `future_reviewed_memory_conflict_visibility`
    - `transition_identity_requirement = canonical_local_transition_id_required`
    - `operator_visible_reason_boundary = explicit_reason_or_note_required`
    - `audit_stage = contract_only_not_emitted`
    - `audit_store_boundary = canonical_transition_record_separate_from_task_log`
    - `post_transition_invariants = aggregate_identity_and_contract_refs_retained`
    - `defined_at = last_seen_at`
    - no auto-apply, no auto-disable, no auto-rollback, no auto-resolve, and no auto-repair
  - the first emitted-transition-record layer is now implemented:
    - one aggregate-level read-only `reviewed_memory_transition_record`
    - `transition_record_version = first_reviewed_memory_transition_record_v1`
    - one `canonical_transition_id`
    - one `transition_action` chosen from the shipped `transition_action_vocabulary`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - one explicit `operator_reason_or_note`
    - `record_stage = emitted_record_only_not_applied`
    - `task_log_mirror_relation = mirror_allowed_not_canonical`
    - `emitted_at`
    - persisted on the session under `reviewed_memory_emitted_transition_records`
    - emitted only at the enabled aggregate-card submit boundary after truthful `unblocked_all_required` and a non-empty operator reason note
    - `record_stage = emitted_record_only_not_applied` means reviewed-memory apply is NOT triggered
    - it remains smaller than reviewed-memory apply, repeated-signal promotion, cross-session counting, and user-level memory
  - the current contract now also emits one read-only unblock-contract object inside each current aggregate item:
    - `reviewed_memory_unblock_contract`
    - `unblock_version = same_session_reviewed_memory_unblock_v1`
    - exact ordered `required_preconditions`
    - `unblock_status = blocked_all_required`
    - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
    - `partial_state_policy = partial_states_not_materialized`
    - `evaluated_at = last_seen_at`
    - current object existence still does not mean `unblocked_all_required`
  - the current contract now also emits one read-only capability-status object inside each current aggregate item:
    - `reviewed_memory_capability_status`
    - `capability_version = same_session_reviewed_memory_capabilities_v1`
    - exact `required_preconditions`
    - `capability_outcome`
      - current shipped state = `unblocked_all_required`
      - no later wider capability-outcome state is currently defined in the MVP slice
    - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
    - `partial_state_policy = partial_states_not_materialized`
    - `evaluated_at`
    - current object existence still does not mean `unblocked_all_required`
    - it does not overwrite the shipped `reviewed_memory_unblock_contract`
    - it remains smaller than emitted transition records and reviewed-memory apply
  - the current truthful capability-path source stays one separate internal helper family above the shipped status surfaces:
    - one current internal `reviewed_memory_capability_source_refs`
    - `source_version = same_session_reviewed_memory_capability_source_refs_v1`
    - `source_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - exact `required_preconditions`
    - one `capability_source_refs`
      - `boundary_source_ref`
      - `rollback_source_ref`
      - `disable_source_ref`
      - `conflict_source_ref`
      - `transition_audit_source_ref`
    - `source_status = all_required_sources_present`
    - `evaluated_at`
    - it remains additive internal local capability machinery, not a current payload surface
    - current contract-object existence alone must not backfill this source family
    - approval-backed save support, historical adjuncts, source-message review acceptance, queue presence, and `task_log` replay alone must not backfill this source family
    - current implementation now also evaluates this internal source family for the same aggregate, and it now resolves one real `boundary_source_ref` backer against the same exact aggregate's `검토 메모 적용 시작` trigger affordance
    - current implementation now also materializes one internal same-aggregate `reviewed_memory_reversible_effect_handle` only from one exact matching shared target plus the current exact `reviewed_memory_rollback_contract`, while reusing the same exact aggregate identity, supporting refs, matching `boundary_source_ref`, and one deterministic `defined_at`
    - current implementation now also resolves one internal `rollback_source_ref` only as one exact ref to that same handle
    - current implementation now also resolves one internal `disable_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_disable_contract` plus the shared `reviewed_memory_applied_effect_target`; it materializes only when both the disable contract and the applied-effect target truthfully match the same exact aggregate scope
    - current implementation now also resolves one internal `conflict_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_conflict_contract` plus the shared `reviewed_memory_applied_effect_target`; it materializes only when both the conflict contract and the applied-effect target truthfully match the same exact aggregate scope
    - current implementation now also resolves one internal `transition_audit_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_transition_audit_contract` plus the shared `reviewed_memory_applied_effect_target`; the internal `reviewed_memory_capability_source_refs` family is now complete with all five refs resolved
    - `reviewed_memory_capability_basis` is now materialized above the complete source family; `capability_outcome` is now `unblocked_all_required`
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_proof_record` helper for that same exact aggregate, and it now materializes only from one exact same-session internal `reviewed_memory_local_effect_presence_proof_record_store` entry for that aggregate; current implementation now also truthfully mints one exact payload-hidden canonical proof-record/store entry for the current exact aggregate state inside that internal boundary while the helper keeps `first_seen_at` alone, source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay outside that lower canonical proof-record layer
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_proof_boundary` helper for that same exact aggregate, and it now materializes one internal same-aggregate proof boundary only from one exact matching canonical local proof record/store entry while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from one exact matching proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source result only from one exact matching fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event` helper for that same exact aggregate, and it now materializes one internal same-aggregate event result only from one exact matching fact-source result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event_producer` helper for that same exact aggregate, and it now materializes one internal same-aggregate producer result only from one exact matching event result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate event-source result only from one exact matching producer result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_record` helper for that same exact aggregate, and it now materializes one internal same-aggregate source-consumer record only from one exact matching event-source helper result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current implementation now also evaluates one internal `reviewed_memory_applied_effect_target` helper for that same exact aggregate, and it now materializes one internal same-aggregate shared target only from one exact matching source-consumer helper result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current implementation now also evaluates one internal `reviewed_memory_reversible_effect_handle` helper for that same exact aggregate, and it now materializes one internal same-aggregate rollback-capability handle only from one exact matching shared target plus one exact matching rollback contract; that layer stays payload-hidden
    - the exact future real rollback-capability backer should stay one later internal local `reviewed_memory_reversible_effect_handle`:
      - `handle_version = first_same_session_reviewed_memory_reversible_effect_handle_v1`
      - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
      - one `aggregate_identity_ref`
      - exact supporting refs
      - one matching `boundary_source_ref`
      - one matching `rollback_contract_ref`
      - `effect_target_kind = applied_reviewed_memory_effect`
      - `effect_capability = reversible_local_only`
      - `effect_invariant = retain_identity_supporting_refs_boundary_and_audit`
      - `effect_stage = handle_defined_not_applied`
      - one local `handle_id`
      - `defined_at`
    - this later internal handle remains above the shipped read-only `reviewed_memory_rollback_contract` and below any later payload-visible basis object, emitted transition record, or reviewed-memory apply result
    - the exact later local target beneath that handle should stay one shared internal `reviewed_memory_applied_effect_target`:
      - `target_version = first_same_session_reviewed_memory_applied_effect_target_v1`
      - `target_scope = same_session_exact_recurrence_aggregate_only`
      - one `aggregate_identity_ref`
      - exact supporting refs
      - one matching `boundary_source_ref`
      - `effect_target_kind = applied_reviewed_memory_effect`
      - `target_capability_boundary = local_effect_presence_only`
      - `target_stage = effect_present_local_only`
      - one local `applied_effect_id`
      - `present_locally_at`
    - the exact later local proof boundary beneath the current fact-source-instance helper should stay one shared internal `reviewed_memory_local_effect_presence_proof_boundary`:
      - `proof_boundary_version = first_same_session_reviewed_memory_local_effect_presence_proof_boundary_v1`
      - `proof_boundary_scope = same_session_exact_recurrence_aggregate_only`
      - one `aggregate_identity_ref`
      - exact supporting refs
      - one matching `boundary_source_ref`
      - `effect_target_kind = applied_reviewed_memory_effect`
      - `proof_capability_boundary = local_effect_presence_only`
      - `proof_stage = first_presence_proved_local_only`
      - one local `applied_effect_id`
      - `present_locally_at`
    - the exact later canonical local proof record beneath that proof-boundary helper should stay one internal `reviewed_memory_local_effect_presence_proof_record`:
      - `proof_record_version = first_same_session_reviewed_memory_local_effect_presence_proof_record_v1`
      - `proof_record_scope = same_session_exact_recurrence_aggregate_only`
      - one `aggregate_identity_ref`
      - exact supporting refs
      - one matching `boundary_source_ref`
      - `effect_target_kind = applied_reviewed_memory_effect`
      - `proof_capability_boundary = local_effect_presence_only`
      - `proof_record_stage = canonical_presence_recorded_local_only`
      - one local `applied_effect_id`
      - `present_locally_at`
    - `first_seen_at` stays necessary-only at that lower layer:
      - it must already exist before a canonical local proof record may materialize
      - it must not become the proof record by itself
      - `present_locally_at` may reuse `first_seen_at` only when the proof record is actually minted at that exact same instant
    - the current `reviewed_memory_local_effect_presence_proof_boundary` helper now materializes only from one exact matching `reviewed_memory_local_effect_presence_proof_record` inside one same-session internal `reviewed_memory_local_effect_presence_proof_record_store` boundary for the same aggregate
    - the current `reviewed_memory_local_effect_presence_fact_source_instance` helper now materializes only from one exact matching `reviewed_memory_local_effect_presence_proof_boundary` for the same aggregate
    - the exact later local fact source beneath that raw helper should stay one shared internal `reviewed_memory_local_effect_presence_fact_source`:
      - `fact_source_version = first_same_session_reviewed_memory_local_effect_presence_fact_source_v1`
      - `fact_source_scope = same_session_exact_recurrence_aggregate_only`
      - one `aggregate_identity_ref`
      - exact supporting refs
      - one matching `boundary_source_ref`
      - `effect_target_kind = applied_reviewed_memory_effect`
      - `fact_capability_boundary = local_effect_presence_only`
      - `fact_stage = presence_fact_available_local_only`
      - one local `applied_effect_id`
      - `present_locally_at`
    - this local fact source stays above that proof-boundary helper and above that smaller canonical local proof record/store that first mints `applied_effect_id` and `present_locally_at`, and it stays smaller than the raw-event helper result, the producer helper result, the event-source helper result, the source-consumer helper result, the shared target, the rollback handle, the full source family, the now-materialized basis object, any later `unblocked_all_required`, any emitted transition record, and any reviewed-memory apply result
    - the first local identity rule should stay minimal:
      - do not add a second fact id in the first contract
      - reuse `applied_effect_id` as the first local identity minted exactly at the truthful local fact-source instant
      - keep `present_locally_at` as that same first truthful local instant and reuse `aggregate.last_seen_at` only when it is exactly that instant
    - the exact later local effect-presence event above that fact source and beneath that producer helper should stay one shared internal `reviewed_memory_local_effect_presence_event`:
      - `event_version = first_same_session_reviewed_memory_local_effect_presence_event_v1`
      - `event_scope = same_session_exact_recurrence_aggregate_only`
      - one `aggregate_identity_ref`
      - exact supporting refs
      - one matching `boundary_source_ref`
      - `effect_target_kind = applied_reviewed_memory_effect`
      - `event_capability_boundary = local_effect_presence_only`
      - `event_stage = presence_observed_local_only`
      - one local `applied_effect_id`
      - `present_locally_at`
    - this local event is the first later same-aggregate event layer above that smaller fact source and below the producer helper, and it stays smaller than the producer helper result, the event-source helper result, the source-consumer helper result, the shared target, the rollback handle, the full source family, the now-materialized basis object, any later `unblocked_all_required`, any emitted transition record, and any reviewed-memory apply result
    - the exact local effect-presence event source above that producer-helper result and beneath the source-consumer helper should stay one shared internal `reviewed_memory_local_effect_presence_event_source`:
      - `event_source_version = first_same_session_reviewed_memory_local_effect_presence_event_source_v1`
      - `event_source_scope = same_session_exact_recurrence_aggregate_only`
      - one `aggregate_identity_ref`
      - exact supporting refs
      - one matching `boundary_source_ref`
      - `effect_target_kind = applied_reviewed_memory_effect`
      - `event_capability_boundary = local_effect_presence_only`
      - `event_stage = presence_event_recorded_local_only`
      - one local `applied_effect_id`
      - `present_locally_at`
    - this later internal target should stay shared by the later rollback handle and the later disable handle, while each handle still keeps its own contract linkage and capability meaning
    - the target itself must not carry `rollback_contract_ref` or `disable_contract_ref`; later handles must bind that shared target back to the matching contract ref separately
    - the current raw-event helper `reviewed_memory_local_effect_presence_event` now materializes only from one exact matching `reviewed_memory_local_effect_presence_fact_source` for the same aggregate
    - the current producer helper `reviewed_memory_local_effect_presence_event_producer` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event` for the same aggregate
    - the current event-source helper `reviewed_memory_local_effect_presence_event_source` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event_producer` for the same aggregate
    - the current source-consumer helper `reviewed_memory_local_effect_presence_record` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event_source` for the same aggregate
    - the current target helper now materializes only from that exact matching source-consumer helper result for the same aggregate
    - current contract existence, blocked trigger visibility, approval-backed save support, historical adjuncts, source-message review acceptance, queue presence, and `task_log` replay alone must not invent that handle
    - current contract existence, blocked trigger visibility, approval-backed save support, historical adjuncts, source-message review acceptance, queue presence, and `task_log` replay alone must not invent that shared applied-effect target either
    - current contract existence, blocked trigger visibility, approval-backed save support, historical adjuncts, source-message review acceptance, queue presence, and `task_log` replay alone must not invent that local fact source, that local effect-presence event, that later producer helper result, that later event-source helper result, or the later source-consumer helper result either
    - the full internal `reviewed_memory_capability_source_refs` family is now complete with all five refs resolved in the current repo
  - the current truthful capability-path basis stays one separate read-only object above that source layer, not a reinterpretation of current contract existence:
    - one current `reviewed_memory_capability_basis`
    - `basis_version = same_session_reviewed_memory_capability_basis_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - exact `required_preconditions`
    - `basis_status = all_required_capabilities_present`
    - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
    - `evaluated_at`
    - this basis object must rest on one matching internal `reviewed_memory_capability_source_refs`, not on current contract existence alone
    - approval-backed save support, historical adjuncts, source-message review acceptance, queue presence, and `task_log` replay alone must not backfill this object
    - current `capability_outcome = unblocked_all_required` is truthful only when the same exact aggregate still matches the current contract chain, this separate capability-source family exists, and this separate capability-basis object also exists
    - current implementation now also emits this basis layer for the same aggregate when the full matching source family exists, and `capability_outcome` is now `unblocked_all_required`
  - the current contract now also emits one additive planning-target ref inside each current aggregate item:
    - `reviewed_memory_planning_target_ref`
    - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
    - `target_label = eligible_for_reviewed_memory_draft_planning_only`
    - `target_scope = same_session_exact_recurrence_aggregate_only`
    - `target_boundary = reviewed_memory_draft_planning_only`
    - `defined_at = last_seen_at`
    - it is the current canonical planning-target source for the aggregate item
    - the earlier duplicated target echoes have now been removed together in one cleanup-only pass
    - it remains smaller than blocked/satisfied outcome, emitted transition records, and reviewed-memory apply
  - the current satisfied capability outcome remains narrower than apply:
    - `unblocked_all_required` means all required reviewed-memory capability family is actually satisfied for one exact same-session aggregate
    - that state must rest on one matching `reviewed_memory_capability_basis`, not on read-only contract existence alone
    - that state opens reviewed-memory draft planning only
    - that state only authorizes later aggregate-card enablement and stays smaller than emitted transition record
    - it does not mean emitted transition record already exists
    - it does not mean reviewed-memory apply already happened
    - it does not mean repeated-signal promotion, cross-session counting, or user-level memory opened
  - the shipped boundary draft remains equally conservative:
    - no readiness or satisfaction tracker
    - no reviewed-memory apply result
    - no cross-session scope
  - the shipped rollback contract remains equally conservative:
    - it stays contract-only above the shipped boundary draft
    - it does not become reviewed-memory apply result, store write, or rollback state machine
    - it keeps `rollback_target_kind = future_applied_reviewed_memory_effect_only`
    - it keeps aggregate identity plus exact supporting refs visible
    - it does not widen into cross-session scope
  - the shipped disable contract remains equally conservative:
    - one read-only `reviewed_memory_disable_contract`
    - `disable_version = first_reviewed_memory_effect_stop_apply_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - `disable_target_kind = future_applied_reviewed_memory_effect_only`
    - `disable_stage = contract_only_not_applied`
    - `effect_behavior = stop_apply_without_reversal`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - no reviewed-memory apply result, no store write, and no cross-session widening
- current next practical path:
  - the current read-only review queue now consumes only `promotion_eligibility = eligible_for_review` `durable_candidate` records
  - the current first `accept` review action now also consumes that same current source-message-anchored basis instead of inventing a second canonical candidate source
  - the shipped `candidate_recurrence_key` plus shipped same-session `recurrence_aggregate_candidates` now provide the first truthful cross-source recurrence surface, and the shipped `aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`, `reviewed_memory_transition_audit_contract`, `reviewed_memory_unblock_contract`, `reviewed_memory_capability_status`, plus additive `reviewed_memory_planning_target_ref` now make the current blocked boundary plus shared planning-only target explicit without opening promotion or apply
  - current same-session aggregates still remain promotion-ineligible until the exact reviewed-memory precondition family is satisfied in full:
    - `reviewed_memory_boundary_defined`
    - `rollback_ready_reviewed_memory_effect`
    - `disable_ready_reviewed_memory_effect`
    - `conflict_visible_reviewed_memory_scope`
    - `operator_auditable_reviewed_memory_transition`
  - satisfying the full family later means one exact internal capability-source family can resolve actual reviewed-memory-layer presence for the same exact aggregate scope:
    - `reviewed_memory_boundary_defined` is satisfied only when one internal `boundary_source_ref` can bind one exact aggregate identity plus exact supporting refs above the current boundary draft
    - current implementation now resolves that first backer against one canonical local aggregate trigger-affordance ref with the fixed action label `검토 메모 적용 시작`; that lower internal ref still serializes `trigger_state = visible_disabled`, while the current operator-facing aggregate-card submit boundary above it is enabled when `capability_outcome = unblocked_all_required` and the user has entered a non-empty reason note
    - `rollback_ready_reviewed_memory_effect` is satisfied only when one internal `rollback_source_ref` can point to a later effect-capability source that can actually reverse one future applied reviewed-memory effect without changing aggregate identity
    - that later rollback-capability source should stay one internal local `reviewed_memory_reversible_effect_handle` bound to the same exact aggregate, the same exact supporting refs, the same `boundary_source_ref`, and the same `reviewed_memory_rollback_contract`
    - that handle must later point to one shared internal `reviewed_memory_applied_effect_target` for the same exact aggregate, while the handle keeps rollback-only capability meaning through its own matching `rollback_contract_ref`
    - that shared target must stay smaller than the handle, smaller than the full source family, and smaller than the now-materialized basis object, any later emitted transition record, or any later reviewed-memory apply result
    - that shared target must later materialize only from one shared internal `reviewed_memory_local_effect_presence_record`, and that source-consumer helper must in turn materialize only from one exact shared internal `reviewed_memory_local_effect_presence_event_source`
    - that event-source helper must later materialize only from one exact shared internal `reviewed_memory_local_effect_presence_event_producer` for the same exact aggregate, exact supporting refs, and the same `boundary_source_ref`
    - that producer helper must later materialize only from one exact shared internal `reviewed_memory_local_effect_presence_event`, and that raw-event helper must in turn materialize only from one exact shared internal `reviewed_memory_local_effect_presence_fact_source` for the same exact aggregate, exact supporting refs, and the same `boundary_source_ref`
    - `disable_ready_reviewed_memory_effect` is satisfied only when one internal `disable_source_ref` can point to a later effect-capability source that can actually stop apply without claiming reversal
    - the first honest contract now keeps that later disable-capability source separate from rollback semantics while still allowing it to reuse the same internal `reviewed_memory_local_effect_presence_record` and its underlying shared `reviewed_memory_local_effect_presence_event_source` through the same shared target and its own later disable-side handle with matching `disable_contract_ref`
    - `conflict_visible_reviewed_memory_scope` is satisfied only when one internal `conflict_source_ref` can point to a later local source that actually exposes competing reviewed-memory targets inside the same exact scope before apply
    - `operator_auditable_reviewed_memory_transition` is satisfied only when one internal `transition_audit_source_ref` can point to a later local source that can emit canonical transition records separate from `task_log`
  - the first truthful capability path above that family should stay two steps smaller than emitted record:
    - resolve one separate internal `reviewed_memory_capability_source_refs` only when all five per-capability source refs exist for the same exact aggregate scope
    - current implementation now resolves all five same-aggregate capability refs: `boundary_source_ref`, `rollback_source_ref`, `disable_source_ref`, `conflict_source_ref`, and `transition_audit_source_ref`; the internal `reviewed_memory_capability_source_refs` family is now complete while staying payload-hidden
    - materialize one separate read-only `reviewed_memory_capability_basis` only when that same exact aggregate still matches both the current contract chain and that matching source family
    - let `reviewed_memory_capability_status.capability_outcome = unblocked_all_required` become truthful only when that same matching basis object exists
    - do not create `canonical_transition_id`, `operator_reason_or_note`, or `emitted_at` at that capability-path boundary
    - do not require `task_log` mirroring at that capability-path boundary
  - the shipped readiness-threshold surface now stays separate from the current blocked-only status object:
    - one read-only `reviewed_memory_unblock_contract`
    - exact `required_preconditions`
    - binary `unblock_status`
    - `partial_state_policy = partial_states_not_materialized`
    - deterministic `evaluated_at`
  - the shipped satisfied-capability outcome surface now stays separate from the shipped unblock contract:
    - one read-only `reviewed_memory_capability_status`
    - keep the shipped `reviewed_memory_unblock_contract` as the blocked-threshold contract only
    - let the shipped capability-status surface carry current `capability_outcome = unblocked_all_required`
    - keep both surfaces narrower than emitted transition records and reviewed-memory apply
    - keep the current shipped planning-only target meaning centralized on `reviewed_memory_planning_target_ref.target_label`
    - do not reintroduce duplicated target echo fields as hidden fallbacks
    - do not add a post-cleanup compatibility note that restates removed echo fields as active current schema; root spec text should stay shared-ref-only
  - the next widening should still stay closed:
    - current shipped contract objects remain `contract exists` only until later machinery can satisfy them
    - keep the shipped transition-audit contract contract-only while the emitted `reviewed_memory_transition_record` is the layer above it
    - the current shell now exposes the first operator-visible trigger-source affordance on one separate aggregate-level surface fed only by `recurrence_aggregate_candidates`, not on source-message cards and not in `review_queue_items`
    - keep that aggregate surface inside the existing shell session stack as one separate section adjacent to `검토 후보`, not as a modal, dashboard, or workspace
    - the aggregate-card submit boundary is now enabled when `capability_outcome = unblocked_all_required`:
      - show one aggregate-card action label `검토 메모 적용 시작`
      - show a mandatory `operator_reason_or_note` textarea on the aggregate card when unblocked
      - keep the submit button disabled while `capability_outcome = blocked_all_required` or while the textarea is empty
      - clicking the enabled submit now emits one `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` and persists it under `reviewed_memory_emitted_transition_records`; reviewed-memory apply is NOT triggered
      - `reviewed_memory_transition_record` is absent while blocked; emitted only at the enabled submit boundary
    - the emitted-record layer is now separate from the capability-path layer:
      - current truthful `unblocked_all_required` requires one matching internal `reviewed_memory_capability_source_refs` plus one matching `reviewed_memory_capability_basis`
      - that capability-path layer alone must not mint `canonical_transition_id`, collect `operator_reason_or_note`, mint `emitted_at`, or emit `reviewed_memory_transition_record` without an actual enabled-submit action
    - the first truthful emission trigger is one explicit operator-visible `future_reviewed_memory_apply` transition only
    - that first emitted record materializes only when one exact same-session aggregate already has truthful `capability_outcome = unblocked_all_required` and the aggregate-card submission provides one real `canonical_transition_id`, one explicit `operator_reason_or_note`, and one local `emitted_at`
    - `future_reviewed_memory_stop_apply` is now also implemented and is no longer later (see stop-apply contract below); `future_reviewed_memory_reversal` is now also implemented and is no longer later (see reversal contract below): after stop-apply (`record_stage = stopped`) the aggregate card shows an `적용 되돌리기` button; clicking it changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; aggregate identity, supporting refs, and contracts are retained; reversal is separate from stop-apply
    - `future_reviewed_memory_conflict_visibility` is now also implemented: after the effect is reversed the aggregate card shows a `충돌 확인` button; clicking it creates a separate conflict-visibility transition record with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, evaluated `conflict_entries` and `conflict_entry_count`, and `source_apply_transition_ref`; the record is separate from the apply transition record; keep repeated-signal promotion, broader durable promotion, and cross-session counting later
    - keep `transition-audit contract exists`, `operator-visible trigger-source layer exists`, `transition record emitted`, and `reviewed-memory apply result` as four separate layers
    - keep `truthful unblocked capability path exists` as its own layer between trigger affordance and emitted transition record
    - keep `task_log` append-only, mirror-only, and non-canonical even after emitted transition records exist
    - keep first-round `task_log` mirroring optional; canonical emitted record must be sufficient by itself before any mirror is added
    - `reviewed_memory_capability_basis` is now truthfully materialized above the complete internal source family; the truthful `unblocked_all_required` path is implemented, the enabled aggregate-card submit boundary is open, and one truthful `reviewed_memory_transition_record` is now emitted at that boundary; the reviewed-memory apply boundary is now also implemented: after emission the aggregate card shows a `검토 메모 적용 실행` button, clicking it changes `record_stage` from `emitted_record_only_not_applied` to `applied_pending_result` and adds `applied_at` via POST `/api/aggregate-transition-apply`; the apply result is now also implemented: after the apply boundary the card shows `결과 확정`, clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply (`future_reviewed_memory_stop_apply`) is now also implemented: after the effect is active the aggregate card shows an `적용 중단` button; clicking it changes `record_stage` to `stopped`, sets `apply_result.result_stage` to `effect_stopped`, removes the effect from `reviewed_memory_active_effects`, and future responses no longer include the `[검토 메모 활성]` prefix; reversal (`future_reviewed_memory_reversal`) is now also implemented: after the effect is stopped the aggregate card shows an `적용 되돌리기` button; clicking it changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; aggregate identity, supporting refs, and contracts are retained; reversal is separate from stop-apply; conflict visibility (`future_reviewed_memory_conflict_visibility`) is now also implemented: after the effect is reversed the aggregate card shows a `충돌 확인` button; clicking it creates a separate conflict-visibility transition record with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, evaluated `conflict_entries` and `conflict_entry_count`, and `source_apply_transition_ref`; the conflict visibility record is separate from the apply transition record and does not mutate it
    - keep operator audit separate from rollback, disable, and conflict semantics even after transition identity vocabulary is now materialized
    - no per-precondition satisfaction booleans yet
    - no widening of the shipped boundary draft into readiness or apply result
    - no payload-visible reviewed-memory store and no payload-visible proof-record or proof-boundary surface
    - no reviewed-memory apply result
    - no repeated-signal promotion
    - no cross-session counting
  - repeated-signal promotion, cross-session aggregation, reviewed history, merge helper reopen, and user-level memory all remain later than this aggregate projection

#### 9. Session-Level Memory Vs Future User-Level Memory
- session-level memory:
  - attached to the current session and immediate follow-up loop
  - should begin as one artifact-scoped `session_local_memory_signal`, not as a cross-artifact preference record
  - may guide retries or next-brief improvements inside the same session
- durable candidate:
  - may outlive the session as a reviewable local record
  - is still not the same thing as user-level memory
- future user-level memory:
  - remains a design target after the candidate-review layer exists
  - should require explicit accept/edit/reject controls, rollback, scope rules, and conflict handling
- current shipped contract does not include user profiles or always-on cross-session preference application

#### 10. Review Surface Before Future User-Level Memory
- current shipped first slice:
  - the session payload may expose one read-only `review_queue_items` list
  - the existing shell may render that list as one compact `검토 후보` section
  - only current `durable_candidate` items with `promotion_eligibility = eligible_for_review` may enter
  - each queue item is only a repackaging of the current source-message `durable_candidate`, not a second canonical durable object
  - the current queue action stays narrow:
    - `accept` only
    - reviewed-but-not-applied only
    - no edit
    - no reject
    - no defer
- `session_local` items should never skip directly into future user-level memory
- first shipped review-outcome trace stays source-message-anchored instead of opening a second durable store:
  - one optional sibling `candidate_review_record` on the same grounded-brief source message
  - canonical source remains current persisted session state
  - current task-log remains audit-only
  - this trace may later appear only as optional aggregate `supporting_review_refs`; it must not become the aggregate-level `future_reviewed_memory_apply` trigger source
- minimum shipped `candidate_review_record` contract:
  - `candidate_id`
  - `candidate_updated_at`
  - `artifact_id`
  - `source_message_id`
  - `review_scope = source_message_candidate_review`
  - `review_action = accept`
  - `review_status = accepted`
  - `recorded_at`
- later contract vocabulary still includes:
  - `accept`
    - means the current source-message `durable_candidate` was explicitly reviewed as reusable
    - does not mean the same candidate was already applied as user-level memory
    - does not rewrite the source-message `durable_candidate` or `corrected_text`
  - `edit`
    - means the reviewed reusable statement is adjusted at review time through `reviewed_statement`
    - does not rewrite the original-vs-corrected pair or the source-message `durable_candidate.statement`
    - does not mean the source-message corrected text itself was edited again
  - `reject`
    - means the current source-message `durable_candidate` was dismissed as a reviewed candidate
    - does not mean content reject, approval reject, no-save, retry, or feedback `incorrect`
  - `defer`
    - means later revisit is needed for the current source-message `durable_candidate`
    - does not invalidate the underlying explicit corrected pair or explicit confirmation basis
    - does not mean queue-only clear of the source-message candidate basis
- first queue-transition contract:
  - `review_queue_items` remain the pending-only inspection surface
  - a queue item should appear only when the same current source message still exposes:
    - current `durable_candidate`
    - `promotion_eligibility = eligible_for_review`
    - no matching current `candidate_review_record` on the same `artifact_id`, `source_message_id`, `candidate_id`, and `candidate_updated_at`
  - after one matching `accept` record is present for that current candidate version, the item should leave the pending queue
  - the first action-capable slice should not add a second queue section, tab, or page for accepted / edited / rejected / deferred items
  - until a later reviewed-memory or review-history surface exists, actioned items remain visible only through the source-message anchor plus audit log
  - aggregate-level reviewed-memory transition initiation must stay outside this queue:
    - `review_queue_items` must not host `future_reviewed_memory_apply`
    - source-message `accept` must not be reinterpreted as reviewed-memory apply trigger
    - `candidate_review_record` must not become canonical transition identity, `operator_reason_or_note`, or `emitted_at` basis
- current shipped first implementation slice after the read-only queue:
  - `accept` only is implemented
  - one source-message `candidate_review_record` is recorded with `review_action = accept` and `review_status = accepted`
  - the matching item leaves pending `review_queue_items`
  - the result stays reviewed-but-not-applied:
    - no user-level memory apply
    - no scope suggestion fields
    - no second review dashboard
    - no edit / reject / defer UI in the same slice
- review actor assumption:
  - the same local user on the same machine
- current repo still does not implement `edit` / `reject` / `defer`, reviewed memory store, or user-level memory store

#### 11. Scope / Conflict / Rollback Principles
- these principles remain later than the first source-message `candidate_review_record`
- the first review-action contract should keep `review_scope = source_message_candidate_review` fixed
- `proposed_scope`, `scope_candidates_considered`, and `scope_suggestion_reason` remain future review-to-memory inputs, not first review-action trace fields
- future reviewed memory may later use one of these scope candidates:
  - `workflow_type`
  - `path_family`
  - `document_type`
  - `global`
- suggested-scope policy:
  - when multiple scope candidates fit the same durable candidate, the default suggestion should prefer:
    - `workflow_type`
    - `path_family`
    - `document_type`
    - `global`
  - the default should stay narrow because narrower scope is safer to review, easier to roll back, and less likely to leak an incidental preference into unrelated document work
  - broader suggested scope should be allowed only when:
    - the narrower candidate is missing, unstable, or poorly supported by trace
    - the same normalized signal already appears across at least two narrower contexts
    - the user explicitly confirms that broader reuse is intended
  - `proposed_scope` is only a review input; it must not be treated as an applied reviewed scope before `accept` or `edit`
- approval-backed save weighting policy:
  - without explicit confirmation, approval-backed save should remain supporting evidence only
  - it may strengthen a path-acceptability reading more than a content-quality reading, but it should not become an automatic promotion or auto-apply signal
- conflict principles:
  - current source-message `candidate_review_record` should decide only the review outcome for one candidate version
  - it should not choose future user-level memory scope by itself
  - reviewed memory should override unreviewed `durable_candidate` signals
  - narrower reviewed scope should override broader reviewed scope within the same category
  - unresolved same-scope conflicts should stay `deferred` or be `rejected`; they should not auto-promote
- rollback and disable principles:
  - item-level rollback or disable is required
  - scope-level disable is required for reviewed entries within one scope bucket
  - rollback should preserve the original candidate, review outcome, and artifact trace instead of deleting history
- without this surface, promotion from `durable_candidate` to future user-level memory would be too broad, hard to audit, and hard to reverse

#### 12. Evidence / Source Trace Linkage
- every artifact should retain a trace back to:
  - source document paths
  - original assistant message
  - evidence snapshot
  - summary chunk snapshot
  - reason records
  - review outcome and rollback status when present
  - related approval events when present
- because the current code stores evidence and summary chunks inline on messages, the minimum contract should preserve **artifact-level snapshots** rather than introducing a new normalized evidence store immediately

### Acceptance / Eval Placeholder

These are placeholders for the next phase, not current shipped acceptance gates.

#### 1. Did Correction Memory Improve The Next Response?
- compare whether a later artifact reuses the relevant `session_local` or `durable_candidate` signal and avoids the previous correction reason
- compare whether the user needs a smaller edit after the memory signal is applied

#### 2. Did The Same Mistake Decrease?
- track repeat counts of the same `reason_label` within the `correction` scope
- a useful memory layer should reduce repeated `factual_error`, `context_miss`, `awkward_tone`, or format-related corrections for the same user pattern
- do not mix correction counts with approval reject or reissue counts

#### 3. Was User Preference Reflected?
- the later artifact should match the stored preference candidate without requiring the same correction again
- explicit confirmation or repeated reuse should be visible before a candidate is treated as durable

#### 4. Was Review State Explicit?
- only reviewed entries should count as future reviewed candidates, and even those should remain separate from user-level memory until later scope/apply rules exist
- unreviewed `durable_candidate` items should remain proposal-only
- `accept`, `edit`, `reject`, and `defer` outcomes should remain distinguishable through source-message `candidate_review_record` traces

#### 5. Did Suggested Scope Stay Conservative?
- when multiple scope candidates fit the same durable candidate, the default proposal should prefer `workflow_type` before `path_family`, `document_type`, and `global`
- if a broader scope is suggested, the trace should preserve both `scope_candidates_considered` and `scope_suggestion_reason`
- a broader suggestion should remain reviewable and reversible rather than acting like an auto-applied scope

#### 6. Did Approval-Backed Save Stay Secondary?
- an approved save without explicit confirmation should remain distinguishable from an explicitly confirmed preference
- approval-backed save may support save-path acceptability more than content acceptability, but it should not be the sole reason for promotion review or broader scope suggestion
- content correction reuse and approval friction should remain separate evaluation axes even when they point to the same artifact

#### 7. Did Approval Friction Decrease Without Hiding Risk?
- track reject and reissue reasons separately from correction reasons
- a useful memory layer may reduce repeated `path_change`, `filename_preference`, or `directory_preference` events when a path pattern is already known

#### 8. Did Rollback Stop Future Application?
- after rollback or disable, later artifacts inside the same reviewed scope should stop applying that memory entry
- rollback should not erase the original candidate or the original review trace

#### 9. Did Conflict Resolution Stay Auditable?
- if conflicting candidates exist, the trace should preserve conflict ids, chosen reviewed scope, and losing or deferred items
- no conflicting reviewed entry should silently disappear from the local audit trail

#### 10. Did The Trace Stay Intact?
- for each artifact, the chain from artifact -> original response -> evidence/source snapshot -> reason record -> review outcome when present -> rollback when present -> approval trail when present -> corrected or accepted outcome should remain traversable
- if any link is missing, the artifact is not eval-ready

### Eval Fixture Family Baseline
- `GB-EVAL-CR-01 correction_reuse`
  - tests whether the same correction reason decreases when a similar user pattern reappears
- `GB-EVAL-AF-01 approval_friction`
  - tests whether reject or reissue friction decreases without hiding approval risk
- `GB-EVAL-RU-01 reviewed_unreviewed_trace`
  - tests whether reviewed and unreviewed candidates stay distinguishable
- `GB-EVAL-SC-01 scope_suggestion_safety`
  - tests whether conservative scope suggestion stays default and broader scope remains justified
- `GB-EVAL-RB-01 rollback_stop_apply`
  - tests whether rollback stops later application inside the same reviewed scope
- `GB-EVAL-CD-01 conflict_defer_trace`
  - tests whether conflicting or deferred candidates remain auditable
- `GB-EVAL-AS-01 explicit_vs_save_support`
  - tests whether explicit confirmation remains distinguishable from approval-backed save support

### First-Slice Verification Direction
- start with focused service and smoke coverage, not browser-e2e expansion
- first tests should verify:
  - a grounded-brief assistant message gets one stable `artifact_id`
  - the same `artifact_id` is preserved across approval request and approval outcome paths
  - write-note task-log events keep the same `artifact_id`
  - feedback-linked traces keep the same assistant-message linkage and log the resolved `artifact_id`
- because the slice is additive and should not change the visible UI contract, browser-e2e should stay deferred for this step

### Eval-Ready Artifact Trace Contract
- core chain required for any eval-ready artifact:
  - artifact record with `artifact_id`, `artifact_kind`, `session_id`, `assistant_message_id`, and `created_at`
  - original response snapshot with draft text, source paths, response origin, summary chunks, and evidence snapshot
  - evidence/source trace that can be tied back to the same assistant message or artifact snapshot
  - corrected or accepted outcome for the artifact
- if any core link above is missing, the artifact is not eval-ready for the workflow-grade fixture matrix
- family-specific trace extensions:
  - correction reuse requires a `correction`-scope reason record
  - approval friction requires an approval trail
  - reviewed-vs-unreviewed and scope-suggestion fixtures require a review record
  - rollback stop-apply requires a rollback record
  - conflict or defer fixtures require conflict ids or an equivalent defer / resolution trace
- explicit-vs-save-support fixtures require both `has_explicit_confirmation` and approval-support linkage when approval support exists

### Eval Axis Separation
- content-quality correction reuse
- approval friction reduction
- scope selection safety
- reviewability and rollbackability
- trace completeness
- approval-backed save may support the approval-friction axis, but it must not be counted as content-quality improvement
- future user-level memory remains outside the current gate and should appear only as a placeholder target inside these eval axes

### Data Assets To Accumulate Now
- source document references and evidence spans
- summary output and saved artifact output
- approval approved / rejected / reissued outcomes
- follow-up question and answer traces
- feedback labels and correction reasons
- future reject / reissue reasons with the same shared fields
- future grounded-brief correction pairs
- current promotion-review decisions for durable candidates through `accept`
- current source-message `candidate_review_record` traces before any reviewed-memory or user-level-memory store
- future reviewed scope selections
- future scope suggestions and broader-scope justifications
- future conflict-resolution and rollback traces
- future approval-backed save support traces kept distinct from explicit confirmation
- future eval-ready / not-eval-ready eligibility markers for fixture selection
- future fixture-family results and trace-completeness summaries
- future durable preference rules with scope and confidence

### Not Yet Specified
- the final durable user-memory schema
- exact recurrence thresholds by category when explicit confirmation is absent
- the exact UI for reviewing, promoting, editing, and rolling back durable candidates
- exact category-specific tuning beyond the baseline approval-backed-save weighting policy
- the exact boundary between service-level automation and later e2e coverage for each fixture family
- whether older sessions or pending approvals without `artifact_id` should ever be backfilled when reused
- whether any repository-specific workflow should let `path_family` outrank the default `workflow_type` suggestion
- the first operator surface after the memory phase

## Long-Term North Star

### Phase Definition

Long term, projectH aims to become a teachable local personal agent that can later expand from document work into constrained local tool or program operation under explicit approval.

### Why Program Operation Is Later
- Program operation has a higher safety requirement than document summarization and note saving.
- It needs action planning, approval UX, audit logs, rollback expectations, and operator boundaries that are not part of the current shipped contract.
- The product should first prove that it can remember the user's intent and style correctly before it expands into action.
- The first operator surface remains intentionally unspecified in this round.

### North-Star Properties
- local-first behavior
- durable preference and workflow memory
- approval-gated and auditable risky actions
- observable and reversible behavior
- vendor-neutral runtime seams

### Not Current Contract
- local app or desktop automation
- broad program control
- personalized local model training
- proprietary model layer

## Testing View

### Implemented
- unit and service regression through `python3 -m unittest -v`
- Playwright smoke coverage for:
  - file summary with evidence and summary range
  - browser file picker
  - browser folder picker search
  - approval reissue
  - approval-backed save
  - late flip after explicit original-draft save keeps saved history while latest content verdict changes
  - `내용 거절` content-verdict path with same-card reject-note update, approval preserved, and later explicit save supersession
  - corrected-save first bridge path
  - corrected-save saved snapshot remains while late reject and later re-correct move the latest state separately
  - candidate-linked explicit confirmation plus pending `검토 후보` `accept`, reviewed-but-not-applied queue removal, and later stale-clear
  - streaming cancel

### In Progress
- broader evaluation coverage for investigation-quality regressions

### Not Implemented
- dedicated benchmark/eval harness for the correction-memory phase

## Do Not Build Now

- generic web-chatbot positioning
- web-search-first product framing
- model learning described as already implemented
- approval-free local action
- cloud-first collaboration and account-heavy architecture
- autonomous background agents

## OPEN QUESTION

1. If `durable_candidate` later stops being source-message-anchored, should it keep reusing the current source-message candidate id or mint a new durable-scope id at that later boundary?
2. Which exact local-store, stale-resolution, and reviewed-memory preconditions should be required before any cross-session recurrence aggregation can open?
3. Which deterministic `rewrite_dimensions` are stable enough to expose in `explicit_pair_rewrite_delta_v1` without overclaiming semantic intent?
4. Should the default recurrence rule stay at two grounded briefs for every candidate category, or vary by category later?
5. Should the current fixed `confidence_marker = same_session_exact_key_match` remain enough until same-session unblock semantics can be satisfied truthfully, or should a later second conservative level be added only after that boundary opens?
6. Should the shipped `reviewed_memory_boundary_draft` keep repeating the fixed `reviewed_scope` label long term, or could a later normalization collapse it into `aggregate_identity_ref` plus supporting refs only?
7. Should later category-specific tuning vary approval-backed-save weight beyond the baseline weak-content / medium-path rule?
