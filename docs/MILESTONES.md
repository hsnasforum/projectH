# Milestones

## Framing

### Current Product
- The shipped contract remains a local-first document assistant web MVP with response feedback capture, grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, and artifact-linked reject/reissue reason traces.
- Web investigation remains a permission-gated secondary mode (disabled/approval/enabled per session) under the document-first guardrail.
- The current release candidate is the `app.web` browser shell; pipeline/controller/operator tooling remains outside the release gate.

### Next Phase
- The next phase is a correction / approval / preference memory layer for document work.

### Long-Term North Star
- The long-term direction is a teachable local personal agent with later approval-gated local action.

## Completed

### Milestone 1: Local Document Loop
- local file read
- document summary
- document search
- session persistence
- approval-based save
- task log

### Milestone 2: Web MVP Shell
- local web shell
- recent sessions and timeline
- response cards with note preview, structured search result preview panel, evidence/source panel, summary source-type labels (`문서 요약` / `선택 결과 요약`), and summary span / applied-range panel
- approval card UX
- reissue approval flow
- response origin badge
- applied-preferences badge (`선호 N건 반영`) on assistant messages when `applied_preferences` is non-empty, with tooltip showing preference descriptions
- streaming progress and cancel

### Milestone 3: Core QA And Trace Baseline
- Python regression suite
- Playwright smoke suite (scenario 1 now also covers response copy button state with clipboard write verification, per-message timestamps, source filename in both quick-meta and transcript meta, note-path default-directory placeholder, and `문서 요약` source-type label in both quick-meta and transcript meta; browser file picker scenario now also covers source filename and `문서 요약` source-type label in both quick-meta and transcript meta; folder-search scenario now also covers `선택 결과 요약` source-type label and multi-source count-based metadata in both quick-meta and transcript meta, plus response detail preview panel alongside summary body with both cards' ordered labels, full-path tooltips, match badges, and snippet text content, and transcript preview panel with item count, both cards' ordered labels, full-path tooltips, match badges, and snippet text content; general chat scenario covers negative source-type label contract; dedicated claim-coverage panel rendering contract scenario with leading status tags, actionable hints, and focus-slot reinvestigation explanation including reinforced / regressed / still single-source / still unresolved with natural Korean particle normalization)
- search-only response browser smoke with transcript preview cards, hidden body text, `selected-copy` button visibility/click/notice/clipboard regression coverage, full-path tooltip on preview card ordered labels, and match-type badge plus content snippet text in both response detail and transcript
- stable mock-baseline Playwright launch contract with dedicated mock webServer startup and no preexisting-server reuse on the smoke port
- late flip after explicit original-draft save browser smoke
- corrected-save first bridge browser smoke
- corrected-save late reject / re-correct browser smoke
- rejected content-verdict browser smoke
- candidate-linked explicit confirmation browser smoke covering response-card separation, save-support distinction, `검토 후보` appearance, `검토 수락`, reviewed-but-not-applied queue removal, and later stale-clear behavior
- same-session recurrence aggregate browser smoke covering separate `검토 메모 적용 후보` placement, `검토 메모 적용 시작` enabled with mandatory reason textarea when `capability_outcome = unblocked_all_required` (disabled while blocked or note empty), preserved separation from `검토 후보`, emitted `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` on enabled submit, `검토 메모 적용 실행` apply button visible after transition record emission, clicking apply changes `record_stage` to `applied_pending_result` and adds `applied_at` via POST `/api/aggregate-transition-apply`, `결과 확정` button visible after apply boundary, clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = effect_active`, and `result_at`, and confirmed the memory effect is now active (`result_stage = effect_active`) with active effects stored on the session as `reviewed_memory_active_effects` and future responses including a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply (`future_reviewed_memory_stop_apply`) is now also implemented: after the effect is active the aggregate card shows an `적용 중단` button; clicking it changes `record_stage` to `stopped`, sets `apply_result.result_stage` to `effect_stopped`, removes the effect from `reviewed_memory_active_effects`, and future responses no longer include the `[검토 메모 활성]` prefix; reversal (`future_reviewed_memory_reversal`) is now also implemented: after the effect is stopped the aggregate card shows an `적용 되돌리기` button; clicking it changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; aggregate identity, supporting refs, and contracts are retained; reversal is separate from stop-apply; conflict visibility (`future_reviewed_memory_conflict_visibility`) is now also implemented: after the effect is reversed the aggregate card shows a `충돌 확인` button; clicking it creates a separate conflict-visibility transition record with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, evaluated `conflict_entries` and `conflict_entry_count`, and `source_apply_transition_ref`; the conflict visibility record is separate from the apply transition record
- web-search history card header badge browser smoke covering answer-mode badge, verification-strength badge with CSS class, and source-role trust badge compact label with trust class
- history-card entity-card `다시 불러오기` click reload browser smoke covering `WEB` badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source-role detail retention after server-side record reload
- history-card latest-update `다시 불러오기` click reload browser smoke covering `WEB` badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source-role detail retention after server-side record reload
- history-card entity-card `다시 불러오기` follow-up browser smoke covering `WEB` badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source-role detail drift prevention
- history-card latest-update `다시 불러오기` follow-up browser smoke covering `WEB` badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source-role detail drift prevention
- history-card latest-update `다시 불러오기` noisy community source exclusion browser smoke covering negative `보조 커뮤니티` / `brunch` in response body, origin detail, and context box + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention
- history-card entity-card `다시 불러오기` noisy single-source claim exclusion browser smoke covering `설명형 다중 출처 합의`, `백과 기반`, negative `출시일` / `2025` / `blog.example.com` in response body and origin detail, positive agreement-backed fact card, `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance in context box/source_paths
- history-card entity-card `다시 불러오기` dual-probe source-path + response-origin exact-field drift-prevention browser smoke covering `pearlabyss.com/200` and `pearlabyss.com/300` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` after reload
- history-card latest-update `다시 불러오기` mixed-source source-path + response-origin exact-field drift-prevention browser smoke covering `store.steampowered.com` and `yna.co.kr` in context box, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` after reload
- history-card latest-update single-source `다시 불러오기` verification-label exact-field drift-prevention browser smoke covering `단일 출처 참고` and `보조 출처` in origin detail after reload
- history-card latest-update news-only `다시 불러오기` verification-label exact-field drift-prevention browser smoke covering `기사 교차 확인` and `보조 기사` in origin detail after reload
- history-card latest-update news-only `다시 불러오기` source-path exact-field drift-prevention browser smoke covering `hankyung.com` and `mk.co.kr` in context box after reload
- history-card latest-update single-source `다시 불러오기` source-path exact-field drift-prevention browser smoke covering `example.com/seoul-weather` in context box after reload
- history-card latest-update single-source `다시 불러오기` follow-up response-origin exact-field drift-prevention service + browser smoke covering `단일 출처 참고` and `보조 출처` drift prevention
- history-card latest-update news-only `다시 불러오기` follow-up response-origin exact-field drift-prevention service + browser smoke covering `기사 교차 확인` and `보조 기사` drift prevention
- history-card entity-card `다시 불러오기` follow-up dual-probe source-path + response-origin exact-field drift-prevention service + browser smoke covering `pearlabyss.com/200` and `pearlabyss.com/300` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반`
- history-card latest-update mixed-source `다시 불러오기` follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `store.steampowered.com` and `yna.co.kr` in context box, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반`
- history-card latest-update single-source `다시 불러오기` follow-up source-path exact-field drift-prevention service + browser smoke covering `example.com/seoul-weather` in context box
- history-card latest-update news-only `다시 불러오기` follow-up source-path exact-field drift-prevention service + browser smoke covering `hankyung.com` and `mk.co.kr` in context box
- history-card entity-card zero-strong-slot `다시 불러오기` reload response-origin + answer-mode + verification-label + source-path exact-field drift-prevention browser smoke covering `WEB` badge, `설명 카드` answer-mode badge, downgraded `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` in context box
- history-card entity-card zero-strong-slot `다시 불러오기` follow-up response-origin + source-path exact-field drift-prevention service + browser smoke covering `WEB` badge, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` drift prevention
- history-card entity-card zero-strong-slot click-reload second-follow-up response-origin + source-path exact-field drift-prevention service + browser smoke covering `WEB` badge, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` drift prevention
- entity-card zero-strong-slot browser natural-reload exact-field + source-path smoke covering `방금 검색한 결과 다시 보여줘` path with `WEB` badge, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` in context box
- entity-card zero-strong-slot browser natural-reload follow-up response-origin + source-path exact-field drift-prevention smoke covering `WEB` badge, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` drift prevention after natural reload + follow-up
- entity-card 붉은사막 검색 결과 browser natural-reload exact-field + noisy exclusion smoke covering `방금 검색한 결과 다시 보여줘` path with `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` retention, `출시일`/`2025`/`blog.example.com` 본문/detail 미노출, context box `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance 포함
- entity-card dual-probe browser natural-reload source-path exact-field drift-prevention smoke covering `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300` in context box after `방금 검색한 결과 다시 보여줘`
- entity-card dual-probe browser natural-reload exact-field smoke covering `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` retention after `방금 검색한 결과 다시 보여줘`
- entity-card dual-probe browser natural-reload follow-up source-path exact-field drift-prevention smoke covering `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300` in context box after natural reload + follow-up
- entity-card dual-probe browser natural-reload follow-up response-origin exact-field drift-prevention smoke covering `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift prevention
- entity-card 붉은사막 actual-search browser natural-reload follow-up source-path + response-origin exact-field drift-prevention smoke covering `namu.wiki`/`ko.wikipedia.org` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` drift prevention
- entity-card 붉은사막 browser natural-reload source-path smoke covering `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance in context box after `방금 검색한 결과 다시 보여줘`
- entity-card 붉은사막 actual-search browser natural-reload follow-up source-path smoke covering `namu.wiki`/`ko.wikipedia.org` in context box after natural reload + follow-up
- entity-card 붉은사막 browser natural-reload follow-up noisy single-source exclusion smoke covering negative assertions for `출시일`, `2025`, `blog.example.com` in response text and origin detail plus `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance context box continuity
- entity-card 붉은사막 browser natural-reload second-follow-up noisy single-source exclusion smoke covering negative assertions for `출시일`, `2025`, `blog.example.com` in response text and origin detail plus `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance context box continuity
- history-card entity-card `다시 불러오기` actual-search source-path plurality + response-origin exact-field drift-prevention service + browser smoke covering `namu.wiki` and `ko.wikipedia.org` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` after click reload
- history-card entity-card `다시 불러오기` follow-up actual-search source-path plurality + response-origin exact-field drift-prevention service + browser smoke covering `namu.wiki` and `ko.wikipedia.org` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` after click reload + follow-up
- history-card entity-card `다시 불러오기` second-follow-up actual-search source-path plurality + response-origin exact-field drift-prevention service + browser smoke covering `namu.wiki` and `ko.wikipedia.org` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` after click reload + second follow-up
- history-card entity-card `다시 불러오기` second-follow-up dual-probe source-path + response-origin exact-field drift-prevention service + browser smoke covering `pearlabyss.com/200`, `pearlabyss.com/300` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` after click reload + second follow-up
- entity-card dual-probe natural-reload second-follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300`, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` after natural reload + second follow-up
- entity-card 붉은사막 actual-search natural-reload second-follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `namu.wiki`/`ko.wikipedia.org`, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` after natural reload + second follow-up
- history-card latest-update mixed-source `다시 불러오기` second-follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `store.steampowered.com`, `yna.co.kr`, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` after click reload + second follow-up
- history-card latest-update single-source `다시 불러오기` second-follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `example.com/seoul-weather`, `WEB` badge, `최신 확인`, `단일 출처 참고`, `보조 출처` after click reload + second follow-up
- history-card latest-update news-only `다시 불러오기` second-follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `hankyung.com`, `mk.co.kr`, `WEB` badge, `최신 확인`, `기사 교차 확인`, `보조 기사` after click reload + second follow-up
- latest-update mixed-source `방금 검색한 결과 다시 보여줘` natural-reload exact-field service + browser smoke covering `store.steampowered.com`, `yna.co.kr`, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반`
- latest-update single-source `방금 검색한 결과 다시 보여줘` natural-reload exact-field service + browser smoke covering `example.com/seoul-weather`, `WEB` badge, `최신 확인`, `단일 출처 참고`, `보조 출처`
- latest-update news-only `방금 검색한 결과 다시 보여줘` natural-reload exact-field service + browser smoke covering `hankyung.com`, `mk.co.kr`, `WEB` badge, `최신 확인`, `기사 교차 확인`, `보조 기사`
- latest-update mixed-source natural-reload follow-up + second-follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `store.steampowered.com`, `yna.co.kr`, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반`
- latest-update single-source natural-reload follow-up + second-follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `example.com/seoul-weather`, `WEB` badge, `최신 확인`, `단일 출처 참고`, `보조 출처`
- latest-update news-only natural-reload follow-up + second-follow-up source-path + response-origin exact-field drift-prevention service + browser smoke covering `hankyung.com`, `mk.co.kr`, `WEB` badge, `최신 확인`, `기사 교차 확인`, `보조 기사`
- latest-update noisy-community natural-reload follow-up + second-follow-up exclusion service + browser smoke covering `보조 커뮤니티`, `brunch` negative in origin detail, response body, context box + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention
- latest-update noisy-community click-reload follow-up + second-follow-up exclusion service + browser smoke covering `보조 커뮤니티`, `brunch` negative in origin detail, response body, context box + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention
- entity-card noisy single-source claim natural-reload + click-reload follow-up/second-follow-up exclusion + provenance exact-field retention: `출시일`, `2025`, `blog.example.com` 본문/detail 미노출, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지, source_paths/context box에 `blog.example.com` provenance 포함
- PDF text-layer support: readable text-layer PDF → visible summary body with `문서 요약` label + context box/quick meta/transcript meta PDF filename
- OCR-not-supported guidance: scanned/image-only PDF → visible response guidance with `요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`
- browser file picker scanned/image-only PDF OCR-not-supported guidance smoke covering visible response guidance with exact strings `요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`
- browser folder picker scanned PDF + readable file mixed search count-only partial-failure notice + preview exact-field + selected-path/copy + transcript hidden smoke
- browser file picker readable text-layer PDF success summary smoke covering OCR guidance 미노출 + visible summary body with extracted text + context box/quick meta/transcript meta `readable-text-layer.pdf` + `문서 요약` label
- browser folder picker mixed scanned-PDF search-plus-summary partial-failure + preview exact-field + transcript preview exact-field smoke
- response feedback capture
- local web-search history storage

## In Progress

### Milestone 4: Secondary-Mode Investigation Hardening
- claim-based entity-card shaping
- slot coverage and reinvestigation
- source role labeling
- stronger official/news/wiki/community weighting
- better separation between strong facts, weak facts, and unresolved slots

### Why This Still Belongs To The Current Phase
- It improves the quality of the secondary investigation mode without changing the core product identity.
- It does not change the product into a web-search-first assistant.

## Next Phase Design Target

### Milestone 5: Grounded Brief Contract
- standardize the `grounded brief` as the first official artifact for single-document work
- make the brief the main product narrative for the current MVP
- keep approval, evidence, and feedback attached to the brief end to end
- implemented entry slice:
  - generate `artifact_id` and `artifact_kind` for grounded-brief responses
  - reuse the current assistant message as the first raw snapshot surface
  - thread the same artifact anchor through approval and task-log traces without adding a new UI surface
  - normalize `original_response_snapshot` on the same grounded-brief message/session surface
  - capture minimum `corrected_outcome.outcome = accepted_as_is` on the same original grounded-brief message when a save actually completes
  - add one small grounded-brief correction editor seeded with the current draft text
  - persist `corrected_text` and `corrected_outcome.outcome = corrected` on that same original grounded-brief message when the user explicitly submits edited text
  - capture minimum approval-linked `approval_reason_record` for reject / reissue traces on the same artifact anchor
  - add one explicit `save_content_source = original_draft` discriminator plus `source_message_id` anchor on the current save-note approval and write trace path
  - keep approval and task-log records anchor-linked instead of copying the full snapshot
- still later inside this milestone:
  - keep the first optional reject-note surface narrow and separate from richer reject labels now that the first explicit content-verdict surface has landed
  - keep corrected-save bridge expansion narrow and forbid automatic approval preview rebasing

### Milestone 6: Minimum Correction / Approval / Preference Memory Contract
- extend the grounded-brief correction outcome contract without widening scope
- record approval / rejection / reissue outcomes with artifact linkage
- define shared reason fields with distinct correction / reject / reissue label sets
- define one first `session_local` memory signal from current shipped explicit traces before any review queue or durable-candidate surface
- fix the truthful content-surface contract:
  - `rejected` requires an explicit content-verdict control separate from approval reject
  - the first control should be one response-card action such as `내용 거절`, separate from `수정본 기록` and corrected-save bridge
  - corrected submit and save approval remain separate actions
  - corrected-save reconciliation now follows `Option B`: a separate explicit save-request action for corrected text
  - reuse the shipped `save_content_source = original_draft | corrected_text` contract instead of changing the trace shape later
  - keep that corrected-save request as a bridge action from the response card that consumes recorded `corrected_text`
  - keep that bridge action always visible in the correction area, but disabled with helper copy until a correction is recorded
  - keep corrected-save approval snapshots immutable and use `approval_id` as the first snapshot identity
  - keep correction-area, approval-card, and corrected-save save-result wording explicit that the approval/write body is the request-time frozen snapshot
  - approval preview should always match the save source explicitly chosen at request time
  - keep the original grounded-brief source message as the content source of truth by extending the existing `corrected_outcome` envelope to allow `outcome = rejected`
  - keep the first reject-reason contract minimal: `reason_scope = content_reject`, `reason_label = explicit_content_rejection`, optional `reason_note`
  - keep one separate `content_reason_record` on that same source message while the latest outcome remains `rejected`
  - keep the shipped optional reject-note UX as one small inline response-card note surface that appears only while the latest outcome remains `rejected`
  - keep blank note submit disabled in the shipped slice instead of treating it as manual clear
  - when that note is recorded, update the same `content_reason_record.reason_note` in place and clear it again when a later correction or explicit save supersedes `rejected`
  - if a later manual clear refinement is ever added, keep it note-only: remove just `content_reason_record.reason_note`, preserve `rejected` plus the fixed label baseline, refresh `content_reason_record.recorded_at`, and audit it through a separate content-linked clear event
  - do not reuse approval-reject labels or approval-linked trace as the content-verdict source
- fix the first session-local memory-signal contract:
  - keep the canonical unit source-message-anchored with `artifact_id` + `source_message_id`
  - keep the signal read-only and session-scoped
  - keep content verdict, approval friction, and save linkage as separate axes inside that signal
  - reuse current session state and current trace anchors instead of adding a separate memory store
  - keep the shipped current-state signal narrow, then add at most one later superseded-reject replay adjunct before durable-candidate work widens
  - keep repeated same-session `correction_rewrite_preference` drafts per-source-message until a truthful merge key exists beyond family alone
- the minimum promotion guardrail from `session_local` to `durable_candidate` is now implemented for the explicit-confirmation path:
  - current `session_local_candidate` drafts stay narrow and unchanged in their own object shape
  - approval-backed save and historical adjuncts stay out of the primary promotion basis
  - the first shipped `durable_candidate` is one source-message-anchored read-only projection that consumes the shipped `candidate_confirmation_record`
  - current first slice reuses the source-message candidate id while the projection stays source-message-anchored
  - repeated-signal promotion remains blocked until a truthful recurrence key exists beyond family alone
- the first truthful recurrence-key slice is now also implemented:
  - the current contract is one source-message-anchored read-only `candidate_recurrence_key` draft
  - it identifies one deterministic rewrite-transformation class derived from the explicit original-vs-corrected pair
  - it is not `candidate_family` alone, fixed statement text alone, review acceptance alone, or approval-backed save alone
  - repeated-signal promotion still remains blocked until at least two distinct grounded briefs expose the same recurrence key
- the first post-key aggregation boundary is now also implemented:
  - the first aggregate unit stays same-session only
  - the current materialization is one read-only session-level `recurrence_aggregate_candidates` projection
  - one aggregate requires at least two distinct grounded-brief source-message anchors with the same exact recurrence identity
  - review acceptance may appear only as optional support and must not replace the recurrence identity
  - `confidence_marker` currently stays fixed at `same_session_exact_key_match`
  - cross-session counting remains later; the same-session layers (local store, rollback, conflict, and reviewed-memory boundary) and the apply lifecycle are already shipped above the capability path
- the first post-aggregate promotion boundary is now also fixed as a contract:
  - choose `Option A`: the shipped same-session aggregates remain promotion-ineligible
  - exact aggregate identity remains necessary but still insufficient for repeated-signal promotion
  - reviewed-memory apply, stop-apply, reversal, and conflict-visibility are now shipped above the exact unblock precondition family; rollback, disable, and operator-audit contract surfaces are also shipped as read-only objects; the capability-status path is materialized (`unblocked_all_required`) while per-precondition satisfaction booleans and repeated-signal promotion remain later:
    - `reviewed_memory_boundary_defined`
    - `rollback_ready_reviewed_memory_effect`
    - `disable_ready_reviewed_memory_effect`
    - `conflict_visible_reviewed_memory_scope`
    - `operator_auditable_reviewed_memory_transition`
  - the smallest shipped promotion surface remains the read-only aggregate-level promotion-eligibility marker only; the reviewed-memory apply path (apply / stop-apply / reversal / conflict-visibility) is shipped separately above the precondition family while promotion and cross-session counting remain later
  - the current contract now also emits one read-only aggregate-level `reviewed_memory_precondition_status` object with fixed overall blocked state and deterministic `evaluated_at = last_seen_at`
  - `reviewed_memory_boundary_defined` is now fixed to one shipped narrow reviewed scope:
    - `same_session_exact_recurrence_aggregate_only`
    - the shipped reviewed-memory boundary draft remains read-only and narrower than reviewed-memory store; the apply path is shipped separately while cross-session counting and user-level memory remain later
  - the current contract now also emits one read-only aggregate-level `reviewed_memory_boundary_draft` with:
    - `boundary_version = fixed_narrow_reviewed_scope_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `aggregate_identity_ref`
    - exact supporting refs
    - `boundary_stage = draft_not_applied`
    - deterministic `drafted_at = last_seen_at`
  - `rollback_ready_reviewed_memory_effect` is now fixed as one shipped rollback contract surface:
    - rollback means reversal of one applied reviewed-memory effect inside `same_session_exact_recurrence_aggregate_only`
    - the shipped boundary draft remains the scope draft and basis ref, not the rollback target
    - aggregate identity, supporting refs, boundary draft, and operator-visible audit trace must remain after rollback while only the applied effect deactivates
    - rollback remains separate from disable, conflict visibility, operator-audit repair, and cross-session counting
  - the current contract now also emits one read-only aggregate-level `reviewed_memory_rollback_contract` with:
    - one `reviewed_memory_rollback_contract`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `rollback_target_kind = future_applied_reviewed_memory_effect_only`
    - `rollback_stage = contract_only_not_applied`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - deterministic `defined_at = last_seen_at`
  - `disable_ready_reviewed_memory_effect` is now fixed as one shipped disable contract surface:
    - disable means stop-apply of one applied reviewed-memory effect inside `same_session_exact_recurrence_aggregate_only`
    - the shipped boundary draft and shipped rollback contract remain basis refs, not the disable target
    - aggregate identity, supporting refs, boundary draft, rollback contract, and operator-visible audit trace must remain after disable while only the applied effect becomes inactive
    - disable remains separate from rollback reversal, conflict visibility, operator-audit repair, and cross-session counting
  - the current contract now also emits one read-only aggregate-level `reviewed_memory_disable_contract` with:
    - one `reviewed_memory_disable_contract`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `disable_target_kind = future_applied_reviewed_memory_effect_only`
    - `disable_stage = contract_only_not_applied`
    - `effect_behavior = stop_apply_without_reversal`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - deterministic `defined_at = last_seen_at`
  - `conflict_visible_reviewed_memory_scope` is now fixed; the apply vocabulary is now shipped above this contract layer:
    - conflict visibility means operator-visible read-only exposure of competing reviewed-memory targets inside one `same_session_exact_recurrence_aggregate_only` scope
    - the first conflict categories stay fixed at:
      - `future_reviewed_memory_candidate_draft_vs_applied_effect`
      - `future_applied_reviewed_memory_effect_vs_applied_effect`
    - conflict visibility stays separate from rollback reversal, disable stop-apply, operator-audit repair, and cross-session counting
  - the current contract now also emits one read-only aggregate-level `reviewed_memory_conflict_contract` with:
    - one read-only aggregate-level `reviewed_memory_conflict_contract`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - `conflict_visibility_stage = contract_only_not_resolved`
    - `audit_trace_expectation = operator_visible_local_transition_required`
    - deterministic `defined_at = last_seen_at`
    - no resolver and no cross-session widening; the reviewed-memory apply path is now shipped above this contract layer
  - `operator_auditable_reviewed_memory_transition` is now fixed; the apply vocabulary is now shipped above this contract layer:
    - operator audit means one canonical local transition identity above the current conflict-visible scope
    - the first transition action vocabulary stays fixed at:
      - `future_reviewed_memory_apply`
      - `future_reviewed_memory_stop_apply`
      - `future_reviewed_memory_reversal`
      - `future_reviewed_memory_conflict_visibility`
    - current append-only `task_log` may mirror that trace, but it must not become the canonical reviewed-memory transition store
    - approval-backed save support, historical adjuncts, review acceptance, queue presence, and task-log replay alone must not create canonical transition state
    - operator audit stays separate from rollback reversal, disable stop-apply, conflict visibility, and cross-session counting
  - the current contract now also emits one read-only aggregate-level `reviewed_memory_transition_audit_contract` with:
    - one read-only aggregate-level `reviewed_memory_transition_audit_contract`
    - `audit_version = first_reviewed_memory_transition_identity_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - fixed `transition_action_vocabulary`
    - `transition_identity_requirement = canonical_local_transition_id_required`
    - `operator_visible_reason_boundary = explicit_reason_or_note_required`
    - `audit_stage = contract_only_not_emitted`
    - `audit_store_boundary = canonical_transition_record_separate_from_task_log`
    - `post_transition_invariants = aggregate_identity_and_contract_refs_retained`
    - deterministic `defined_at = last_seen_at`
    - no resolver and no cross-session widening; the reviewed-memory apply / emitted-transition vocabulary is now shipped above this planning-target layer
  - exact same-session unblock semantics are now fixed and shipped:
    - shipped boundary / rollback / disable / conflict / transition-audit objects remain `contract exists` only
    - none of those read-only objects counts as `satisfied` by itself
    - the first same-session unblock threshold stays binary and all-required:
      - current shipped `reviewed_memory_unblock_contract.unblock_status = blocked_all_required`
      - current shipped `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`
    - `reviewed_memory_planning_target_ref.target_label = eligible_for_reviewed_memory_draft_planning_only` remains the right narrow label, and it means draft planning only
    - the shipped readiness surface stays one read-only `reviewed_memory_unblock_contract`; the apply path and emitted transition record are now shipped above the readiness layer; cross-session counting remains later
  - the shipped capability outcome is now fixed:
    - keep the shipped `reviewed_memory_unblock_contract` as the blocked-threshold contract only
    - the shipped separate read-only `reviewed_memory_capability_status` now carries current `capability_outcome = unblocked_all_required`
    - the current truthful `unblocked_all_required` state requires one separate internal `reviewed_memory_capability_source_refs`, not current contract-object existence alone
    - that source family should stay same-session-only, exact-aggregate-scoped, and smaller than any later payload object
    - current implementation now also evaluates that internal source family and resolves all five same-aggregate refs: `boundary_source_ref`, `rollback_source_ref`, `disable_source_ref`, `conflict_source_ref`, and `transition_audit_source_ref`; the internal family now materializes with `source_status = all_required_sources_present` while staying payload-hidden
    - current implementation now also mints one exact payload-hidden canonical local proof-record/store entry for the current exact aggregate state inside the same-session internal `reviewed_memory_local_effect_presence_proof_record_store` boundary, and the proof-record helper can now consume only that exact same-aggregate entry while keeping `first_seen_at` alone, source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay outside the lower canonical proof-record layer
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_proof_boundary` helper for that same exact aggregate, and it now materializes one internal same-aggregate proof boundary only from one exact matching canonical local proof record/store entry while reusing the same `applied_effect_id` and `present_locally_at`; the helper still requires the aggregate's exact `first_seen_at` anchor and still treats source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay as smaller support or mirror traces
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from one exact matching proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source result only from one exact matching fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`
    - the exact local fact-source-instance layer now also stays fixed above that shared proof-boundary result and above one smaller canonical local proof record/store that first mints `applied_effect_id` plus same-instant `present_locally_at` for one exact same-session aggregate without implying any higher helper materialization
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event` helper for that same exact aggregate, and it now materializes one internal same-aggregate event result only from one exact matching fact-source result while reusing the same `applied_effect_id` and `present_locally_at`
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event_producer` helper for that same exact aggregate, and it now materializes one internal same-aggregate producer result only from one exact matching event result while reusing the same `applied_effect_id` and `present_locally_at`
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate event-source result only from one exact matching producer result while reusing the same `applied_effect_id` and `present_locally_at`
    - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_record` helper for that same exact aggregate, and it now materializes one internal same-aggregate source-consumer record only from one exact matching event-source helper result while reusing the same `applied_effect_id` and `present_locally_at`
    - current implementation now also evaluates one internal `reviewed_memory_applied_effect_target` helper for that same exact aggregate, and it now materializes one internal same-aggregate shared target only from one exact matching source-consumer helper result while reusing the same `applied_effect_id` and `present_locally_at`
    - current implementation now also evaluates one internal `reviewed_memory_reversible_effect_handle` helper for that same exact aggregate, and it now materializes one internal same-aggregate rollback-capability handle only from one exact matching shared target plus the current exact rollback contract
    - the exact rollback-capability backer is one now-materialized internal local `reviewed_memory_reversible_effect_handle` above the shipped `reviewed_memory_rollback_contract` and below the now-materialized basis, the now-shipped emitted transition record, and the now-shipped reviewed-memory apply result
    - that handle must stay same-session-only, exact-aggregate-scoped, and bound to the same supporting refs plus the same `boundary_source_ref`
    - the exact local target beneath that handle is one now-materialized shared internal `reviewed_memory_applied_effect_target` above no current payload surface and below the handle
    - that target stays same-session-only, exact-aggregate-scoped, and shared by the now-materialized rollback handle (and later disable handles when implemented) while each handle keeps its own matching contract ref
    - the exact local fact source beneath that raw helper is one now-materialized shared internal `reviewed_memory_local_effect_presence_fact_source` with `fact_source_version = first_same_session_reviewed_memory_local_effect_presence_fact_source_v1`, the same exact aggregate identity plus supporting refs, one matching `boundary_source_ref`, `effect_target_kind = applied_reviewed_memory_effect`, `fact_capability_boundary = local_effect_presence_only`, `fact_stage = presence_fact_available_local_only`, one local `applied_effect_id`, and one local `present_locally_at`
    - the exact local event above that fact source and beneath that producer helper is one now-materialized shared internal `reviewed_memory_local_effect_presence_event` with `event_version = first_same_session_reviewed_memory_local_effect_presence_event_v1`, the same exact aggregate identity plus supporting refs, one matching `boundary_source_ref`, `effect_target_kind = applied_reviewed_memory_effect`, `event_capability_boundary = local_effect_presence_only`, `event_stage = presence_observed_local_only`, one local `applied_effect_id`, and one local `present_locally_at`
    - the exact local effect-presence event source above that producer-helper result and beneath the current source-consumer helper is one now-materialized shared internal `reviewed_memory_local_effect_presence_event_source` beneath the current source-consumer helper and beneath the now-materialized target and handle
    - that event source now stays same-session-only, exact-aggregate-scoped, and now lets the current `reviewed_memory_local_effect_presence_record` helper materialize one shared source-consumer result only when one truthful local presence fact exists
    - one separate read-only `reviewed_memory_capability_basis` now stays above that source family and below the now-shipped emitted transition record
    - current implementation now also emits that basis layer during aggregate serialization because the full matching source family now exists, and `capability_outcome` is now `unblocked_all_required`
    - keep current `unblocked_all_required` smaller than enabled submit, emitted transition records, and reviewed-memory apply
  - readiness-target label narrowing is now fixed and shipped:
    - current shipped truth keeps `eligible_for_reviewed_memory_draft_planning_only` on `reviewed_memory_planning_target_ref.target_label`
    - current meaning stays reviewed-memory draft planning only
    - the current aggregate item now also exposes one additive `reviewed_memory_planning_target_ref` only
    - the cleanup-only pass has now removed the three duplicated target echo fields together
    - docs, payload, and tests now read planning-target meaning only from the shared ref
    - the post-cleanup compatibility-note question is now closed with no extra aftercare note; any later reopening should discuss later broader reviewed-memory machinery only, not a second partial rename or semantic widening
  - the first emitted-transition-record layer is now fixed and shipped:
    - keep the shipped `reviewed_memory_transition_audit_contract` contract-only
    - the first operator-visible `future_reviewed_memory_apply` trigger-source affordance is now implemented on one separate aggregate-level surface fed only by `recurrence_aggregate_candidates`
    - keep that surface inside the existing shell session stack as one section adjacent to `검토 후보`, not as a modal or dashboard
    - keep `review_queue_items` and source-message `candidate_review_record` separate from that aggregate-level trigger source
    - keep the first action label fixed at `검토 메모 적용 시작`
    - keep the blocked presentation visible but disabled while `blocked_all_required` / `contract_only_not_emitted` truth still holds; the submit boundary is now enabled when `capability_outcome = unblocked_all_required` and the user has entered a non-empty reason note; clicking the enabled submit now emits one aggregate-level `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` and persists it on the session under `reviewed_memory_emitted_transition_records`; reviewed-memory apply is NOT triggered
    - the emitted surface is one aggregate-level read-only `reviewed_memory_transition_record`
    - `transition_record_version = first_reviewed_memory_transition_record_v1`
    - one `canonical_transition_id`
    - one `transition_action` from the shipped fixed vocabulary
    - one `aggregate_identity_ref` plus exact supporting refs
    - one explicit `operator_reason_or_note`
    - `record_stage = emitted_record_only_not_applied`
    - `task_log_mirror_relation = mirror_allowed_not_canonical`
    - one local `emitted_at`
    - the first truthful emitted action is `future_reviewed_memory_apply` only
    - that emitted record requires truthful `unblocked_all_required` plus one real `canonical_transition_id`, one explicit `operator_reason_or_note`, and one local `emitted_at` created only at the enabled aggregate-card submit boundary
    - keep first-round `task_log` mirroring optional
    - keep that surface smaller than reviewed-memory apply, repeated-signal promotion, cross-session counting, and user-level memory
    - keep `task_log` mirror-only and never canonical
    - keep `transition-audit contract exists`, `operator-visible trigger-source layer exists`, `transition record emitted`, and `reviewed-memory apply result` as four separate layers
    - current implementation now also resolves one internal `disable_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_disable_contract` plus the shared `reviewed_memory_applied_effect_target`; it materializes only when both the disable contract and the applied-effect target truthfully match the same exact aggregate scope
    - current implementation now also resolves one internal `conflict_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_conflict_contract` plus the shared `reviewed_memory_applied_effect_target`; it materializes only when both the conflict contract and the applied-effect target truthfully match the same exact aggregate scope
    - current implementation now also resolves one internal `transition_audit_source_ref` for the same exact aggregate, backed by the existing `reviewed_memory_transition_audit_contract` plus the shared `reviewed_memory_applied_effect_target`; the internal `reviewed_memory_capability_source_refs` family is now complete with all five refs resolved
    - `reviewed_memory_capability_basis` is now materialized above the complete source family; `capability_outcome` is now `unblocked_all_required`
    - the truthful same-aggregate `unblocked_all_required` path above the already-materialized basis is now implemented, the enabled aggregate-card submit boundary is now open, and one truthful aggregate-level `reviewed_memory_transition_record` is now emitted at the enabled submit boundary; the reviewed-memory apply boundary is now also implemented: after emission the aggregate card shows a `검토 메모 적용 실행` button, clicking it POSTs to `/api/aggregate-transition-apply` which changes `record_stage` from `emitted_record_only_not_applied` to `applied_pending_result` and adds `applied_at`; the apply result is now also implemented: after the apply boundary the card shows `결과 확정`, clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = effect_active`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply is now also implemented: `적용 중단` changes `record_stage` to `stopped`, sets `apply_result.result_stage` to `effect_stopped`, and removes the effect from `reviewed_memory_active_effects`; reversal is now also implemented: `적용 되돌리기` changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; conflict-visibility is now also implemented: `충돌 확인` creates a separate `reviewed_memory_conflict_visibility_record` with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, `source_apply_transition_ref`, evaluated `conflict_entries`, and `conflict_entry_count`
- the first review outcome slice is now also implemented on top of that reviewable boundary:
  - current session payloads may expose one pending `review_queue_items` list
  - the existing shell may render one compact `검토 후보` section
  - one same-source-message `candidate_review_record` may now be recorded through `accept` only
  - the outcome stays reviewed-but-not-applied and does not open user-level memory
- keep durable candidates reviewable and separate from future user-level memory
- keep `edit` / `reject` / `defer`, reviewed-memory store, and user-level memory later than the shipped `accept` slice

### Milestone 7: Reviewable Durable Candidate Surface
- implemented first slice:
  - one local pending review queue surface for eligible `durable_candidate` records
  - one compact existing-shell `검토 후보` section fed only by current session `review_queue_items`
  - one same-source-message `candidate_review_record` may now be recorded through `accept`
  - the result stays reviewed-but-not-applied and the matching pending item leaves the queue
- still later inside this milestone:
  - keep the source-message-anchored `candidate_review_record` vocabulary wider than the shipped slice:
    - `edit`
    - `reject`
    - `defer`
  - keep scope suggestion fields later than the first review-action trace
  - define minimum scope, conflict, and rollback rules before future user-level memory
  - define a conservative default suggested-scope order and justification rule only when reviewed-memory planning opens
  - keep reviewed memory distinguishable from unreviewed durable candidates

### Milestone 8: Workflow-Grade Eval Assets
- create repeatable fixtures for document -> grounded brief quality
- define a named fixture-family matrix for correction reuse, approval friction, reviewed-vs-unreviewed trace, scope suggestion safety, rollback stop-apply, conflict / defer trace, and explicit-vs-save-support distinction
- define one eval-ready artifact core trace contract plus family-specific trace extensions
- keep correction reuse, approval friction, scope safety, reviewability / rollbackability, and trace completeness as separate evaluation axes
- keep approval-backed save as supporting evidence only and never treat it as content-quality improvement
- stage the rollout as manual placeholder -> service fixture -> unit helper -> e2e later
- measure whether stored memory reduces repeated mistakes on recurring document tasks without claiming model learning

## Later, After The Memory Phase

### Milestone 9: Approval-Gated Local Operator Foundation
- choose one narrow operator surface
- define action approval, audit, and rollback expectations
- keep local actions observable and reversible

### Why This Is Later
- Program operation should follow stable correction and preference memory, not precede it.
- The system must prove alignment on document work before it expands into action.

## Long-Term

### Milestone 10: Personalized Local Model Layer
- promote high-quality local traces into personalization assets
- evaluate whether a local adaptive model layer is justified
- keep deployment and rollback safe and measurable

### Preconditions
- enough grounded-brief correction pairs
- enough preference traces
- enough approval / rejection traces
- enough workflow-level eval data

## Next 3 Implementation Priorities

1. Keep the shipped read-only `reviewed_memory_boundary_draft` draft-only and do not widen it into readiness tracking or cross-session scope. The rollback / disable / conflict / operator-audit contracts and the reviewed-memory apply path are now shipped; boundary draft stays separate from apply result.
2. Keep `edit` / `reject` / `defer`, broader scope suggestion, merge-helper reopen, broader save-history replay, durable-candidate application, user-level memory, and broader operator work in later slices until the recurrence boundary and review boundary both stay small and non-confusing.
3. The reviewed-memory apply result, stop-apply (`future_reviewed_memory_stop_apply`), reversal (`future_reviewed_memory_reversal`), and conflict visibility (`future_reviewed_memory_conflict_visibility`) are now all implemented: after the effect is reversed (`record_stage = reversed`), the aggregate card shows a `충돌 확인` button; clicking it creates a separate conflict-visibility transition record with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, evaluated `conflict_entries` and `conflict_entry_count`, and `source_apply_transition_ref` linking back to the original apply record; the conflict visibility record is separate from the apply transition record and does not mutate it; aggregate identity, supporting refs, and contracts are retained. Keep repeated-signal promotion, broader durable promotion, and cross-session counting later than the now-shipped conflict visibility.

## Do Not Pull Forward

- generic web-chatbot expansion
- web-search-first positioning
- broad local program automation
- model training described as current product behavior
- cloud-first collaboration

## OPEN QUESTION

1. If `durable_candidate` later leaves the source-message surface, should it keep reusing the current source-message candidate id or mint a new durable-scope id at that boundary?
2. Should the default recurrence rule stay at two grounded briefs for every candidate category, or vary by category later?
3. Which exact local-store, stale-resolution, and reviewed-memory preconditions should be required before any cross-session recurrence aggregation opens?
4. Should the current fixed `confidence_marker = same_session_exact_key_match` remain enough until same-session unblock semantics can be satisfied truthfully, or should a later second conservative level be added only after that boundary opens?
5. Should the shipped `reviewed_memory_boundary_draft` keep repeating the fixed `reviewed_scope` label long term, or could a later normalization collapse it into `aggregate_identity_ref` plus supporting refs only?
6. Should later category-specific tuning vary approval-backed-save weight beyond the baseline weak-content / medium-path rule?
