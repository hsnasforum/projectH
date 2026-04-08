# Architecture

## Purpose

This repository implements a **local-first document assistant web MVP** with explicit approval for risky actions and transparent evidence handling.

## Current Contract Vs Next Design Target

### Current Contract
- current shipped behavior is the document-first MVP
- web investigation remains a secondary mode
- approval currently governs note saving only

### Next Design Target
- the next phase adds a correction / approval / preference memory layer around one official `grounded brief` artifact
- current rounds can still land small additive trace fields on the existing session/task-log surfaces, but no separate artifact store or new review UI is introduced here

## Layered Structure

### 1. App Layer
- `app/main.py`
- `app/web.py`
- `app/templates/index.html`

Responsibilities:
- local web shell / CLI entry
- request parsing
- session list and timeline rendering
- compact pending review queue rendering for eligible current `durable_candidate` items, plus one `accept`-only reviewed-but-not-applied action
- streaming progress and cancel
- approval card interactions
- session serialization for evidence, summary chunks, approval objects, and feedback

### 2. Core Layer
- `core/agent_loop.py`
- `core/request_intents.py`
- `core/web_claims.py`
- `core/source_policy.py`

Responsibilities:
- orchestration
- request mode and web-search intent classification
- approval gating and reissue approval flow
- evidence and summary-range selection
- active document context handling
- web investigation ranking, claim extraction, slot coverage, and reinvestigation

### 3. Tools Layer
- `tools/file_reader.py`
- `tools/file_search.py`
- `tools/write_note.py`
- `tools/web_search.py`

Responsibilities:
- local file read
- local document search
- approval-backed note writing
- permission-gated external web investigation

Design rule:
- tools are explicit, narrow, auditable, and local-first by default

### 4. Storage Layer
- `storage/session_store.py`
- `storage/task_log.py`
- `storage/web_search_store.py`

Responsibilities:
- JSON session persistence
- JSONL task log
- web search history and page previews

Current implementation note:
- `session_store` already persists `message_id`, optional artifact trace fields, normalized original-response snapshots, explicit `corrected_text`, minimum corrected-outcome records, content-linked `content_reason_record`, source-message `candidate_confirmation_record`, source-message `candidate_review_record`, minimum approval-linked reason records, `feedback`, `pending_approvals`, `permissions`, and `active_context`
- `app/web.py` now also computes one optional source-message-anchored read-only `candidate_recurrence_key` projection from the current explicit original-vs-corrected pair plus the matching current `session_local_candidate`; that projection is not persisted as a separate store
- `app/web.py` now computes one optional source-message-anchored read-only `durable_candidate` projection from the current serialized `session_local_candidate` plus a matching current `candidate_confirmation_record`; that projection is not persisted as a separate store
- `app/web.py` now also computes one optional top-level read-only `recurrence_aggregate_candidates` session projection from current same-session serialized source-message `candidate_recurrence_key` records when at least two distinct grounded-brief anchors share the same exact recurrence identity; that projection is not persisted as a separate store
- each current `recurrence_aggregate_candidates` item now also exposes deterministic read-only projections (`aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`, `reviewed_memory_transition_audit_contract`, `reviewed_memory_unblock_contract`, `reviewed_memory_capability_status`, `reviewed_memory_planning_target_ref`), one conditional `reviewed_memory_capability_basis` (present only when `capability_outcome = unblocked_all_required`), and lifecycle records: one conditional `reviewed_memory_transition_record` (emitted / applied / stopped / reversed) and one optional `reviewed_memory_conflict_visibility_record` (conflict_visibility_checked); none of these objects is persisted as a separate store
- `app/web.py` now also computes one top-level pending `review_queue_items` session projection from current serialized source-message `durable_candidate` records with `promotion_eligibility = eligible_for_review` and no matching current `candidate_review_record`; that projection is not persisted as a separate store
- `app/templates/index.html` now consumes current `recurrence_aggregate_candidates` as one separate aggregate-level `검토 메모 적용 후보` section adjacent to `검토 후보`; the `검토 메모 적용 시작` submit boundary is now enabled when `capability_outcome = unblocked_all_required` and the user has entered a non-empty reason note (visible but disabled while blocked or while the note is empty); clicking the enabled submit now emits one `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` and persists it under `reviewed_memory_emitted_transition_records`; after emission the same aggregate card shows `검토 메모 적용 실행`, and clicking that apply boundary POSTs to `/api/aggregate-transition-apply` which changes `record_stage` to `applied_pending_result` with `applied_at` added; after the apply boundary the card shows `결과 확정`, and clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply: after the effect is active the aggregate card shows `적용 중단`; clicking it changes `record_stage` to `stopped` and removes the effect; reversal: after stop the card shows `적용 되돌리기`; clicking it changes `record_stage` to `reversed`; conflict-visibility: after reversal the card shows `충돌 확인`; clicking it records a `reviewed_memory_conflict_visibility_record` with `record_stage = conflict_visibility_checked`
- `app/web.py` now also resolves one internal `boundary_source_ref` backer for the same exact aggregate, truthfully mints one exact payload-hidden canonical local proof-record/store entry for the current exact aggregate state inside one same-session internal `reviewed_memory_local_effect_presence_proof_record_store` boundary while keeping `first_seen_at` alone, source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay outside that lower proof-record layer, materializes one internal `reviewed_memory_local_effect_presence_proof_boundary` helper result only from that exact same-aggregate lower entry while reusing the same `applied_effect_id` and `present_locally_at`, materializes one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper result only from that exact same-aggregate proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`, materializes one internal `reviewed_memory_local_effect_presence_fact_source` helper result only from that exact same-aggregate fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`, materializes one internal `reviewed_memory_local_effect_presence_event` helper result only from that exact same-aggregate fact-source result while reusing the same `applied_effect_id` and `present_locally_at`, materializes one internal `reviewed_memory_local_effect_presence_event_producer` helper result only from that exact same-aggregate event result while reusing the same `applied_effect_id` and `present_locally_at`, materializes one internal `reviewed_memory_local_effect_presence_event_source` helper result only from that exact same-aggregate producer result while reusing the same `applied_effect_id` and `present_locally_at`, materializes one internal `reviewed_memory_local_effect_presence_record` helper result only from that exact same-aggregate event-source result while reusing the same `applied_effect_id` and `present_locally_at`, materializes one internal `reviewed_memory_applied_effect_target` helper result only from that exact same-aggregate source-consumer result while reusing the same `applied_effect_id` and `present_locally_at`, materializes one internal `reviewed_memory_reversible_effect_handle` helper result only from that exact same-aggregate shared target plus the current exact rollback contract, and resolves one internal `rollback_source_ref` only as one exact ref to that same handle; none of these helpers is a payload field or a `task_log` mirror
- current save-note approvals also carry one explicit `save_content_source = original_draft | corrected_text` plus `source_message_id`, and save-related assistant/system messages may mirror those same fields only on approval/write trace surfaces
- `task_log` already persists request, approval, write, feedback, minimum corrected-outcome events, content-verdict events, dedicated reject-note update events, candidate-confirmation events, candidate-review events, and minimum approval-linked reason records, with additive `artifact_id`, `source_message_id`, and `save_content_source` detail on grounded-brief save-related traces when applicable

### 5. Model Adapter Layer
- `model_adapter/base.py`
- `model_adapter/mock.py`
- `model_adapter/ollama.py`

Responsibilities:
- provider-swappable response generation
- summarization / context answer / note generation
- runtime status reporting

## Current Runtime Entry

Primary UX entry:
- `python3 -m app.web`
- default local address: `http://127.0.0.1:8765`

The web shell is the main MVP surface. CLI remains available as a narrower debug and development path.

## Current Request Flows

### A. File Summary
1. user chooses a local path or browser-picked file
2. file is read locally
3. summary is generated
4. evidence and summary-range panels are attached
5. save is optional and approval-gated

### B. Document Search
1. user provides search root or browser-picked folder
2. search returns selected sources
3. summary is generated from selected results
4. evidence and summary-range metadata are attached
5. save is optional and approval-gated

### C. Approval Save
1. response requests save
2. API returns `needs_approval` + `approval`
3. user can approve, reject, or reissue with a new path
4. write runs only after explicit approval

### D. Web Investigation
1. request is classified into `general`, `entity_card`, or `latest_update`
2. permission gate is checked
3. search results and page extracts are collected
4. claim extraction / slot coverage / reinvestigation may run
5. response renders source roles and claim coverage state
6. search history is stored locally

## Current Response Payload Contract

`app/serializers.py:_serialize_response` produces the top-level JSON object returned to the shell on every assistant response. The full field set is:

| Field | Type | Role |
|-------|------|------|
| `status` | string | response status — one of `answer`, `error`, `needs_approval`, `saved` (`core/contracts.py:ResponseStatus`) — shell control |
| `actions_taken` | list | actions taken during processing (default `[]`) — shell control |
| `requires_approval` | bool | `true` when save needs explicit approval — shell control |
| `proposed_note_path` | string \| null | proposed save path — shell control |
| `saved_note_path` | string \| null | actual saved path after approval — shell control |
| `web_search_record_path` | string \| null | local web-search history record path — shell control |
| `follow_up_suggestions` | list[string] | localized follow-up suggestions (default `[]`) — shell control |
| `search_results` | list[`{path, matched_on, snippet}`] | document search preview (default `[]`) — shell control |
| `artifact_id` | string \| null | stable artifact identifier |
| `artifact_kind` | string \| null | artifact type (e.g. `grounded_brief`) |
| `source_message_id` | string \| null | source message anchor for save trace |
| `text` | string | localized response text body |
| `note_preview` | string \| null | localized note preview for save request |
| `selected_source_paths` | list | selected source file paths (default `[]`) |
| `approval` | object \| null | serialized approval (see Approval Contract) |
| `active_context` | object \| null | follow-up context |
| `response_origin` | object \| null | `{provider, badge, label, model, kind, answer_mode, source_roles, verification_label}` when present; `null` on error paths |
| `applied_preferences` | list \| null | applied preference records |
| `evidence` | list | evidence/source items (reuses per-message shape; default `[]`) |
| `summary_chunks` | list | summary chunk items (reuses per-message shape; default `[]`) |
| `claim_coverage` | list | claim coverage slots (reuses per-message shape; default `[]`) |
| `claim_coverage_progress_summary` | string | localized reinvestigation summary (default `""`) |
| `original_response_snapshot` | object \| null | pre-correction snapshot |
| `corrected_outcome` | object \| null | correction outcome metadata |
| `approval_reason_record` | object \| null | reject or reissue reason record |
| `content_reason_record` | object \| null | explicit rejection reason record |
| `save_content_source` | string \| null | `original_draft` or `corrected_text` |

The eight control fields (`status`, `actions_taken`, `requires_approval`, `proposed_note_path`, `saved_note_path`, `web_search_record_path`, `follow_up_suggestions`, `search_results`) are directly consumed by `app/static/app.js` to drive approval UI, save confirmation, search preview, and follow-up rendering. Focused service tests (`tests/test_web_app.py`) and Python smoke tests (`tests/test_smoke.py`) lock these fields and their expected values. The same tests also lock correction/save field anchors including `original_response_snapshot`, `corrected_outcome`, `save_content_source`, `approval_reason_record`, and `content_reason_record`. Playwright browser smoke (`e2e/tests/web-smoke.spec.mjs`) covers the browser-visible contract separately.

Nested field shapes (evidence items, summary chunks, claim coverage slots, approval objects, response origin) are documented in their respective existing sections and are not duplicated here.

## Current Persistence Surfaces

### Session JSON

Current session JSON stores:
- `schema_version`
- `session_id`
- `title`
- `messages`
- `pending_approvals` — list of serialized approval objects (see Approval section for field shape)
- `permissions` — `{web_search, web_search_label}` where `web_search` is `disabled` / `approval` / `enabled` and `web_search_label` is `차단 · 읽기 전용 검색` / `승인 필요 · 읽기 전용 검색` / `허용 · 읽기 전용 검색`
- `active_context` — `{kind, label, source_paths, summary_hint, suggested_prompts, record_path, claim_coverage_progress_summary}`; updated by correction-submit `summary_hint`
- `created_at`
- `updated_at`

Current session payloads may also expose:
- computed top-level `recurrence_aggregate_candidates`
  - derived only from current same-session serialized grounded-brief source messages that already expose exact-match `candidate_recurrence_key`
  - emitted only when at least two distinct `artifact_id` + `source_message_id` anchors share the same exact recurrence identity
  - current items expose deterministic read-only projections (`aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`, `reviewed_memory_transition_audit_contract`, `reviewed_memory_unblock_contract`, `reviewed_memory_capability_status`, `reviewed_memory_planning_target_ref`), one conditional `reviewed_memory_capability_basis` (present only when `capability_outcome = unblocked_all_required`), and lifecycle records: one conditional `reviewed_memory_transition_record` (emitted / applied / stopped / reversed) and one optional `reviewed_memory_conflict_visibility_record` (conflict_visibility_checked)
  - not persisted as a separate session-store field
- computed top-level `review_queue_items`
  - derived from current `durable_candidate` items with `promotion_eligibility = eligible_for_review` and no matching current `candidate_review_record`
  - not persisted as a separate session-store field

Current message records include:
- `message_id`
- `role`
- `text`
- `created_at`
- optional response metadata such as:
  - `artifact_id`
  - `artifact_kind`
  - `response_origin` — `{provider, badge, label, model, kind, answer_mode, source_roles, verification_label}` when present; omitted from the session message when absent (unlike the top-level response payload, which returns `null`)
  - `evidence` — list of `{label, source_name, source_path, snippet, source_role}`
  - `summary_chunks` — list of `{chunk_id, chunk_index, total_chunks, source_path, source_name, selected_line}`
  - `claim_coverage` — list of slot objects, each containing `slot`, `status`, `status_label`, `value`, `support_count`, `candidate_count`, `source_role`, `rendered_as` (`fact_card` / `uncertain` / `not_rendered`); during reinvestigation, slots also carry `previous_status`, `previous_status_label`, `progress_state` (`improved` / `regressed` / `unchanged`), `progress_label`, and `is_focus_slot`
  - `claim_coverage_progress_summary` — plain-language Korean sentence summarizing the focus-slot reinvestigation outcome (empty string on first investigation)
  - `web_search_history` — list of recent search record summaries (up to 8), each containing `record_id`, `query`, `created_at`, `result_count`, `page_count`, `record_path`, `summary_head`, `answer_mode` (`entity_card` / `latest_update` / `general`), `verification_label`, `source_roles` (list of role strings), `claim_coverage_summary` (`strong` / `weak` / `missing` counts), and `pages_preview` (list of `{title, url, excerpt, text_preview, char_count}`)
  - `feedback`
  - `selected_source_paths`
  - `saved_note_path`
  - `note_preview`
  - approval metadata
- grounded-brief source message fields (owned by original source message only):
  - `original_response_snapshot` — `{artifact_id, artifact_kind, draft_text, source_paths, response_origin, summary_chunks_snapshot, evidence_snapshot}`; nested `response_origin` may be `null` when absent
  - `corrected_text`
  - `corrected_outcome`
  - `content_reason_record`
  - `save_content_source` — also present on save/approval trace messages
  - `source_message_id` — also present on save/approval trace messages
  - `session_local_memory_signal` — requires `original_response_snapshot`
  - `superseded_reject_signal` — requires source-message anchor and eligible `session_local_memory_signal` path
  - `historical_save_identity_signal` — requires source-message anchor and `session_local_memory_signal` with `save_signal`
  - `session_local_candidate` — requires same source-message anchor
  - `candidate_confirmation_record` — sibling of `session_local_candidate`
  - `candidate_recurrence_key` — sibling of `session_local_candidate`
  - `durable_candidate` — sibling of `session_local_candidate` + `candidate_confirmation_record`
  - `candidate_review_record` — resolves when `durable_candidate` join matches
- approval trace message fields:
  - `approval_reason_record` — owned by reject/reissue approval trace messages
  - `save_content_source` — also present on grounded-brief source messages after direct approved save
  - `source_message_id` — links back to the original source message

### Task Log

Current task log is append-only JSONL and already records actions such as:
- `request_received` — detail: `{user_text, source_path, search_root, search_query, save_summary, approved, approved_approval_id, rejected_approval_id, reissue_approval_id, corrected_save_message_id, note_path, retry_feedback_label, retry_feedback_reason, retry_target_message_id}`
- `request_cancelled` — detail: `{user_text, source_path, uploaded_file_name, search_root, search_query}`
- `document_context_updated` — detail: `{kind, label, source_paths}`
- `request_intent_classified` — detail: `{kind, query, score, reasons, freshness_risk, answer_mode, suggestion_kind, suggestion_query, suggestion_score, suggestion_reasons, suggestion_freshness_risk, suggestion_answer_mode}`
- `read_search_results` — detail: `{search_query, selected_match_count, selected_paths, selected_file_metadata}` where each file metadata entry is `{resolved_path, content_format, extraction_method, encoding_used}`
- `summarize_search_results` — detail: `{search_query, source_count}`
- `read_uploaded_file` — detail: `{requested_name, resolved_path, size_bytes, content_format, extraction_method, encoding_used}`
- `summarize_uploaded_file` — detail: `{source_name, title}`
- `read_file` — detail: `{requested_path, resolved_path, size_bytes, content_format, extraction_method, encoding_used}`
- `summarize_file` — detail: `{source_path, title}`
- `approval_requested` — detail: `{approval_id, artifact_id, source_message_id, note_path, overwrite, save_content_source}` plus optional `source_path` (file/source summary) or `search_query` + `source_paths` (search summary)
- `approval_granted` — detail: `{approval_id, kind, requested_path, overwrite, artifact_id, source_message_id, save_content_source}`
- `approval_rejected` — detail: `{approval_id, kind, requested_path, artifact_id, source_message_id, save_content_source, approval_reason_record}`
- `approval_reissued` — detail: `{old_approval_id, new_approval_id, old_requested_path, new_requested_path, overwrite, source_paths, artifact_id, source_message_id, save_content_source, approval_reason_record}`
- `write_note` — detail: `{artifact_id, source_message_id, note_path, save_content_source}` plus optional `approval_id`, `source_paths`, and optional `source_path` (file/source summary) or `search_query` (search summary)
- `response_feedback_recorded` — detail: `{message_id, artifact_id, artifact_kind, feedback_label, feedback_reason}`
- `correction_submitted` — detail: `{message_id, artifact_id, artifact_kind, source_message_id, corrected_text_length}`
- `corrected_outcome_recorded` — detail: `{outcome, recorded_at, artifact_id, source_message_id}` plus optional `approval_id`, `saved_note_path`, `corrected_text_length` (correction path), or `content_reason_record` (reject path); emitted from both feedback handler and save/write paths
- `content_verdict_recorded` — detail: `{message_id, artifact_id, artifact_kind, source_message_id, content_verdict, content_reason_record}`
- `content_reason_note_recorded` — detail: `{message_id, artifact_id, artifact_kind, source_message_id, reason_scope, reason_label, reason_note, content_reason_record}`
- `candidate_confirmation_recorded` — detail: `{message_id, artifact_id, source_message_id, candidate_id, candidate_family, candidate_updated_at, confirmation_scope, confirmation_label}`
- `candidate_review_recorded` — detail: `{message_id, artifact_id, source_message_id, candidate_id, candidate_family, candidate_updated_at, review_scope, review_action, review_status}`
- `stream_cancel_requested` — detail: `{request_id}`
- `web_search_permission_updated` — detail: `{web_search}`
- `permissions_updated` — detail: `{web_search}`
- `ocr_not_supported` — detail: `{source_path, error}`
- `web_search_record_loaded` — detail: `{query, record_id, record_path, result_count}`
- `web_search_retried` — detail: `{query, result_count, page_count, record_path, urls, search_queries, deprioritized_urls}` (shared web-search detail shape)
- `answer_with_active_context` — detail: `{label, source_paths, intent, conversation_mode, retrieved_chunk_count, selected_evidence_count, retry_feedback_label, retry_feedback_reason, retry_target_message_id}`
- `reviewed_memory_transition_emitted` — detail: `{canonical_transition_id, transition_action, aggregate_fingerprint, operator_reason_or_note, record_stage, emitted_at}`
- `reviewed_memory_transition_applied` — detail: `{canonical_transition_id, transition_action, aggregate_fingerprint, record_stage, applied_at}`
- `reviewed_memory_transition_result_confirmed` — detail: `{canonical_transition_id, aggregate_fingerprint, record_stage, applied_effect_kind, result_stage, result_at}`
- `reviewed_memory_transition_stopped` — detail: `{canonical_transition_id, aggregate_fingerprint, record_stage, stopped_at}`
- `reviewed_memory_transition_reversed` — detail: `{canonical_transition_id, aggregate_fingerprint, record_stage, reversed_at}`
- `reviewed_memory_conflict_visibility_checked` — detail: `{canonical_transition_id, transition_action, aggregate_fingerprint, source_apply_transition_ref, conflict_entry_count, record_stage, checked_at}`
- `agent_response` — detail: `{status, actions, requires_approval, proposed_note_path, saved_note_path, selected_source_paths, has_note_preview, approval_id, artifact_id, artifact_kind, source_message_id, save_content_source, approval_reason_record, active_context_label, evidence_count, summary_chunk_count}`
- `agent_error` — detail: `{error}`
- `session_deleted` — detail: `{}` (admin path)
- `all_sessions_deleted` — detail: `{count}` (admin path)
- `preference_activated` — detail: `{preference_id}` (system maintenance)
- `preference_paused` — detail: `{preference_id}` (system maintenance)
- `preference_rejected` — detail: `{preference_id}` (system maintenance)

## Approval Contract

Current approval object shape:
- `approval_id`
- `artifact_id` when linked to a grounded brief
- `source_message_id` when linked to a grounded-brief save trace
- `kind`
- `requested_path`
- `overwrite`
- `preview_markdown`
- `source_paths`
- `created_at`
- `save_content_source = original_draft | corrected_text` for the current shipped save-note path
- optional `approval_reason_record` on rejected or reissued approvals

Related request paths:
- `approved_approval_id`
- `rejected_approval_id`
- `reissue_approval_id`

## Next-Phase Memory Design Target

### Chosen Official Artifact

The next phase should standardize one `grounded brief` artifact.

### Why This Fits The Current Architecture
- `core/agent_loop.py` already builds one summary-first note body per document flow
- `app/web.py` already serializes the response-level evidence, summary chunks, feedback, approval preview, and saved note path together
- `storage/session_store.py` already persists the response message as the narrowest existing trace bundle
- `storage/task_log.py` already provides approval and feedback event history, and the first slice now links the grounded-brief save path back to the same artifact anchor

### Implemented Entry Slice: Artifact Trace Anchor

- the first implementation slice now lands one additive trace anchor, not a new review or memory surface
- that anchor is:
  - `artifact_id`
  - `artifact_kind = grounded_brief`
- the same anchor is currently reused across:
  - the assistant message in session storage
  - approval records and approval outcomes when present
  - append-only task-log details for approval, write, and feedback-related traces when present
- this is the smallest architecture cut because the current code already has:
  - one response-level message bundle
  - one approval flow
  - one append-only audit log

### Expected First Files
- `core/agent_loop.py`
- `core/approval.py`
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`

### Rollback-Friendly Implementation Order
1. add optional `artifact_id` and `artifact_kind` to grounded-brief assistant messages
2. thread the same `artifact_id` into approval request / outcome paths and write-note events
3. expose the same optional fields through response and session serialization, and log resolved `artifact_id` on feedback capture
4. normalize `original_response_snapshot` on the same grounded-brief message surface
5. add minimum `accepted_as_is` corrected-outcome capture on that same source message surface
6. add minimum reject / reissue `approval_reason_record` capture on approval-linked trace surfaces
7. add focused service and smoke regression before considering any UI changes

### Migration And Backward-Compat Risk
- this slice should stay additive
- current message normalization already tolerates optional extra keys
- pending approval records already persist dict payloads without a separate schema registry
- task-log detail is append-only JSONL and can accept additive fields
- the preferred first cut therefore avoids:
  - schema-version bump
  - destructive migration
  - new required UI fields

### Minimum Record Types

#### 1. Artifact Record
- base anchor implemented:
  - `artifact_id`
  - `artifact_kind = grounded_brief`
- conceptual-only separate record:
  - `session_id`
  - `assistant_message_id`
  - `source_paths`
  - `created_at`

#### 2. Original Response Snapshot
- implemented as a normalized companion object on original grounded-brief assistant messages:
  - `original_response_snapshot.artifact_id`
  - `original_response_snapshot.artifact_kind`
  - `original_response_snapshot.draft_text`
  - `original_response_snapshot.source_paths`
  - `original_response_snapshot.response_origin` — same shape as message-level `response_origin` (`{provider, badge, label, model, kind, answer_mode, source_roles, verification_label}`) or `null` when absent
  - `original_response_snapshot.summary_chunks_snapshot` — same shape as message-level `summary_chunks`
  - `original_response_snapshot.evidence_snapshot` — same shape as message-level `evidence`
- current source-of-truth layering:
  - the assistant message still holds the raw text, source paths, evidence, and summary chunks
  - `storage/session_store.py` derives or refreshes the normalized snapshot from those message fields for grounded-brief messages
  - `app/web.py` serializes the same snapshot contract and refreshes `response_origin` on that snapshot after the final response origin is known
- this keeps the snapshot on the existing message/session surface instead of introducing a separate artifact store in the same round

#### 3. Approval Trail
- one artifact may have multiple approval events
- each event should keep:
  - `approval_id`
  - outcome
  - requested path
  - overwrite flag
  - timestamps
- reject / reissue events may now also keep:
  - nested `approval_reason_record`
  - `reason_scope`
  - `reason_label`
  - optional `reason_note`
  - `artifact_id`
  - `artifact_kind`
  - `source_message_id`
  - `approval_id`
- source-of-truth layering:
  - original grounded-brief assistant messages remain the content/source surface
  - assistant system messages created by reject / reissue persist the approval-linked reason trace in session JSON
  - reissued pending approvals keep the same record as a convenience copy on the live approval surface
  - task-log entries mirror the same record for audit

#### 4. Corrected Outcome
- implemented minimum record now:
  - `outcome = accepted_as_is | corrected | rejected`
  - `recorded_at`
  - `artifact_id`
  - `source_message_id`
  - optional `approval_id`
  - optional `saved_note_path`
- explicit correction submit also persists:
  - `corrected_text`
- current source-of-truth layering:
  - the original grounded-brief assistant message keeps the corrected-outcome record on the same message that already owns `artifact_id` and `original_response_snapshot`
  - when the user explicitly submits edited text, that same message also stores `corrected_text`
  - when the user explicitly clicks `내용 거절`, that same message also stores one `content_reason_record`
  - correction-submit responses and session serialization expose the updated `corrected_text` and `corrected_outcome` from that same source message
  - explicit reject responses and session serialization expose `corrected_outcome = rejected` plus `content_reason_record` from that same source message
  - an existing pending approval keeps the `note_text` / preview snapshot that was captured when the approval was first requested
  - approval-execute system responses do not duplicate that record
  - task-log events keep linkage-oriented audit detail instead of copying the full corrected-outcome blob
- still later:
  - a possible manual reject-note clear refinement if it stays note-only and does not blur verdict semantics
  - richer corrected / rejected reason metadata
- truthful current layering:
  - `corrected` is persisted only from an explicit content-correction submit action that carries actual edited text
  - the shipped UI surface is one multiline correction editor on the grounded-brief response, seeded with the current draft text
  - unchanged submits fail validation and must not create a synthetic content outcome
  - save approval remains separate and current pending approval previews do not auto-rebase onto `corrected_text`
  - correction submit never mutates an already-issued approval object
  - `rejected` is persisted only from one explicit content-verdict action on that grounded-brief response surface
- truthful current layering:
  - recommended reconciliation policy remains `Option B`
  - the response card content-edit area now exposes a distinct corrected-save bridge action such as `이 수정본으로 저장 요청`
  - that bridge action stays visible even before a correction is recorded, but it must remain disabled with helper copy until recorded `corrected_text` exists
  - that bridge action stays separate from both `수정본 기록` and the later approval controls
  - the bridge action reads the latest recorded `corrected_text` from the source message; it does not silently bridge unsaved editor state
  - if the editor diverges from the last recorded correction, the response-card helper copy should explain that the bridge action still targets the recorded correction until another explicit submit updates it
  - that approval object snapshots the corrected text into its own preview / `note_text` at request time
  - approval-card and corrected-save save-result wording should describe that body as a request-time frozen snapshot so later source-message edits are not mistaken for automatic approval rebasing
  - the approval object, approval-request audit detail, approval-granted audit detail, and write-note detail all expose the same explicit save-target discriminator, i.e. `save_content_source = corrected_text`
  - the same corrected-save trace also carries `source_message_id` because the corrected text still lives on the original grounded-brief source message
  - `approval_id` acts as the immutable approval-snapshot identity in the first corrected-save slice; do not add a separate `snapshot_id` unless approval records stop storing the frozen body snapshot
  - corrected-save approval execution keeps the source message as the content surface, so `corrected_outcome.outcome` remains `corrected` while optional `approval_id` / `saved_note_path` linkage is added there
  - `rejected` is now persisted only from the distinct content-verdict action `내용 거절` on that same grounded-brief response surface
  - that action stays separate from `수정본 기록`, corrected-save bridge, and approval-surface approve / reject / reissue controls
  - that action records verdict immediately on the content trace path rather than creating or cancelling an approval
  - the same source message now carries `content_reason_record` with:
    - `reason_scope = content_reject`
    - `reason_label = explicit_content_rejection`
    - `recorded_at`, `artifact_id`, `artifact_kind`, `source_message_id`
    - optional `reason_note`
  - fixed-label baseline remains truthful even with no note:
    - `내용 거절` still records `explicit_content_rejection` immediately
    - any later reject note only supplements that baseline
  - the current shipped optional reject-note surface:
    - stays inside the same response-card content-verdict box
    - appears only while the latest outcome on that same source message is still `rejected`
    - uses one short inline textarea plus one explicit secondary note-submit action
    - stays separate from the correction editor, corrected-save bridge, and approval controls
    - keeps blank-note submit disabled in the shipped slice and must not reinterpret blank submit as note clear
  - recording that optional note updates the existing `content_reason_record` on the same source message in place:
    - `reason_note` is added or replaced there
    - `content_reason_record.recorded_at` refreshes to the latest note-update time
    - `corrected_outcome.recorded_at` continues to mark when the reject verdict itself was recorded
  - deferred manual clear contract:
    - current MVP recommendation remains `Option B`: keep the shipped disabled-blank-submit behavior and do not add a second reject-note micro-action yet
    - if a later refinement introduces manual clear, it should stay in the same response-card content-verdict box as one tiny secondary affordance that appears only while a non-empty note already exists
    - that future clear should remove only `content_reason_record.reason_note`; it must not revoke `corrected_outcome.outcome = rejected` or the fixed-label `explicit_content_rejection` baseline
    - the same `content_reason_record` should remain on the source message with its scope / label / anchor fields intact while only the optional note field is removed
    - `content_reason_record.recorded_at` should refresh to the clear time while `corrected_outcome.recorded_at` continues to identify the original reject-verdict time
  - if the same source message later receives an explicit correction submit, explicit original-draft save, or corrected-save approval, the latest `corrected_outcome` on that source message may move away from `rejected` and the stale `content_reason_record` including any `reason_note` should clear with it
  - task-log history preserves the note audit separately through the dedicated content-linked event `content_reason_note_recorded` rather than overloading approval-reject trace
  - if a future manual clear lands, task-log history should preserve that note removal through a second content-linked event such as `content_reason_note_cleared` rather than replaying either verdict or approval-friction events
  - approval reject, save omission, retry, and feedback `incorrect` remain separate signals and must not be normalized into `rejected`
  - if an explicit original-draft save already produced a saved note, a later `내용 거절` still changes only the latest content verdict on that source-message trace; the saved file body and saved path remain as prior explicit-save history and are not rewritten automatically
  - if a corrected-save already produced a saved note, later `내용 거절` or a later explicit correction submit still move only the latest source-message verdict / corrected text; the saved corrected snapshot body and saved path remain prior explicit-save history until a new explicit save is approved
- recommended next refinement order:
  - keep the shipped optional reject-note surface small and stable, and keep manual clear deferred until a real operator need outweighs the extra micro-action
  - keep the shipped `corrected` and `rejected` surfaces narrow because they produce explicit content artifacts closest to document productivity
  - reconcile corrected-save through one explicit bridge action rather than silently rebasing the approval preview
  - keep richer reject taxonomy for a later slice

#### 5. Shared Reason Envelope
- minimum conceptual fields:
  - `reason_scope = correction | content_reject | approval_reject | approval_reissue`
  - `reason_label`
  - `reason_note`
- `storage/session_store.py` already normalizes correction reasons through `feedback.reason`
- approval reject and reissue reasons should use distinct label sets rather than reusing correction labels
- current implemented minimum labels stay intentionally narrow until a truthful reason-input surface exists:
  - `approval_reject -> explicit_rejection`
  - `approval_reissue -> path_change`
- the current first content-level reject label stays equally narrow:
  - `content_reject -> explicit_content_rejection`
  - `reason_note` remains optional and can stay absent, or be recorded only through the same response-card note surface
- content-level `rejected` reasons should live under the content-outcome path on the original grounded-brief source message, not under approval-linked reason traces
- this keeps the current feedback flow close to implementation while leaving room for later review surfaces

#### 6. First Session-Local Memory Signal
- the first `session_local` memory signal should be a **read-only projection**, not a new source-of-truth record
- it should summarize explicit user-authored state around one grounded-brief artifact inside the current session
- it should not be described as:
  - learned preference memory
  - durable candidate review input
  - user-level memory
  - training-ready personalization artifact
- the canonical anchor should stay:
  - one original grounded-brief source message
  - one `artifact_id`
  - one `source_message_id`
- the signal should keep three separate axes instead of collapsing approval friction, content verdict, and save history into one label:
  - `content_signal`
  - `approval_signal`
  - `save_signal`
- canonical input locations for that first signal should stay inside the current persisted session state:
  - source message fields for the content axis:
    - `original_response_snapshot`
    - `corrected_text`
    - `corrected_outcome`
    - `content_reason_record`
  - approval-linked session messages and pending approvals for the approval-friction axis:
    - `approval_reason_record`
    - `approval_id`
    - `source_message_id`
    - `artifact_id`
  - saved response messages plus source-message save linkage for the save axis:
    - `save_content_source`
    - `saved_note_path`
    - optional `approval_id`
- task-log replay should remain audit-only in the first slice:
  - task log may confirm or replay historical events later
  - it should not be the canonical source for the first signal projection
- current truthful limitation:
  - if later explicit correction submit or explicit save clears `rejected` from the source message, the superseded reject or reject-note may disappear from the first signal while still remaining in task-log audit
- current implementation:
  - `storage/session_store.py` now computes one optional `session_local_memory_signal` from the current normalized session object without adding a separate memory store
  - `app/web.py` now attaches that read-only projection only to serialized grounded-brief source messages
  - the projection currently resolves:
    - `content_signal` from the source message itself
    - `approval_signal` from matching approval-linked session messages and pending approvals
    - `save_signal` from matching saved response messages plus any still-visible save linkage on the source message
  - because the first slice stays current-state-only, fields such as stale reject-note or an old save approval ID may fall out once later explicit actions clear them from the current session state
  - `app/web.py` now also attaches one optional `superseded_reject_signal` only on serialized grounded-brief source messages
  - that helper remains source-message-anchored and historical:
    - it reads only same-anchor content-side audit traces needed to restore the latest superseded reject + optional reject-note
    - it stays absent while the current `content_signal` still shows `rejected`
    - it never merges its replayed state back into `content_signal`
    - it selects at most one latest superseded reject entry in the first slice rather than building a mini-history list
    - it omits a replayed note when same-anchor note association is ambiguous
  - task-log replay remains helper-only:
    - it should not scan task-log as a new canonical state store
    - it should not reconstruct approval/save history into that helper
  - save-axis gaps such as later `latest_approval_id` loss remain separate from the content-side replay helper
  - `app/web.py` now also attaches one optional `historical_save_identity_signal` to the same grounded-brief source-message serialization
  - that adjunct stays historical and narrow:
    - it should not overwrite `save_signal`
    - it should replay at most one latest approval-backed save identity for the same anchor
    - it should stay absent while the current `save_signal` still exposes `latest_approval_id`
    - it should read same-anchor save audit traces only as needed to restore:
      - optional `approval_id`
      - optional `save_content_source`
      - optional `saved_note_path`
      - optional `recorded_at`
    - the first shipped slice uses `write_note` audit with non-empty `approval_id` rather than `approval_granted` because the helper is meant to replay persisted save identity, not granted-but-not-written approval state
    - the current MVP should keep that `write_note`-only rule as the default replay boundary until a concrete insufficiency appears
    - if a later refinement adds `approval_granted`, it should remain corroboration-only:
      - it should require the same anchor and the same `approval_id` as an already-selected `write_note` candidate
      - it should not create the adjunct when `approval_granted` exists without a matching persisted `write_note`
      - it should not reopen pending-approval replay or a broader save-history surface
    - it should suppress itself when the current `save_signal` linkage and the replay candidate disagree on save source or saved path
    - it should not replay saved body text, approval preview text, content verdict state, or approval-friction labels
  - task-log still must not become the canonical current-state store:
    - current `save_signal` remains the current-state summary
    - the adjunct remains a helper-only historical identity replay

#### 7. First Normalized `session_local_candidate`
- the shipped layer above the source-message signal/adjunct set is now one normalized `session_local_candidate`
- that unit should still remain local-first and lightweight:
  - it is not a new canonical store in the first contract
  - it is not a durable candidate yet
  - it is not reviewed memory
- the candidate should consume one or more shipped source-message projections rather than skipping directly from raw task-log events
- the minimum envelope should now include:
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
- the candidate should not simply reuse `session_local_memory_signal` because:
  - the shipped signal is still current-state-only and source-message-scoped
  - the shipped signal may drop superseded state after later explicit actions
  - the shipped signal has no normalized reusable statement or evidence-strength field
- the first candidate family should stay narrow and correction-led:
  - `candidate_family = correction_rewrite_preference`
  - primary basis should be the explicit `original_response_snapshot.draft_text` -> `corrected_text` pair on the same source message
  - the shipped first statement is `explicit rewrite correction recorded for this grounded brief`
  - the normalized statement should describe the reusable rewrite preference signal, not embed the full corrected body as candidate state
- the first extraction rule stays conservative:
  - one eligible corrected pair may emit one `session_local_candidate` draft
  - the shipped first candidate currently references only current-state signal support:
    - `session_local_memory_signal.content_signal` as primary basis
    - `session_local_memory_signal.save_signal` only when the same current anchor still exposes `latest_approval_id`
  - replay helpers remain supporting-context-only follow-up territory:
    - `superseded_reject_signal` should not become a primary extraction source
    - `historical_save_identity_signal` should not become a primary extraction source
    - the current shipped candidate does not reference those historical adjuncts yet
  - approval-backed save should remain supporting evidence only:
    - it may strengthen the same candidate only when the same current anchor still carries approval-backed save support
    - it should not be the sole basis for extraction
    - it should not widen scope or act like explicit confirmation
- the first evidence-strength policy should stay factual rather than speculative:
  - `explicit_single_artifact`
  - current save support may add `session_local_memory_signal.save_signal` to `supporting_signal_refs`, but it does not change `evidence_strength` in the first slice
  - future stronger levels remain out of the first slice
- the shipped source-message sibling trace above that candidate is now one optional `candidate_confirmation_record`
- that trace stays separate from the candidate itself:
  - it records one positive reuse confirmation for the current source-message candidate only
  - it keeps `candidate_id`, `candidate_family`, `candidate_updated_at`, `artifact_id`, `source_message_id`, `confirmation_scope`, `confirmation_label`, and `recorded_at`
  - it does not rewrite `supporting_signal_refs` or `evidence_strength`
  - it does not add `has_explicit_confirmation`, `promotion_basis`, or `promotion_eligibility` onto `session_local_candidate`
- the current shipped response-card surface for that trace stays narrow:
  - one small action such as `이 수정 방향 재사용 확인`
  - shown only when the current source message already emits `session_local_candidate`
  - separate from correction submit, corrected-save request, content verdict, reject-note, and approval controls
- current-state boundary:
  - approval-backed save still remains supporting evidence only and does not create the confirmation trace
  - later explicit correction submit or non-`corrected` outcome clears stale `candidate_confirmation_record` from current session state on that source message
  - append-only audit keeps the separate task-log event `candidate_confirmation_recorded`
- repeated same-session drafts should currently remain attached to their source-message candidates:
  - the shipped candidate envelope does not yet carry a truthful same-preference merge key beyond family alone
  - the fixed statement and current support refs are therefore insufficient to justify a session-level merge helper now
- if a later reopen is needed, the smallest architecture target should be:
  - one optional top-level session projection such as `session_candidate_family_signal`
  - read-only and session-local
  - derived from already-computed source-message `session_local_candidate` drafts rather than raw task-log replay
  - absent unless at least two distinct source-message candidates in the same session share the same future merge key derived from the explicit corrected pair itself
  - separate from source-message candidates and separate from future `durable_candidate`
  - kept out of array/feed history shapes in the first reopen slice

### Minimum Promotion Guardrail

- current shipped `session_local_candidate` drafts remain promotion-ineligible in their own object shape:
  - `session_local_candidate` itself still does not emit `has_explicit_confirmation`, `promotion_basis`, or `promotion_eligibility`
  - the same serialized grounded-brief source message may now emit one separate sibling `durable_candidate`
- the current architecture now opens only the smallest explicit-confirmation promotion path:
  - one current source message must still expose both:
    - a valid `session_local_candidate`
    - a matching `candidate_confirmation_record`
  - repeated-signal promotion remains blocked until a later recurrence key derived from the explicit corrected pair itself exists
- approval-backed save and historical adjuncts stay outside the primary gate:
  - approval-backed save may remain supporting evidence only
  - `superseded_reject_signal` and `historical_save_identity_signal` remain supporting context only
  - task-log replay alone must not become a promotion basis
- the current projection surface stays source-message-anchored:
  - one optional computed `durable_candidate` on serialized grounded-brief source messages only
  - canonical source = current persisted session state on that same source message plus sibling `session_local_candidate` and `candidate_confirmation_record`
  - the join rule stays exact on `artifact_id`, `source_message_id`, `candidate_id`, and `candidate_updated_at`
  - stale or ambiguous confirmation matches omit the current confirmation serialization and therefore also omit `durable_candidate`
  - task-log remains audit-only and must not become the canonical projection source
  - current read-only review-queue items now consume that projection; they do not invent it first
- the current shipped `durable_candidate` record stays separate from `session_local_candidate` and includes only:
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
- first explicit-confirmation projection path stays minimal:
  - reuse the consumed source-message `session_local_candidate` values for `candidate_family`, `statement`, `supporting_artifact_ids`, `supporting_source_message_ids`, `supporting_signal_refs`, and `evidence_strength`
  - add one `supporting_confirmation_refs` item from the matching `candidate_confirmation_record`
  - reuse the source-message `session_local_candidate.candidate_id` while the projection stays source-message-anchored
  - set `has_explicit_confirmation = true`
  - set `promotion_basis = explicit_confirmation`
  - set `promotion_eligibility = eligible_for_review`
  - set `created_at` / `updated_at` from `candidate_confirmation_record.recorded_at`
- keep the first guardrail narrower than the later review layer:
  - no suggested scope fields at the promotion step
  - no review queue semantics beyond `promotion_eligibility = eligible_for_review`
  - no automatic promotion to user-level memory
- current practical next path:
  - keep the shipped read-only review queue consuming those `durable_candidate` records without opening any apply / rollback or user-level-memory layer yet
  - repeated-signal promotion remains blocked until a truthful recurrence key exists beyond family alone

### First Truthful Recurrence-Key Contract

- the first truthful recurrence key is now implemented as one source-message-anchored read-only `candidate_recurrence_key` draft and should stay smaller than repeated-signal promotion itself
- that key should identify one deterministic rewrite-transformation class for `correction_rewrite_preference`, not a broad semantic preference label
- the key must be derived only from the explicit original-vs-corrected pair already recoverable on the same grounded-brief source message:
  - `original_response_snapshot.draft_text`
  - explicit `corrected_text`
  - current source-message `candidate_family`
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
- the identity-bearing part should stay narrow:
  - `candidate_family`
  - `key_version`
  - `normalized_delta_fingerprint`
- `candidate_family` alone is still insufficient:
  - it identifies only the family bucket
  - it does not identify which rewrite transformation repeated
- the current fixed statement is still insufficient:
  - it records that one explicit rewrite happened
  - it does not identify the recurring rewrite direction
- allowed versus forbidden basis must remain explicit:
  - allowed basis:
    - the explicit original-vs-corrected pair
    - later explicit reviewed-but-not-applied trace only as strengthening evidence after the key exists
    - same candidate family only together with the stricter recurrence key
  - supporting context only:
    - `session_local_memory_signal`
    - `superseded_reject_signal`
    - `historical_save_identity_signal`
    - approval-backed save support
  - never basis:
    - `candidate_family` alone
    - fixed statement text alone
    - queue presence alone
    - `candidate_review_record` alone
    - task-log replay alone
    - approval-backed save alone
    - historical adjunct alone
- the future architecture boundary should stay source-message-first:
  - each grounded-brief source message may expose one optional sibling `candidate_recurrence_key`
  - canonical source remains current persisted session state, not task-log replay
  - the key remains tied to one current source-message candidate version through `source_candidate_id` and `source_candidate_updated_at`
  - if a later correction changes the current pair and candidate version, the old key must not bind to the new candidate version
- the first repeated-signal threshold should stay conservative:
  - at least two distinct grounded briefs must expose the same recurrence key before repeated-signal promotion may even be considered
  - distinctness is anchored by different `artifact_id` + `source_message_id`
  - repeated edits on one source message do not count as multi-brief recurrence
  - two is the first truthful baseline for the current family, not a permanent rule for every later family
- the first post-key aggregation boundary is now implemented as one current session-level read-only `recurrence_aggregate_candidates` projection:
  - same-session only:
    - derive only from current session serialization
    - keep the first aggregate boundary local-first and auditable without adding a second canonical store
    - keep cross-session counting closed until explicit local-store, rollback, conflict, and reviewed-memory contracts exist
  - one aggregate identity should require the same:
    - `candidate_family`
    - `key_scope`
    - `key_version`
    - `derivation_source`
    - `normalized_delta_fingerprint`
  - `source_candidate_id` and `source_candidate_updated_at` remain version refs only:
    - they keep the aggregate tied to current source-message candidate versions
    - they do not become the aggregate identity
  - the current aggregate envelope stays additive and read-only:
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
  - current `candidate_review_record` may support trace confidence only when it still matches the same current source-message candidate version
  - current `durable_candidate` remains supporting context only and is not repackaged as a separate aggregate-ref list in this slice
  - approval-backed save, `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, queue presence, fixed statement text, `candidate_family` alone, and task-log replay alone must stay outside aggregate identity
  - the first aggregate surface must not overwrite source-message `candidate_recurrence_key`, must not reuse `review_queue_items`, and must not imply repeated-signal promotion by itself
- the first post-aggregate promotion boundary should stay smaller than repeated-signal promotion itself:
  - choose `Option A` for the current MVP:
    - every current same-session `recurrence_aggregate_candidates` item stays promotion-ineligible
    - aggregate identity is necessary but still insufficient for promotion
  - current source-message traces remain separate from any later reviewed-memory layer:
    - `durable_candidate` remains one source-message explicit-confirmation projection
    - `candidate_review_record` remains one source-message reviewed-but-not-applied trace
    - `recurrence_aggregate_candidates` remains one same-session cross-source grouping projection
    - reviewed memory remains a later rollbackable, disableable, conflict-visible, operator-auditable layer above those current surfaces
  - valid future promotion inputs remain narrow:
    - exact same-session aggregate identity from current `recurrence_aggregate_candidates`
    - distinct grounded-brief anchors only
    - current `durable_candidate` only when it still matches the same source-message candidate version
    - current `candidate_review_record` only as confidence support when it still matches the same source-message candidate version
  - never treat review acceptance, approval-backed save, historical adjuncts, queue presence, fixed statement text, `candidate_family` alone, or task-log replay as promotion identity
  - current architecture now emits one aggregate-level blocked marker only inside each current aggregate item:
    - `aggregate_promotion_marker`
    - `promotion_basis = same_session_exact_recurrence_aggregate`
    - `promotion_eligibility = blocked_pending_reviewed_memory_boundary`
    - `reviewed_memory_boundary = not_open`
    - `marker_version = same_session_blocked_reviewed_memory_v1`
    - `derived_at = last_seen_at`
  - current architecture now also emits one blocked-only aggregate-level precondition status object:
    - `reviewed_memory_precondition_status`
    - `status_version = same_session_reviewed_memory_preconditions_v1`
    - `overall_status = blocked_all_required`
    - `all_required = true`
    - ordered `preconditions`
    - `evaluated_at = last_seen_at`
  - current architecture now also emits one read-only aggregate-level boundary draft object:
    - `reviewed_memory_boundary_draft`
    - `boundary_version = fixed_narrow_reviewed_scope_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - `supporting_source_message_refs`
    - `supporting_candidate_refs`
    - optional `supporting_review_refs`
    - `boundary_stage = draft_not_applied`
    - `drafted_at = last_seen_at`
  - current architecture now also emits one read-only aggregate-level rollback-contract object:
    - `reviewed_memory_rollback_contract`
    - `rollback_version = first_reviewed_memory_effect_reversal_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - `supporting_source_message_refs`
    - `supporting_candidate_refs`
    - optional `supporting_review_refs`
    - `rollback_target_kind = future_applied_reviewed_memory_effect_only`
    - `rollback_stage = contract_only_not_applied`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - `defined_at = last_seen_at`
  - current architecture now also emits one read-only aggregate-level disable-contract object:
    - `reviewed_memory_disable_contract`
    - `disable_version = first_reviewed_memory_effect_stop_apply_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - `supporting_source_message_refs`
    - `supporting_candidate_refs`
    - optional `supporting_review_refs`
    - `disable_target_kind = future_applied_reviewed_memory_effect_only`
    - `disable_stage = contract_only_not_applied`
    - `effect_behavior = stop_apply_without_reversal`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - `defined_at = last_seen_at`
  - the current blocked marker remains correct because the reviewed-memory precondition family gates the unblock path; the reviewed-memory apply path is now shipped above this precondition layer:
    - `reviewed_memory_boundary_defined`
      - future reviewed memory must have a separate local persistence/apply boundary and one fixed narrow reviewed scope above source-message and aggregate projections
      - the first reviewed scope should stay fixed at `same_session_exact_recurrence_aggregate_only`
      - that scope should be tied to one current aggregate identity plus its exact current supporting refs
      - this is not source-message history, not `candidate_review_record`, not `recurrence_aggregate_candidates`, and not user-level memory
    - `rollback_ready_reviewed_memory_effect`
      - reviewed-memory effect must be reversible without mutating source-message records or aggregate identity
      - the rollback target stays fixed at one applied reviewed-memory effect inside `same_session_exact_recurrence_aggregate_only`
      - the shipped `reviewed_memory_boundary_draft` remains the scope draft and basis reference, not the rollback target itself
      - rollback means explicit local reversal of applied influence, not rewinding `corrected_text`, deleting `candidate_review_record`, deleting `candidate_recurrence_key`, or rewriting aggregate history
      - after rollback, aggregate identity, supporting refs, the current boundary draft, and operator-visible rollback trace must remain while only the applied effect deactivates
    - `disable_ready_reviewed_memory_effect`
      - reviewed-memory effect must support explicit local stop-apply without deleting candidate traces, aggregate evidence, the current boundary draft, or the current rollback contract
      - the disable target stays fixed at one applied reviewed-memory effect inside `same_session_exact_recurrence_aggregate_only`
      - disable means influence stop without claiming reversal of the already-applied effect
      - this is not candidate deletion, not review reject, and not rollback of source-message correction history
      - after disable, aggregate identity, supporting refs, the current boundary draft, the current rollback contract, and operator-visible disable trace must remain while only the applied effect becomes inactive
    - `conflict_visible_reviewed_memory_scope`
      - reviewed-memory layer must keep competing reviewed-memory targets visible inside one reviewed scope
      - the first conflict-visible scope should stay fixed at `same_session_exact_recurrence_aggregate_only`
      - the first conflict categories should stay fixed and narrow:
        - `future_reviewed_memory_candidate_draft_vs_applied_effect`
        - `future_applied_reviewed_memory_effect_vs_applied_effect`
      - this is not a source-message `corrected_text` diff surface, not promotion of `candidate_review_record` into a conflict object, and not aggregate-identity rewrite
      - conflict visibility remains read-only only:
        - no auto-resolve
        - no auto-disable
        - no auto-rollback
        - no auto-apply
    - `operator_auditable_reviewed_memory_transition`
      - any later reviewed-memory transition above the blocked marker must leave one explicit operator-visible local trace with canonical transition identity
      - the first transition action vocabulary should stay fixed and narrow:
        - `future_reviewed_memory_apply`
        - `future_reviewed_memory_stop_apply`
        - `future_reviewed_memory_reversal`
        - `future_reviewed_memory_conflict_visibility`
      - operator trace must keep reviewed scope, aggregate identity, exact basis refs, transition timing, and explicit local reason or note boundary visible
      - this is not source-message trace reuse, not aggregate rewrite, and not promotion of boundary / rollback / disable / conflict contracts into transition results
      - append-only `task_log` may mirror that trace, but it is not the canonical reviewed-memory transition surface
      - approval-backed save support, historical adjuncts, review acceptance, queue presence, and task-log replay alone must not create canonical transition state
  - current shipped contract objects still mean only `contract exists`:
    - the shipped boundary / rollback / disable / conflict / transition-audit objects do not satisfy their own preconditions
    - approval-backed save support, historical adjuncts, review acceptance, queue presence, and `task_log` mirror existence remain outside satisfaction basis
  - all required preconditions must be satisfied before aggregate promotion vocabulary can widen:
    - the first same-session unblock threshold stays binary:
      - current shipped `reviewed_memory_unblock_contract.unblock_status = blocked_all_required`
      - current shipped `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`
    - partial satisfaction may later surface read-only only, but remains blocked in this phase
    - partial satisfaction must not create reviewed-memory apply, repeated-signal promotion, or cross-session counting
    - current architecture does not yet report per-precondition satisfied / unsatisfied booleans
  - the first unblocked target remains planning-only:
    - the current `reviewed_memory_planning_target_ref.target_label = eligible_for_reviewed_memory_draft_planning_only` remains the right narrow label
    - it means one exact same-session aggregate may enter reviewed-memory draft planning only
    - it does not mean emitted transition record or reviewed-memory apply already exists
    - the current aggregate item now also emits one additive shared planning-target ref:
      - `reviewed_memory_planning_target_ref`
      - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
      - `target_label = eligible_for_reviewed_memory_draft_planning_only`
      - `target_scope = same_session_exact_recurrence_aggregate_only`
      - `target_boundary = reviewed_memory_draft_planning_only`
      - `defined_at = last_seen_at`
    - the shipped additive ref is now the canonical planning-target source for aggregate payloads
    - the first cleanup contract now stays structural-only:
      - the one compatibility release window is now complete
      - the current shipped payload removes all three duplicated target echo fields together
      - docs, payload, and tests now read planning-target meaning only from `reviewed_memory_planning_target_ref`
      - do not normalize only one field back into a fallback string
      - do not drop only one or two duplicated fields in any reopening
      - do not let cleanup hide readiness, emitted-transition, or apply widening
  - the shipped boundary draft remains smaller than store/apply:
    - current architecture does not yet widen the draft into readiness, apply, or cross-session scope
  - the shipped rollback contract stays contract-only:
    - it keeps `rollback_target_kind = future_applied_reviewed_memory_effect_only`
    - it keeps one `aggregate_identity_ref` plus exact supporting refs visible
    - it keeps `rollback_stage = contract_only_not_applied`
    - it keeps `audit_trace_expectation = operator_visible_local_transition_required`
    - current append-only `task_log` may mirror rollback transitions but must not become the canonical rollback store
  - the shipped disable slice stays contract-only:
    - one read-only `reviewed_memory_disable_contract`
    - `disable_target_kind = future_applied_reviewed_memory_effect_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - `disable_stage = contract_only_not_applied`
    - `effect_behavior = stop_apply_without_reversal`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - current append-only `task_log` may mirror disable transitions but must not become the canonical disable store
  - the shipped conflict slice stays contract-only:
    - one read-only `reviewed_memory_conflict_contract`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - fixed `conflict_target_categories`:
      - `future_reviewed_memory_candidate_draft_vs_applied_effect`
      - `future_applied_reviewed_memory_effect_vs_applied_effect`
    - `conflict_visibility_stage = contract_only_not_resolved`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - current append-only `task_log` may mirror conflict transitions but must not become the canonical conflict store
  - the shipped operator-audit slice stays contract-only:
    - one read-only `reviewed_memory_transition_audit_contract`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
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
    - current append-only `task_log` may mirror transition traces but must not become the canonical transition store
  - the first operator-visible trigger-source layer is now implemented above that contract-only slice and still below the emitted record:
    - `Option A` is shipped
    - one separate aggregate-level surface is fed only by `recurrence_aggregate_candidates`
    - it stays in the existing shell session stack as one section adjacent to `검토 후보`
    - it does not live on source-message cards and does not live in `review_queue_items`
    - the first operator-visible action label stays fixed at `검토 메모 적용 시작`
    - blocked state remains operator-visible while `capability_outcome = blocked_all_required`:
      - keep the control visible but disabled while blocked or while the note is empty
      - do not show an active `operator_reason_or_note` field while blocked
      - do not mint `canonical_transition_id` or `emitted_at` while blocked
      - do not emit `reviewed_memory_transition_record` while blocked
    - the enabled submit boundary is now implemented when `capability_outcome = unblocked_all_required`:
      - show a mandatory `operator_reason_or_note` textarea on the aggregate card
      - keep the submit button disabled until the textarea is non-empty
      - clicking the enabled submit now emits one `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` and persists it on the session under `reviewed_memory_emitted_transition_records`; reviewed-memory apply is NOT triggered
      - `reviewed_memory_transition_record` is absent while blocked; emitted only at the enabled submit boundary
    - the enabled state stays inline on the same aggregate card:
      - require one explicit local `operator_reason_or_note`
      - mint one real `canonical_transition_id` only at that enabled aggregate-card submission boundary
      - mint one local `emitted_at` only at that same submission boundary
    - this trigger-source layer remains separate from reviewed-memory apply result
  - the first emitted-transition-record layer is now implemented above that contract-only slice:
    - one aggregate-level read-only `reviewed_memory_transition_record`
    - `transition_record_version = first_reviewed_memory_transition_record_v1`
    - one `canonical_transition_id`
    - one `transition_action` from the shipped fixed vocabulary
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
    - that layer remains smaller than reviewed-memory apply and user-level memory
  - the shipped unblock slice stays contract-only:
    - one read-only `reviewed_memory_unblock_contract`
    - exact `required_preconditions`
    - `unblock_status = blocked_all_required`
    - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
    - `partial_state_policy = partial_states_not_materialized`
    - current object existence does not mean `unblocked_all_required`
  - the shipped capability outcome stays separate from the shipped unblock slice:
    - one read-only `reviewed_memory_capability_status`
    - `capability_version = same_session_reviewed_memory_capabilities_v1`
    - exact `required_preconditions`
    - `capability_outcome`
      - current shipped state = `unblocked_all_required`
      - no later wider capability-outcome state is currently defined in the MVP slice
    - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
    - `partial_state_policy = partial_states_not_materialized`
    - current object existence does not mean `unblocked_all_required`
    - it does not overwrite the shipped `reviewed_memory_unblock_contract`
    - it remains smaller than emitted transition records and reviewed-memory apply
  - the current truthful capability-path source stays separate from both shipped status surfaces:
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
    - this source family stays internal and additive; it is not a shipped payload object
    - current contract-object existence does not mean this source family exists
    - approval-backed save support, historical adjuncts, source-message review acceptance, queue presence, and `task_log` replay do not materialize this source family
    - current architecture now also evaluates this internal source family for the same aggregate, and it now resolves one real `boundary_source_ref` backer against the same exact aggregate's `검토 메모 적용 시작` trigger affordance
    - current architecture now also resolves one internal `rollback_source_ref` only as one exact ref to the same exact rollback-side handle
    - current architecture now also resolves one internal `disable_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_disable_contract` plus the shared `reviewed_memory_applied_effect_target`; it materializes only when both the disable contract and the applied-effect target truthfully match the same exact aggregate scope
    - current architecture now also resolves one internal `conflict_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_conflict_contract` plus the shared `reviewed_memory_applied_effect_target`; it materializes only when both the conflict contract and the applied-effect target truthfully match the same exact aggregate scope
    - current architecture now also resolves one internal `transition_audit_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_transition_audit_contract` plus the shared `reviewed_memory_applied_effect_target`; the internal `reviewed_memory_capability_source_refs` family is now complete with all five refs resolved
    - `reviewed_memory_capability_basis` is now materialized above the complete source family; `capability_outcome` is now `unblocked_all_required`
    - current architecture now also evaluates one internal `reviewed_memory_local_effect_presence_proof_record` helper for that same exact aggregate, and it now materializes only from one exact same-session internal `reviewed_memory_local_effect_presence_proof_record_store` entry for that aggregate; current implementation now also truthfully mints one exact payload-hidden canonical proof-record/store entry for the current exact aggregate state inside that internal boundary while the helper keeps `first_seen_at` alone, source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay outside that lower canonical proof-record layer
    - current architecture now also evaluates one internal `reviewed_memory_local_effect_presence_proof_boundary` helper for that same exact aggregate, and it now materializes one internal same-aggregate proof boundary only from one exact matching canonical local proof record/store entry while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current architecture now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from one exact matching proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current architecture now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source result only from one exact matching fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - the exact local proof boundary beneath that fact-source-instance helper is one now-materialized shared internal `reviewed_memory_local_effect_presence_proof_boundary`
    - the exact canonical local proof record beneath that proof-boundary helper is one now-materialized internal `reviewed_memory_local_effect_presence_proof_record`, and the proof-boundary helper now materializes only from one exact matching proof record inside one same-session internal `reviewed_memory_local_effect_presence_proof_record_store` boundary for the same aggregate
    - current architecture now also evaluates one internal `reviewed_memory_local_effect_presence_event` helper for that same exact aggregate, and it now materializes one internal same-aggregate event result only from one exact matching fact-source result while reusing the same `applied_effect_id` and `present_locally_at`; that layer stays payload-hidden
    - current architecture now also evaluates one internal `reviewed_memory_local_effect_presence_event_producer` helper for that same exact aggregate, and it now materializes one internal same-aggregate producer result only from one exact matching event result while reusing the same `applied_effect_id` and `present_locally_at`
    - current architecture now also evaluates one internal `reviewed_memory_local_effect_presence_event_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate event-source result only from one exact matching producer result while reusing the same `applied_effect_id` and `present_locally_at`
    - current architecture now also evaluates one internal `reviewed_memory_local_effect_presence_record` helper for that same exact aggregate, and it now materializes one internal same-aggregate source-consumer record only from one exact matching event-source helper result while reusing the same `applied_effect_id` and `present_locally_at`
    - current architecture now also evaluates one internal `reviewed_memory_applied_effect_target` helper for that same exact aggregate, and it now materializes one internal same-aggregate shared target only from one exact matching source-consumer helper result while reusing the same `applied_effect_id` and `present_locally_at`
    - current architecture now also evaluates one internal `reviewed_memory_reversible_effect_handle` helper for that same exact aggregate, and it now materializes one internal same-aggregate rollback-capability handle only from one exact matching shared target plus one exact matching rollback contract
    - the exact local fact source beneath that raw helper is one now-materialized shared internal `reviewed_memory_local_effect_presence_fact_source`:
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
    - the exact local event above that fact source and beneath that producer helper is one now-materialized shared internal `reviewed_memory_local_effect_presence_event`:
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
    - the first local identity rule should stay minimal:
      - do not add a second proof id in the first contract
      - reuse `applied_effect_id` as the first local identity minted at the truthful canonical proof-record instant beneath the proof-boundary helper
      - reuse `aggregate.last_seen_at` only when it is exactly that same first truthful local instant
    - the exact local target beneath that handle is one now-materialized shared internal `reviewed_memory_applied_effect_target`:
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
    - the exact local effect-presence event source above that producer-helper result and beneath the source-consumer helper is one now-materialized shared internal `reviewed_memory_local_effect_presence_event_source`:
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
    - the current raw-event helper `reviewed_memory_local_effect_presence_event` now materializes only from one exact matching `reviewed_memory_local_effect_presence_fact_source`
    - the current producer helper `reviewed_memory_local_effect_presence_event_producer` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event`
    - the current event-source helper `reviewed_memory_local_effect_presence_event_source` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event_producer`
    - the current source-consumer helper `reviewed_memory_local_effect_presence_record` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event_source`
    - the current target helper now materializes only from that exact matching source-consumer helper result
    - that target is shared by the now-materialized rollback handle (and later disable handles when implemented), while each handle keeps its own contract linkage and capability semantics
    - the full internal `reviewed_memory_capability_source_refs` family is now complete with all five refs resolved
  - the current truthful capability-path basis stays separate from both shipped status surfaces and from that source family:
    - one current read-only `reviewed_memory_capability_basis`
    - `basis_version = same_session_reviewed_memory_capability_basis_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - exact `required_preconditions`
    - `basis_status = all_required_capabilities_present`
    - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
    - `evaluated_at`
    - current contract-object existence does not mean this basis object exists
    - approval-backed save support, historical adjuncts, source-message review acceptance, queue presence, and `task_log` replay do not materialize this basis object
    - current `capability_outcome = unblocked_all_required` is truthful only when the same exact aggregate also exposes both a full matching `reviewed_memory_capability_source_refs` family and this matching capability-basis object
    - current architecture now also emits this basis layer during aggregate serialization when the same aggregate exposes the full matching source family, and `capability_outcome` is now `unblocked_all_required`
  - current architecture still emits no reviewed-memory candidate store; the reviewed-memory apply path (apply / stop-apply / reversal / conflict-visibility) is now shipped
- current review-layer traces stay downstream from this key:
  - `review_queue_items` remain the pending-only surface for one current `durable_candidate`
  - `candidate_review_record` remains the reviewed-but-not-applied outcome for one current candidate version
  - reviewed acceptance may later strengthen repeated-signal promotion evidence, but it must not replace the recurrence key itself
- this contract should come before broader `edit` / `reject` / `defer` expansion because those actions still operate on one source-message candidate version, while the recurrence-key-plus-same-session-aggregate boundary is the first truthful cross-source identity needed before same-family aggregation or repeated-signal promotion can be honest
  - this contract should also come before repeated-signal promotion because current architecture still has no separate reviewed-memory boundary, no rollback / disable surface, no operator-audit repair surface, and no cross-session conflict boundary above the aggregate
  - the next architecture widening should still stay closed:
    - keep the shipped readiness surface separate from the blocked-only status object:
      - one read-only `reviewed_memory_unblock_contract`
      - exact `required_preconditions`
      - binary `unblock_status`
      - `partial_state_policy = partial_states_not_materialized`
      - keep the shipped capability-status surface separate from the shipped unblock contract:
        - one read-only `reviewed_memory_capability_status`
        - current `capability_outcome` is now `unblocked_all_required`
        - let current `unblocked_all_required` mean draft-planning readiness only
        - require one matching internal `reviewed_memory_capability_source_refs` plus one matching `reviewed_memory_capability_basis` before that truthful state can exist
        - keep the current shipped planning-only target meaning centralized on `reviewed_memory_planning_target_ref.target_label`
        - keep duplicated target echo fields removed together and do not reopen them as compatibility fallbacks
        - do not add a post-cleanup compatibility note that presents removed target fields as active schema; architecture wording should stay shared-ref-only
        - do not reinterpret the shipped unblock contract as emitted transition record, apply result, or state machine
      - keep the capability-path layer smaller than emitted transition record:
        - capability-path opening alone must not create `canonical_transition_id`
        - capability-path opening alone must not collect `operator_reason_or_note`
        - capability-path opening alone must not create `emitted_at`
        - capability-path opening alone must not require `task_log` mirroring
      - keep `review_queue_items` and source-message `candidate_review_record` separate from the current shipped aggregate-level trigger-source layer
      - the current shipped emitted transition surface is one separate `reviewed_memory_transition_record`, not a `task_log` replay or apply result
      - that emitted record materializes only for one explicit aggregate-card `future_reviewed_memory_apply` submission after truthful `unblocked_all_required`
      - `future_reviewed_memory_stop_apply` is now also implemented (no longer later than the first action-specific emission trigger); `future_reviewed_memory_reversal` is now also implemented (no longer later): after stop-apply the aggregate card shows an `적용 되돌리기` button; clicking it changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; aggregate identity, supporting refs, and contracts are retained; `future_reviewed_memory_conflict_visibility` is now also implemented (see `reviewed_memory_conflict_visibility_record`)
      - keep first-round `task_log` mirroring optional; canonical emitted record remains the state source
      - the truthful same-aggregate `unblocked_all_required` path above the now-materialized basis and now-complete internal source family is now implemented; the enabled aggregate-card submit boundary is now open; one truthful aggregate-level `reviewed_memory_transition_record` is now emitted at that boundary; the reviewed-memory apply boundary is now also implemented: after emission the aggregate card shows a `검토 메모 적용 실행` button, clicking it changes `record_stage` from `emitted_record_only_not_applied` to `applied_pending_result` and adds `applied_at` via POST `/api/aggregate-transition-apply`; the apply result is now also implemented: after the apply boundary the card shows `결과 확정`, clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply (`future_reviewed_memory_stop_apply`) is now also implemented: after the effect is active the aggregate card shows an `적용 중단` button; clicking it changes `record_stage` to `stopped`, sets `apply_result.result_stage` to `effect_stopped`, removes the effect from `reviewed_memory_active_effects`, and future responses no longer include the `[검토 메모 활성]` prefix; reversal (`future_reviewed_memory_reversal`) is now also implemented: after the effect is stopped the aggregate card shows an `적용 되돌리기` button; clicking it changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; aggregate identity, supporting refs, and contracts are retained; reversal is separate from stop-apply; `future_reviewed_memory_conflict_visibility` is now also implemented: after reversal the aggregate card shows a `충돌 확인` button; clicking it records a `reviewed_memory_conflict_visibility_record` with `record_stage = conflict_visibility_checked`
    - no disable state machine or disable satisfaction booleans yet
    - no rollback state machine or rollback satisfaction booleans yet
    - no per-precondition satisfaction booleans yet
    - the emitted reviewed-memory transition record surface is now shipped (apply / stop-apply / reversal / conflict-visibility)
    - no payload-visible reviewed-memory store and no payload-visible proof-record or proof-boundary surface
  - no cross-session counting
  - the shipped operator-audit contract now closes the last read-only precondition surface before any apply vocabulary opens

### Session-Level Vs Future User-Level Boundary

- session-level memory stays attached to the current session object and immediate follow-up loop
- the first session-level unit should remain an artifact-scoped working signal, not a cross-session user rule
- the current `durable_candidate` lives on source-message serialization and may be repackaged by the current session-level read-only review queue, but it is not yet a user profile record
- user-level memory remains a future design target until the product has:
  - explicit candidate review controls
  - local audit and rollback
  - scope rules
  - conflict handling

### Review Queue Surface

- the current shipped first slice now includes one local pending review queue surface fed only by eligible `durable_candidate` records
- that surface remains narrow:
  - it is derived from current session serialization
  - it does not create a second durable store
  - it allows only `accept`
  - it keeps the result reviewed-but-not-applied
- `session_local` signals should not enter the review queue directly
- the first shipped review-action trace reuses the same source-message anchor instead of opening a second review store:
  - one optional source-message sibling `candidate_review_record`
  - canonical source remains current persisted session state
  - task-log remains audit-only
- minimum shipped `candidate_review_record` fields:
  - `candidate_id`
  - `candidate_updated_at`
  - `artifact_id`
  - `source_message_id`
  - `review_scope = source_message_candidate_review`
  - `review_action = accept`
  - `review_status = accepted`
  - `recorded_at`
- later action meanings stay narrow:
  - `accept` reviews the current `durable_candidate` as reusable, but does not apply user-level memory
  - `edit` records a reviewed reusable statement, but does not rewrite the source-message corrected text or the source-message `durable_candidate`
  - `reject` dismisses the current `durable_candidate` as a reviewed candidate, but is not content reject or approval reject
  - `defer` postpones review of the current `durable_candidate`, but does not invalidate its source-message basis
- queue derivation rule in the shipped slice:
  - `review_queue_items` should remain the pending-only surface
  - an item should appear only while the same current source message still has:
    - current `durable_candidate`
    - `promotion_eligibility = eligible_for_review`
    - no matching current `candidate_review_record` on the same `artifact_id`, `source_message_id`, `candidate_id`, and `candidate_updated_at`
  - after one matching `accept` record is written for that current candidate version, the item should leave the pending queue
  - first action-capable slices should not add accepted / rejected / deferred tabs or a second page
- remaining review vocabulary stays later:
  - `edit`, `reject`, and `defer` are still deferred in UI and persistence
- the default reviewer assumption is the same local user on the same machine
- review outcomes should be append-only audit events rather than silent replacement of candidate history
- current code now has one `accept` review action API but still has no `edit` / `reject` / `defer` API, no payload-visible reviewed-memory store, no payload-visible proof-record or proof-boundary surface, and no user-level memory application

### Scope / Conflict / Rollback Boundary

- the first review-action contract should not open scope suggestion yet:
  - `review_scope` stays fixed at `source_message_candidate_review`
  - future `proposed_scope`, `scope_candidates_considered`, and `scope_suggestion_reason` belong to later reviewed-memory planning, not the first action trace
- future reviewed memory may later use these scope candidates:
  - `workflow_type`
  - `path_family`
  - `document_type`
  - `global`
- the default suggested scope should stay conservative:
  - `workflow_type`
  - `path_family`
  - `document_type`
  - `global`
- broader suggested scope should require recorded justification that:
  - narrower candidates are missing, unstable, or weakly supported
  - the same signal already spans multiple narrower contexts
  - or explicit user confirmation requests broader reuse
- proposed scope remains review input only; it is not an applied memory scope before review
- reviewed memory should outrank unreviewed `durable_candidate` signals
- narrower reviewed scope should outrank broader reviewed scope within the same category
- unresolved same-scope conflicts should remain pending or deferred until explicitly reviewed
- item-level and scope-level disable or rollback are required before any promotion to future user-level memory
- rollback should preserve audit history and later non-application traces instead of deleting prior records
- approval-backed save may support a review decision, but it should not act as an implicit globalizer of scope
- reviewed outcome and user-level memory must remain separate layers:
  - `candidate_review_record` is the first review-outcome trace only
  - future reviewed memory may later consume that trace
  - future user-level memory application remains later because rollback and scope rules are still required

### Evidence / Source Link Strategy

- the minimum contract should reuse the existing message-level evidence and summary chunk snapshots
- it should carry reason records alongside those snapshots
- it should carry future review and rollback references when they exist
- it should not require a new normalized evidence database in the same step
- the artifact must remain traceable back to the original message and original source paths
- approval payloads and task-log records should keep only `artifact_id` linkage rather than copying the full normalized snapshot

### Eval-Ready Artifact Trace Contract

- future workflow-grade eval should require one core chain:
  - artifact record
  - original response snapshot
  - evidence/source trace
  - corrected or accepted outcome
- the current implementation already exposes raw ingredients for that chain through:
  - session message records with `message_id`, `original_response_snapshot`, `evidence`, `summary_chunks`, `saved_note_path`, and feedback
  - append-only task-log events for approval and write actions
  - response serialization in `app/web.py`
- future placeholder extensions should add:
  - reason records
  - review records
  - rollback records
  - explicit-confirmation versus approval-support linkage
- the first implementation slice should prepare only the initial anchor for that future chain:
  - one `artifact_id`
  - one `artifact_kind`
  - one consistent linkage path across message, approval, write, and feedback-related traces
- if a core link is missing, the artifact should not enter the workflow-grade fixture matrix
- if a family-specific extension is missing, the artifact may still be trace-complete for another family, but not for that specific fixture family

### Future Operator Boundary

- broad local operator flows are still out of scope for the current and next phase contracts
- the first narrow reviewed-memory operator surface is now implemented as one aggregate-level `future_reviewed_memory_apply` trigger-source affordance:
  - fed only by `recurrence_aggregate_candidates`
  - rendered in the existing shell session stack
  - separate from `검토 후보`
  - the submit boundary is now enabled when `capability_outcome = unblocked_all_required` and the user has entered a non-empty reason note
  - a mandatory `operator_reason_or_note` textarea is now visible on the aggregate card when unblocked; the submit button stays disabled until the note is non-empty
  - clicking the enabled submit now emits one `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied`; reviewed-memory apply result is NOT triggered at this boundary
  - the reviewed-memory apply boundary is now also implemented: after emission the aggregate card shows a `검토 메모 적용 실행` button; clicking it POSTs to `/api/aggregate-transition-apply` and changes `record_stage` from `emitted_record_only_not_applied` to `applied_pending_result` with `applied_at` added; the apply result is now also implemented: after the apply boundary the card shows `결과 확정`, clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply (`future_reviewed_memory_stop_apply`) is now also implemented: after the effect is active the aggregate card shows an `적용 중단` button; clicking it changes `record_stage` to `stopped`, sets `apply_result.result_stage` to `effect_stopped`, removes the effect from `reviewed_memory_active_effects`, and future responses no longer include the `[검토 메모 활성]` prefix; reversal (`future_reviewed_memory_reversal`) is now also implemented: after the effect is stopped the aggregate card shows an `적용 되돌리기` button; clicking it changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; aggregate identity, supporting refs, and contracts are retained; reversal is separate from stop-apply; `future_reviewed_memory_conflict_visibility` is now also implemented: after reversal the aggregate card shows a `충돌 확인` button; clicking it records a `reviewed_memory_conflict_visibility_record` with `record_stage = conflict_visibility_checked`
  - still smaller than active reviewed-memory effect on future responses
- broader operator-control architecture should remain later than the reviewed-memory layer and its eval traces

## Safety Boundaries

- writes are approval-based
- overwrite is rejected by default
- web search is read-only and permission-gated
- PDF requires a text layer
- OCR is currently unsupported and must return explicit guidance
- future preference memory must remain auditable and local-first

## Testing Strategy

### Automated
- `python3 -m unittest -v`
- focused service/smoke slices
- Playwright browser smoke (`make e2e-test`)

### Browser Smoke Coverage
- file summary with evidence and summary-range panels
- browser file picker
- browser folder picker for search
- approval reissue
- approval-backed save
- late flip after explicit original-draft save keeps saved history while latest content verdict changes
- corrected-save first bridge path
- `내용 거절` content-verdict path with same-card reject-note update, approval preserved, and later explicit save supersession
- candidate-linked explicit confirmation path with read-only `검토 후보` appearance and later stale-clear
- same-session recurrence aggregate path with one separate `검토 메모 적용 후보` section, `검토 메모 적용 시작` enabled with mandatory reason textarea when `capability_outcome = unblocked_all_required` (disabled while blocked or note empty), emitted `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` on enabled submit, preserved `review_queue_items` separation, `검토 메모 적용 실행` apply button visible after transition record emission, clicking apply changes `record_stage` to `applied_pending_result` and adds `applied_at`, `결과 확정` button visible after apply boundary, clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`, and the memory effect on future responses is now active (`result_stage = effect_active`) with active effects stored on the session as `reviewed_memory_active_effects` and future responses including a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply: after the effect is active the card shows `적용 중단`; clicking it changes `record_stage` to `stopped` and removes the effect; reversal: after stop the card shows `적용 되돌리기`; clicking it changes `record_stage` to `reversed`; conflict-visibility: after reversal the card shows `충돌 확인`; clicking it records a `reviewed_memory_conflict_visibility_record` with `record_stage = conflict_visibility_checked`
- corrected-save saved snapshot remains while late reject and later re-correct move the latest state separately
- streaming cancel

### Next-Phase Eval Placeholder
- use named fixture families rather than one broad placeholder bucket:
  - `GB-EVAL-CR-01`
  - `GB-EVAL-AF-01`
  - `GB-EVAL-RU-01`
  - `GB-EVAL-SC-01`
  - `GB-EVAL-RB-01`
  - `GB-EVAL-CD-01`
  - `GB-EVAL-AS-01`
- keep the eval axes separate:
  - correction reuse
  - approval friction
  - scope safety
  - reviewability / rollbackability
  - trace completeness
- for the first implementation slice, begin with focused service/smoke checks that prove the trace anchor survives across existing layers
- start with manual inspection placeholders and service-level fixtures once the memory records exist
- add unit-level helpers for count, trace-chain, and eligibility validation
- defer e2e coverage until review or rollback UI surfaces actually exist

## Implementation Status

### Implemented
- local web shell
- session timeline
- approval + reissue approval flow
- evidence/source panel
- summary-range panel
- response origin badge
- streaming progress and cancel
- feedback capture on assistant messages
- claim coverage state and reinvestigation helpers

### In Progress
- higher-quality entity-card investigation
- better slot agreement and source consensus
- stronger distinction between confirmed vs uncertain facts

### Not Implemented
- separate `grounded brief` artifact store
- correction / approval / preference memory store
- OCR
- background automation
- proprietary model training
- local operator surface

### Partial / Opt-In
- SQLite backend (`storage_backend='sqlite'`): opt-in storage seam for session, artifact, preference, task-log tables. JSON backend remains default. Corrections store stays JSON-only. `storage/migrate.py` provides a JSON→SQLite migration CLI. Default rollout is deferred.

### Open Questions
- What is the narrowest future explicit confirmation signal shape that stays candidate-linked without being mistaken for save approval?
- If `durable_candidate` later leaves the source-message surface, should it keep reusing the current source-message candidate id or mint a new durable-scope id at that boundary?
- Which exact local-store, stale-resolution, and reviewed-memory preconditions should be required before any cross-session recurrence aggregation opens?
- Should the default recurrence rule stay at two grounded briefs for every candidate category, or vary by category later?
- Should the current fixed `confidence_marker = same_session_exact_key_match` remain enough until same-session unblock semantics can be satisfied truthfully, or should a later second conservative level be added only after that boundary opens?
- Should the shipped `reviewed_memory_boundary_draft` keep repeating the fixed `reviewed_scope` label long term, or could a later normalization collapse it into `aggregate_identity_ref` plus supporting refs only?
- Should later category-specific tuning vary approval-backed-save weight beyond the baseline weak-content / medium-path rule?
