# Task Backlog

## Current Product Identity

- shipped contract: local-first document assistant web MVP
- current release candidate: `app.web` browser shell only
- secondary mode: permission-gated web investigation
- next phase target: correction / approval / preference memory around one official `grounded brief`
- long-term north star: teachable local personal agent with later approval-gated local action
- operator tooling (`controller.server`, `pipeline_gui/`, `windows-launchers/`, `_data/`) remains outside the current release gate unless explicitly promoted

## Implemented

1. Local web shell and recent session timeline
2. File summary / document search / general chat modes
3. Active document context for follow-up questions
4. Approval-based save and reissue approval flow
5. Evidence/source panel and summary-range panel
6. Response-origin badges
7. Streaming progress and cancel
8. Response feedback capture with label/reason
9. PDF text-layer handling and OCR-not-supported guidance
10. Permission-gated web investigation with local history
11. Claim coverage and slot reinvestigation scaffolding
12. Playwright smoke coverage for the main browser loop (scenario 1 now also covers response copy button state with clipboard write verification, per-message timestamps, source filename in both quick-meta and transcript meta, note-path default-directory placeholder, and `문서 요약` source-type label in both quick-meta and transcript meta; browser file picker scenario now also covers source filename and `문서 요약` source-type label in both quick-meta and transcript meta; folder-search scenario now also covers `선택 결과 요약` source-type label and multi-source count-based metadata in both quick-meta and transcript meta, plus response detail preview panel alongside summary body with both cards' ordered labels, full-path tooltips, match badges, and snippet text content, and transcript preview panel with item count, both cards' ordered labels, full-path tooltips, match badges, and snippet text content; general chat scenario covers negative source-type label contract; dedicated claim-coverage panel rendering contract scenario with leading status tags and actionable hints)
13. Search-only response Playwright smoke coverage with `selected-copy` button visibility/click/notice/clipboard regression, full-path tooltip on preview card ordered labels, and match-type badge plus content snippet text
14. Corrected-save first bridge Playwright smoke coverage
15. Rejected content-verdict Playwright smoke coverage
16. Late flip after explicit original-draft save Playwright smoke coverage
17. Corrected-save late reject / re-correct Playwright smoke coverage
18. Candidate-linked explicit-confirmation Playwright smoke coverage
19. Dedicated `mock` Playwright smoke launch that clears inherited provider/model overrides and does not reuse an already running smoke-port server
20. Local read-only `review_queue_items` session projection plus compact existing-shell `검토 후보` section for eligible current `durable_candidate` items
21. First `accept`-only review action on the shipped queue with source-message `candidate_review_record`, pending queue removal, reviewed-but-not-applied semantics, and focused regression
22. Web-search history card header badge Playwright smoke coverage (answer-mode, verification-strength, source-role trust)
23. History-card `다시 불러오기` click reload Playwright smoke coverage (`WEB` badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source-role detail)
24. History-card latest-update `다시 불러오기` click reload Playwright smoke coverage (`WEB` badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source-role detail)
25. History-card `다시 불러오기` follow-up Playwright smoke coverage (response origin badge, answer-mode badge drift prevention)
26. History-card latest-update `다시 불러오기` follow-up Playwright smoke coverage (`WEB` badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source-role detail drift prevention)
27. History-card latest-update `다시 불러오기` noisy community source exclusion Playwright smoke coverage (negative `보조 커뮤니티` / `brunch` in response body, origin detail, and context box)
28. History-card entity-card `다시 불러오기` noisy single-source claim exclusion Playwright smoke coverage (`설명형 다중 출처 합의`, `백과 기반`, negative `출시일` / `2025` / `blog.example.com` in response body and origin detail, positive agreement-backed fact card, `blog.example.com` provenance in context box/source_paths)
29. History-card entity-card `다시 불러오기` dual-probe source-path + response-origin continuity Playwright smoke coverage (`pearlabyss.com/200`, `pearlabyss.com/300` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반`)
30. History-card latest-update `다시 불러오기` mixed-source source-path + response-origin continuity Playwright smoke coverage (`store.steampowered.com`, `yna.co.kr` in context box, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반`)
31. History-card latest-update single-source `다시 불러오기` verification-label continuity Playwright smoke coverage (`단일 출처 참고`, `보조 출처` in origin detail)
32. History-card latest-update news-only `다시 불러오기` verification-label continuity Playwright smoke coverage (`기사 교차 확인`, `보조 기사` in origin detail)
33. History-card latest-update news-only `다시 불러오기` source-path continuity Playwright smoke coverage (`hankyung.com`, `mk.co.kr` in context box)
34. History-card latest-update single-source `다시 불러오기` source-path continuity Playwright smoke coverage (`example.com/seoul-weather` in context box)
35. History-card latest-update single-source `다시 불러오기` follow-up response-origin continuity service + Playwright smoke coverage (`단일 출처 참고`, `보조 출처` drift prevention)
36. History-card latest-update news-only `다시 불러오기` follow-up response-origin continuity service + Playwright smoke coverage (`기사 교차 확인`, `보조 기사` drift prevention)
37. History-card entity-card `다시 불러오기` follow-up dual-probe source-path + response-origin continuity service + Playwright smoke coverage (`pearlabyss.com/200`, `pearlabyss.com/300` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift prevention)
38. History-card latest-update mixed-source `다시 불러오기` follow-up source-path + response-origin continuity service + Playwright smoke coverage (`store.steampowered.com`, `yna.co.kr` in context box, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` drift prevention)
39. History-card latest-update single-source `다시 불러오기` follow-up source-path continuity service + Playwright smoke coverage (`example.com/seoul-weather` in context box)
40. History-card latest-update news-only `다시 불러오기` follow-up source-path continuity service + Playwright smoke coverage (`hankyung.com`, `mk.co.kr` in context box)
41. History-card entity-card zero-strong-slot `다시 불러오기` reload verification-label continuity Playwright smoke coverage (downgraded `설명형 단일 출처`, `백과 기반`)
42. History-card entity-card zero-strong-slot `다시 불러오기` follow-up response-origin continuity service + Playwright smoke coverage (`설명 카드`, `설명형 단일 출처`, `백과 기반` drift prevention)
43. Entity-card zero-strong-slot click-reload follow-up response-origin continuity Playwright smoke + natural-reload service coverage (`설명 카드`, `설명형 단일 출처`, `백과 기반` drift prevention)
44. Entity-card zero-strong-slot browser natural-reload exact-field Playwright smoke coverage (`방금 검색한 결과 다시 보여줘` path)
45. Entity-card zero-strong-slot browser natural-reload follow-up response-origin continuity Playwright smoke coverage (natural reload + follow-up drift prevention)
46. Entity-card 붉은사막 검색 결과 browser natural-reload exact-field + noisy exclusion Playwright smoke coverage (`방금 검색한 결과 다시 보여줘` path, `출시일`/`2025`/`blog.example.com` 본문/detail 미노출, context box `blog.example.com` provenance 포함)
47. Entity-card dual-probe browser natural-reload source-path continuity Playwright smoke coverage (`pearlabyss.com` dual-probe URLs in context box)
48. Entity-card dual-probe browser natural-reload exact-field Playwright smoke coverage (`WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반`)
49. Entity-card dual-probe browser natural-reload follow-up source-path continuity service + Playwright smoke coverage (`pearlabyss.com` dual-probe URLs in context box)
50. Entity-card dual-probe browser natural-reload follow-up response-origin truth-sync service + Playwright smoke coverage (`WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift prevention)
51. Entity-card 붉은사막 browser natural-reload follow-up response-origin truth-sync service + Playwright smoke coverage (`WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` drift prevention)
52. Entity-card 붉은사막 browser natural-reload source-path plurality service + Playwright smoke coverage (`namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance in context box)
53. Entity-card 붉은사막 browser natural-reload follow-up source-path plurality service + Playwright smoke coverage (`namu.wiki`, `ko.wikipedia.org` in context box)
54. History-card entity-card `다시 불러오기` actual-search source-path plurality + response-origin continuity service + Playwright smoke coverage (`namu.wiki`, `ko.wikipedia.org` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`)
55. History-card entity-card `다시 불러오기` follow-up actual-search source-path plurality + response-origin continuity service + Playwright smoke coverage (`namu.wiki`, `ko.wikipedia.org` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` drift prevention)
56. History-card entity-card `다시 불러오기` second-follow-up actual-search source-path plurality + response-origin continuity service + Playwright smoke coverage (`namu.wiki`, `ko.wikipedia.org` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` drift prevention)
57. History-card entity-card `다시 불러오기` second-follow-up dual-probe source-path + response-origin continuity service + Playwright smoke coverage (`pearlabyss.com/200`, `pearlabyss.com/300` in context box, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift prevention)
58. Entity-card dual-probe natural-reload second-follow-up source-path + response-origin continuity service + Playwright smoke coverage (`pearlabyss.com` dual-probe URLs in context box)
59. Entity-card 붉은사막 natural-reload second-follow-up source-path + response-origin continuity service + Playwright smoke coverage (`namu.wiki`, `ko.wikipedia.org` in context box)
60. History-card latest-update mixed-source `다시 불러오기` second-follow-up source-path + response-origin continuity service + Playwright smoke coverage (`store.steampowered.com`, `yna.co.kr` in context box, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` drift prevention)
61. History-card latest-update single-source `다시 불러오기` second-follow-up source-path + response-origin continuity service + Playwright smoke coverage (`example.com/seoul-weather` in context box, `WEB` badge, `최신 확인`, `단일 출처 참고`, `보조 출처` drift prevention)
62. History-card latest-update news-only `다시 불러오기` second-follow-up source-path + response-origin continuity service + Playwright smoke coverage (`hankyung.com`, `mk.co.kr` in context box, `WEB` badge, `최신 확인`, `기사 교차 확인`, `보조 기사` drift prevention)
63. Latest-update mixed-source `방금 검색한 결과 다시 보여줘` natural-reload exact-field service + Playwright smoke coverage (`store.steampowered.com`, `yna.co.kr` in context box, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반`)
64. Latest-update single-source `방금 검색한 결과 다시 보여줘` natural-reload exact-field service + Playwright smoke coverage (`example.com/seoul-weather` in context box, `WEB` badge, `최신 확인`, `단일 출처 참고`, `보조 출처`)
65. Latest-update news-only `방금 검색한 결과 다시 보여줘` natural-reload exact-field service + Playwright smoke coverage (`hankyung.com`, `mk.co.kr` in context box, `WEB` badge, `최신 확인`, `기사 교차 확인`, `보조 기사`)
66. Latest-update mixed-source natural-reload follow-up source-path + response-origin continuity service + Playwright smoke coverage (`store.steampowered.com`, `yna.co.kr` in context box, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` drift prevention)
67. Latest-update mixed-source natural-reload second-follow-up source-path + response-origin continuity service + Playwright smoke coverage (`store.steampowered.com`, `yna.co.kr` in context box, `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` drift prevention)
68. Latest-update single-source natural-reload follow-up source-path + response-origin continuity service + Playwright smoke coverage (`example.com/seoul-weather` in context box, `WEB` badge, `최신 확인`, `단일 출처 참고`, `보조 출처` drift prevention)
69. Latest-update single-source natural-reload second-follow-up source-path + response-origin continuity service + Playwright smoke coverage (`example.com/seoul-weather` in context box, `WEB` badge, `최신 확인`, `단일 출처 참고`, `보조 출처` drift prevention)
70. Latest-update news-only natural-reload follow-up source-path + response-origin continuity service + Playwright smoke coverage (`hankyung.com`, `mk.co.kr` in context box, `WEB` badge, `최신 확인`, `기사 교차 확인`, `보조 기사` drift prevention)
71. Latest-update news-only natural-reload second-follow-up source-path + response-origin continuity service + Playwright smoke coverage (`hankyung.com`, `mk.co.kr` in context box, `WEB` badge, `최신 확인`, `기사 교차 확인`, `보조 기사` drift prevention)
72. Latest-update noisy-community natural-reload follow-up exclusion service + Playwright smoke coverage (`보조 커뮤니티`, `brunch` negative in origin detail, response body, context box + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention)
73. Latest-update noisy-community natural-reload second-follow-up exclusion service + Playwright smoke coverage (`보조 커뮤니티`, `brunch` negative in origin detail, response body, context box + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention)
74. History-card latest-update noisy-community click-reload follow-up exclusion service + Playwright smoke coverage (`보조 커뮤니티`, `brunch` negative in origin detail, response body, context box + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention)
75. History-card latest-update noisy-community click-reload second-follow-up exclusion service + Playwright smoke coverage (`보조 커뮤니티`, `brunch` negative in origin detail, response body, context box + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention)
76. Entity-card noisy single-source claim natural-reload follow-up exclusion + provenance truth-sync (`출시일`, `2025`, `blog.example.com` 본문/detail 미노출, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지, source_paths/context box에 `blog.example.com` provenance 포함)
77. Entity-card noisy single-source claim natural-reload second-follow-up exclusion + provenance truth-sync (`출시일`, `2025`, `blog.example.com` 본문/detail 미노출, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지, source_paths/context box에 `blog.example.com` provenance 포함)
78. History-card entity-card noisy single-source claim click-reload follow-up exclusion + provenance truth-sync (`출시일`, `2025`, `blog.example.com` 본문/detail 미노출, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지, source_paths/context box에 `blog.example.com` provenance 포함)
79. History-card entity-card noisy single-source claim click-reload second-follow-up exclusion + provenance truth-sync (`출시일`, `2025`, `blog.example.com` 본문/detail 미노출, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지, source_paths/context box에 `blog.example.com` provenance 포함)

## Current Phase In Progress

1. Improve entity-card web investigation quality
2. Prefer multi-source agreement over single-source noise
3. Reinvestigate weak or unresolved slots more effectively
4. Distinguish strong facts, single-source facts, and unresolved slots more clearly

## Why The Current Phase Must Stay Here

1. The document assistant loop is currently the most grounded and auditable workflow in the codebase.
2. Web investigation helps as a secondary mode, but it is still noisier and less deterministic than document work.
3. Program operation would widen scope before the product has stable correction and preference memory.

## Next 3 Implementation Priorities

1. Keep the shipped read-only aggregate-level `reviewed_memory_precondition_status` fixed at overall blocked-only and do not widen it into per-precondition satisfaction or eligibility transition before actual reviewed-memory apply result machinery exists.
2. Keep `edit` / `reject` / `defer`, broader scope suggestion, merge-helper reopen, broader save-history replay, durable-candidate application, user-level memory, and broader operator work in later slices until the recurrence boundary and review boundary both stay small and non-confusing.
3. The reviewed-memory apply result, stop-apply (`future_reviewed_memory_stop_apply`), reversal (`future_reviewed_memory_reversal`), and conflict visibility (`future_reviewed_memory_conflict_visibility`) are now all implemented: after the effect is reversed (`record_stage = reversed`), the aggregate card shows a `충돌 확인` button; clicking it creates a separate conflict-visibility transition record with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, evaluated `conflict_entries` and `conflict_entry_count`, and `source_apply_transition_ref`; the conflict visibility record is separate from the apply transition record. Keep repeated-signal promotion, broader durable promotion, and cross-session counting later than the now-shipped conflict visibility.

## Recently Landed Memory Foundation

1. `artifact_id` and `artifact_kind` are now attached to grounded-brief assistant messages.
2. The current assistant message is now the first raw response snapshot surface for that artifact anchor.
3. The same `artifact_id` is threaded through pending approval records and approval request / outcome traces, and current save-note approvals now also carry explicit `source_message_id` anchoring.
4. The same `artifact_id` is threaded through write-note and feedback-related task-log detail when applicable.
5. Current response and session serialization exposes artifact linkage without requiring a new UI flow.
6. Original grounded-brief assistant messages now also persist a normalized `original_response_snapshot`.
7. The same snapshot contract is exposed again through response and session serialization.
8. Legacy grounded-brief messages with artifact linkage plus evidence or summary chunks can be normalized into the same snapshot shape on session load.
9. Approval and task-log traces remain anchor-linked and do not duplicate the full snapshot blob.
10. Minimum `corrected_outcome` capture now records `accepted_as_is` on the original grounded-brief source message when save completion is explicit and successful.
11. Direct approved save responses can expose that same normalized `corrected_outcome` only when the response itself is the original grounded-brief source message.
12. Approval-execute system responses keep linkage-only behavior, while the original grounded-brief message receives the persisted `corrected_outcome`.
13. Reject / reissue approval traces now record one normalized `approval_reason_record` on approval-linked surfaces, while leaving `corrected_outcome` content-only.
14. Reissued pending approvals can expose the same `approval_reason_record` on the live approval payload, and task-log audit events mirror the same record.
15. Grounded-brief response surfaces now expose one multiline correction editor seeded with the current draft text.
16. Explicit correction submit now persists `corrected_text` and `corrected_outcome.outcome = corrected` on the original grounded-brief source message.
17. Unchanged correction submit is rejected as a no-op, and save approval remains a separate flow.
18. Current original-draft save approvals, approval execution, direct approved saves, and save/write traces now expose `save_content_source = original_draft` plus explicit `source_message_id`.
19. The correction area now also exposes a minimum corrected-save bridge action that stays always visible, remains disabled with helper copy until recorded `corrected_text` exists, consumes recorded `corrected_text` only, and issues a fresh approval with `save_content_source = corrected_text`.
20. Corrected-save approval execution now reuses the same `artifact_id` / `source_message_id` trace contract while preserving `corrected_outcome.outcome = corrected` on the source message, and approval/save-result wording now describes the body as the request-time frozen snapshot.
21. Focused service and smoke regression now cover message / approval / task-log linkage plus snapshot normalization, minimum accepted-as-is capture, minimum approval-reason capture, explicit corrected-text submission, the save-target discriminator, the save-trace source-message anchor, the first corrected-save bridge path, the corrected-save snapshot wording contract, the shipped `내용 거절` content-verdict browser path including same-card reject-note update, the late-flip-after-save browser path where saved history remains while the latest content verdict changes, and the longer corrected-save history chain where a saved corrected snapshot remains while later reject and re-correct move the latest state separately.
22. Grounded-brief source messages can now also persist one candidate-linked `candidate_confirmation_record`, and the response card can record it through one small explicit reuse-confirmation action that stays separate from save approval and from the current `session_local_candidate` object itself.
23. Current session payloads can now also expose one pending `review_queue_items` list, the existing shell can render it as one compact `검토 후보` section, and one `accept` action can record source-message `candidate_review_record` while leaving the result reviewed-but-not-applied.
24. Current session payloads can now also expose one optional top-level read-only `recurrence_aggregate_candidates` projection derived only from current same-session serialized source-message `candidate_recurrence_key` records, emitted only for exact identity matches across at least two distinct grounded-brief anchors, and kept separate from `review_queue_items`, promotion, and user-level memory.
25. Current same-session `recurrence_aggregate_candidates` items can now also expose one read-only `aggregate_promotion_marker` that keeps the aggregate explicitly blocked with `promotion_basis = same_session_exact_recurrence_aggregate`, `promotion_eligibility = blocked_pending_reviewed_memory_boundary`, `reviewed_memory_boundary = not_open`, fixed `marker_version`, and deterministic `derived_at = last_seen_at`.
26. Current same-session `recurrence_aggregate_candidates` items can now also expose one read-only `reviewed_memory_precondition_status` object that keeps the same blocked state explicit with `status_version = same_session_reviewed_memory_preconditions_v1`, `overall_status = blocked_all_required`, `all_required = true`, ordered fixed precondition ids, and deterministic `evaluated_at = last_seen_at`.
27. The existing shell can now also render one separate aggregate-level read-only `검토 메모 적용 후보` section fed only by current `recurrence_aggregate_candidates`, shown adjacent to `검토 후보` only when aggregates exist; the `검토 메모 적용 시작` submit boundary is now enabled when `capability_outcome = unblocked_all_required` and the user has entered a non-empty reason note (visible but disabled while blocked or while note is empty); clicking the enabled submit now emits one `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` and persists it under `reviewed_memory_emitted_transition_records`; after emission the same aggregate card shows `검토 메모 적용 실행`, and clicking that apply boundary changes `record_stage` to `applied_pending_result` with `applied_at` added; after the apply boundary the card shows `결과 확정`, and clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint.

## Next Phase Design Backlog

1. Keep the corrected-save bridge action always visible with disabled helper copy whenever no recorded correction exists.
2. Keep approval preview and approval execution tied to the save target explicitly chosen at request time.
3. Reuse the shipped `save_content_source = original_draft | corrected_text` contract if later corrected-save variants widen.
4. Keep using recorded `corrected_text`, not unsaved editor state, if later corrected-save variants create fresh approval snapshots.
5. Keep treating `approval_id` plus the frozen approval `note_text` / preview body as the first immutable corrected-save snapshot identity; do not add a separate `snapshot_id` in the first slice.
6. Keep the shipped explicit response-card content-verdict action for `rejected` outside the approval surface, and do not infer reject from no-save, retry, feedback `incorrect`, or approval reject.
7. Keep reusing the existing content-outcome envelope plus source-message `content_reason_record` for `rejected` instead of adding a separate reject store.
8. Keep the first reject-reason contract intentionally narrow:
  - `reason_scope = content_reject`
  - `reason_label = explicit_content_rejection`
  - optional `reason_note` only through the shipped response-card reject-note surface and it may stay absent
9. Keep approval reject labels and approval-linked `approval_reason_record` separate from the content-verdict path.
10. Keep the shipped reject-note UX visible only while the latest source-message outcome remains `rejected`, and keep it as one short inline response-card note surface rather than a new modal or panel.
11. When that note is recorded, update the same `content_reason_record.reason_note` in place, append the dedicated content-linked task-log event `content_reason_note_recorded`, and clear the stale note again when later correction or explicit save supersedes `rejected`.
12. Keep blank note submit invalid and do not reinterpret it as clear while the current shipped note surface stays add/update-only.
13. If a later manual clear refinement is needed, keep it inside the same response-card content-verdict box, show it only when a non-empty note exists, and make it clear only `content_reason_record.reason_note` rather than revoking `rejected`.
14. If that future clear lands, keep the same `content_reason_record` object with scope / label / anchor fields, refresh `content_reason_record.recorded_at`, preserve `corrected_outcome.recorded_at`, and append a separate content-linked clear event such as `content_reason_note_cleared`.
15. Keep the shipped first `session_local_memory_signal` as one read-only, source-message-anchored working summary keyed by `artifact_id` + `source_message_id`.
16. Keep that first signal derived from current persisted session state rather than a separate memory store or task-log replay.
17. Keep the shipped signal axes separate:
  - latest content state from `corrected_outcome`, current `corrected_text`, and current `content_reason_record`
  - latest approval friction from approval-linked `approval_reason_record`
  - latest save linkage from `save_content_source`, optional `approval_id`, and optional `saved_note_path`
18. Keep the first shipped signal thin and linkage-oriented:
  - no saved body copy
  - no inferred preference statement
  - no cross-artifact aggregation
19. Keep the shipped `superseded_reject_signal` read-only, source-message-anchored, and separate from `session_local_memory_signal.content_signal`.
20. Keep that helper audit-derived only from same-anchor `content_verdict_recorded` and `content_reason_note_recorded` traces.
21. Keep that helper narrow:
  - no saved body copy
  - no approval preview body copy
  - no approval-friction labels
  - no inferred preference statements
  - no cross-artifact aggregate
  - no list-based mini history
22. Omit the replayed note when same-anchor note association is ambiguous instead of guessing.
23. Keep save-axis `latest_approval_id` replay separate from the content-side helper, and keep the shipped first slice limited to same-anchor `write_note`-backed historical identity only.
24. Keep `write_note`-only replay as the default save-axis rule unless a concrete insufficiency appears in focused operator use or regression.
25. If a later refinement opens `approval_granted`, keep it corroboration-only:
  - same anchor only
  - same `approval_id` only
  - never enough by itself to emit `historical_save_identity_signal`
26. Do not widen that corroboration question into pending-approval replay, broad save-history replay, or a list/feed viewer.
27. Keep the shipped first `session_local_candidate` separate from:
  - `session_local_memory_signal`
  - `superseded_reject_signal`
  - `historical_save_identity_signal`
  - future `durable_candidate`
28. Keep the shipped first candidate family narrow:
  - `correction_rewrite_preference`
  - primary basis = explicit original-vs-corrected pair on the same source message
29. Keep the shipped first `session_local_candidate.statement` fixed and deterministic:
  - `explicit rewrite correction recorded for this grounded brief`
  - do not open a rewrite-summary helper in the first slice
30. Keep repeated same-session `correction_rewrite_preference` drafts per-source-message for now:
  - do not merge by `candidate_family` alone
  - the current fixed statement and support refs do not yet provide a truthful same-preference merge key
31. Keep the shipped first post-key aggregation surface to one optional top-level session-local read-only `recurrence_aggregate_candidates` projection:
  - same session only
  - exact recurrence-key identity only
  - at least two distinct source-message anchors
  - never overwrite source-message `session_local_candidate`
  - never replace source-message `candidate_recurrence_key`
  - never imply `durable_candidate`, review outcome, or user-level memory
32. Keep replay helpers as supporting context only for that first candidate family; do not let them become the primary extraction source.
33. Keep approval-backed save as supporting evidence only for candidate normalization:
  - never sole basis
  - never implicit content confirmation
  - never broader-scope justification
34. Keep the first candidate evidence strength conservative:
  - `explicit_single_artifact`
  - current save support may add `session_local_memory_signal.save_signal` to `supporting_signal_refs`, but it does not raise `evidence_strength` in the first slice
35. Expand reject / reissue labels only when a truthful user-input surface exists for those distinctions.
36. Keep the current shipped `session_local_candidate` promotion-ineligible in its own object shape:
  - no `durable_candidate` nested under `session_local_candidate`
  - no eligibility from `candidate_family` alone
  - no eligibility from approval-backed save or historical adjuncts
37. Keep the shipped first `durable_candidate` contract separate from `session_local_candidate`:
  - `candidate_id`
  - `candidate_scope = durable_candidate`
  - `candidate_family`
  - `statement`
  - `supporting_artifact_ids`
  - `supporting_source_message_ids`
  - `supporting_signal_refs`
  - `supporting_confirmation_refs`
  - `evidence_strength`
  - `promotion_basis`
  - `promotion_eligibility`
  - `has_explicit_confirmation`
  - timestamps only
38. Keep the first explicit-confirmation promotion path source-message-anchored and read-only:
  - same source message only
  - same `candidate_id` and `candidate_updated_at` only
  - current persisted session state stays canonical
  - task-log remains audit-only
  - current first slice reuses the source-message candidate id while the projection stays source-message-anchored
  - explicit confirmation yields `promotion_eligibility = eligible_for_review`, not reviewed memory
39. Defer repeated-signal promotion until a truthful recurrence key exists beyond family alone:
  - first aggregation boundary before promotion = one same-session-only read-only `recurrence_aggregate_candidates`
  - at least two distinct source-message candidates
  - merge key derived from the explicit corrected pair itself
40. Keep the first truthful recurrence-key contract smaller than repeated-signal promotion itself:
  - current implemented draft name = `candidate_recurrence_key`
  - source-message anchored and read-only
  - derived only from normalized explicit original-vs-corrected pair
  - identity carried by `candidate_family` + `key_version` + `normalized_delta_fingerprint`
  - never emitted from `candidate_family` alone
  - never emitted from fixed statement text alone
  - never emitted from approval-backed save alone
  - never emitted from task-log replay alone
41. Keep the first recurrence-key envelope deterministic and local-only:
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
42. Let review acceptance strengthen repeated-signal evidence only after the key exists:
  - `candidate_review_record` may raise confidence later
  - it must not replace the recurrence key
  - queue presence alone must not replace the recurrence key
  - the first same-session aggregate may consume it only as confidence support, not as identity basis
43. Keep the shipped local read-only review queue fed only by `promotion_eligibility = eligible_for_review` durable candidates and do not widen it into a second canonical durable surface.
44. Reuse the current source-message anchor for the first review-outcome trace through one optional `candidate_review_record`:
  - same `artifact_id`
  - same `source_message_id`
  - same `candidate_id`
  - same `candidate_updated_at`
  - no second durable store
45. Define the four-action vocabulary now, but keep the first implementation slice narrower:
  - `accept | edit | reject | defer` are the contract-level review actions
  - implement `accept` only first
  - keep that first accept path reviewed-but-not-applied
46. Keep the first review-action trace smaller than later reviewed-memory planning:
  - fixed `review_scope = source_message_candidate_review`
  - optional `reviewed_statement` only for later `edit`
  - keep `proposed_scope`, `scope_candidates_considered`, and `scope_suggestion_reason` for later reviewed-memory work
47. Keep `durable_candidate` separate from future reviewed memory and future user-level memory until review / scope / rollback rules exist.
48. Treat approval-backed save as supporting evidence only, distinct from explicit confirmation and distinct from content-correction signals.
49. Define one eval-ready artifact core trace contract before claiming workflow-grade fixtures.
50. Name fixture families for correction reuse, approval friction, reviewed-vs-unreviewed trace, scope suggestion safety, rollback stop-apply, conflict / defer trace, and explicit-vs-save-support distinction.
51. Add regression fixtures for repeated document tasks that test conservative scope suggestion, correction reuse, rollback stop-apply, conflict visibility, and support distinction.
52. Stage future coverage as manual placeholder first, service fixtures next, unit helpers after that, and e2e only when review / rollback UI exists.
53. Keep the shipped same-session `recurrence_aggregate_candidates` promotion-ineligible:
  - exact aggregate identity remains necessary but insufficient for repeated-signal promotion
  - no post-aggregate apply path, no reviewed-memory candidate store, and no cross-session counting in the current contract
54. Keep the first post-aggregate reviewed-memory boundary explicit and separate:
  - `candidate_review_record` remains one source-message reviewed-but-not-applied trace
  - `recurrence_aggregate_candidates` remains one same-session grouping surface
  - reviewed memory remains later than rollback, disable, conflict, and operator-audit rules
55. Keep the shipped post-aggregate surface as one read-only aggregate-level promotion-eligibility marker only:
  - `promotion_basis = same_session_exact_recurrence_aggregate`
  - `promotion_eligibility = blocked_pending_reviewed_memory_boundary`
  - `reviewed_memory_boundary = not_open`
56. Keep review acceptance, approval-backed save, historical adjuncts, queue presence, fixed statement text, and task-log replay out of post-aggregate promotion identity.
57. Keep the same-session aggregate unblock contract exact and all-required:
  - `reviewed_memory_boundary_defined`
  - `rollback_ready_reviewed_memory_effect`
  - `disable_ready_reviewed_memory_effect`
  - `conflict_visible_reviewed_memory_scope`
  - `operator_auditable_reviewed_memory_transition`
58. Keep each unblock precondition truthful and separate:
  - rollback reverses later reviewed-memory effect, not source-message correction history
  - disable stops later apply, not candidate deletion
  - conflict visibility means reviewed-signal conflict across aggregates within the same reviewed scope, not only same-source edit conflict
  - operator-audit means explicit operator-visible transition trace, not task-log promoted to canonical
59. Require all unblock preconditions before any same-session aggregate can leave `blocked_pending_reviewed_memory_boundary`:
  - partial satisfaction may later surface read-only only
  - same-session unblock must not auto-open cross-session counting
60. Keep the shipped aggregate-level `reviewed_memory_precondition_status` object narrow and blocked-only:
  - no per-precondition satisfaction booleans yet
  - no payload-visible reviewed-memory store and no payload-visible proof-record or proof-boundary surface
  - no reviewed-memory apply
  - no repeated-signal promotion
  - no user-level memory
61. Fix `reviewed_memory_boundary_defined` to one first narrow reviewed scope only:
  - `same_session_exact_recurrence_aggregate_only`
  - no reviewed-scope enum in the first boundary slice
  - no rename of `candidate_review_record`, `recurrence_aggregate_candidates`, or the current blocked marker into reviewed memory
62. Current same-session `recurrence_aggregate_candidates` items may now also expose one read-only `reviewed_memory_boundary_draft`:
  - `boundary_version = fixed_narrow_reviewed_scope_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - one `aggregate_identity_ref`
  - `supporting_source_message_refs`
  - `supporting_candidate_refs`
  - optional `supporting_review_refs`
  - `boundary_stage = draft_not_applied`
  - deterministic `drafted_at = last_seen_at`
63. Keep the shipped `reviewed_memory_boundary_draft` narrower than reviewed-memory store/apply:
  - no readiness or satisfaction tracker
  - no apply result
  - no cross-session scope
  - do not widen into cross-session counting or user-level memory
64. Fix `rollback_ready_reviewed_memory_effect` to one exact future rollback target only:
  - rollback means later reviewed-memory effect reversal, not source-message correction-history rewind
  - the first rollback target stays one later applied reviewed-memory effect inside `same_session_exact_recurrence_aggregate_only`
  - the shipped `reviewed_memory_boundary_draft` remains a scope draft and basis ref, not the rollback target
65. Keep rollback narrower than delete or rewrite semantics:
  - rollback must not delete `candidate_review_record`
  - rollback must not delete `candidate_recurrence_key`
  - rollback must not rewrite `recurrence_aggregate_candidates` identity history
  - boundary-draft deletion must not become canonical rollback
66. Keep rollback output boundaries exact:
  - aggregate identity, supporting refs, boundary draft, and operator-visible audit trace must remain after rollback
  - only later applied reviewed-memory influence may deactivate
  - current append-only `task_log` may mirror rollback trace but must not become the canonical rollback store
67. Keep rollback separate from disable, conflict visibility, and operator audit:
  - rollback = reversal of already-applied reviewed-memory effect
  - disable = later stop-apply machinery
  - conflict visibility and operator-audit remain separate preconditions and must not be implied by rollback target definition alone
68. Current same-session `recurrence_aggregate_candidates` items may now also expose one read-only `reviewed_memory_rollback_contract`:
  - `rollback_version = first_reviewed_memory_effect_reversal_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - one `aggregate_identity_ref`
  - exact supporting refs
  - `rollback_target_kind = future_applied_reviewed_memory_effect_only`
  - `rollback_stage = contract_only_not_applied`
  - `audit_trace_expectation = operator_visible_local_transition_required`
  - deterministic `defined_at = last_seen_at`
69. Keep the shipped `reviewed_memory_rollback_contract` narrower than reviewed-memory store/apply:
  - it must remain contract-only and read-only
  - it must not become a rollback state machine
  - it must not widen into cross-session scope
70. Fix `disable_ready_reviewed_memory_effect` to one exact future stop-apply target only:
  - disable means later reviewed-memory effect stop-apply, not source-message correction-history rewrite
  - the first disable target stays one later applied reviewed-memory effect inside `same_session_exact_recurrence_aggregate_only`
  - the shipped `reviewed_memory_boundary_draft` and shipped `reviewed_memory_rollback_contract` remain basis refs, not the disable target
71. Keep disable narrower than delete or reversal semantics:
  - disable must not delete `candidate_review_record`
  - disable must not delete `candidate_recurrence_key`
  - disable must not rewrite `recurrence_aggregate_candidates` identity history
  - disable must not be treated as rollback reversal
72. Keep disable output boundaries exact:
  - aggregate identity, supporting refs, boundary draft, rollback contract, and operator-visible audit trace must remain after disable
  - only later applied reviewed-memory influence may become inactive
  - current append-only `task_log` may mirror disable trace but must not become the canonical disable store
73. Keep disable separate from rollback, conflict visibility, and operator audit:
  - disable = stop-apply of already-applied reviewed-memory effect
  - rollback = reversal of already-applied reviewed-memory effect
  - conflict visibility and operator-audit remain separate preconditions and must not be implied by disable target definition alone
74. Current same-session `recurrence_aggregate_candidates` items may now also expose one read-only `reviewed_memory_disable_contract`:
  - one `reviewed_memory_disable_contract`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - `disable_target_kind = future_applied_reviewed_memory_effect_only`
  - `disable_stage = contract_only_not_applied`
  - `effect_behavior = stop_apply_without_reversal`
  - `audit_trace_expectation = operator_visible_local_transition_required`
  - deterministic `defined_at = last_seen_at`
75. Keep the shipped `reviewed_memory_disable_contract` narrower than reviewed-memory store/apply:
  - it must remain contract-only and read-only
  - it must not become a disable state machine
  - it must not widen into cross-session scope
76. Fix `conflict_visible_reviewed_memory_scope` to one exact same-session visibility boundary only:
  - conflict visibility means operator-visible read-only exposure of competing reviewed-memory targets inside `same_session_exact_recurrence_aggregate_only`
  - it must remain tied to one current aggregate identity plus its exact supporting refs
  - it must stay broader than same-source-message edit conflict alone without widening into cross-session scope
77. Keep the first conflict categories fixed and narrow:
  - `future_reviewed_memory_candidate_draft_vs_applied_effect`
  - `future_applied_reviewed_memory_effect_vs_applied_effect`
  - current `candidate_review_record` must not become a conflict object by itself
78. Keep conflict visibility narrower than resolution mechanics:
  - it must not auto-resolve
  - it must not auto-disable
  - it must not auto-rollback
  - it must not auto-apply
79. Keep conflict visibility separate from current shipped contracts:
  - current `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, and `reviewed_memory_disable_contract` remain basis refs or neighboring contracts, not the conflict object itself
  - current append-only `task_log` may mirror conflict trace but must not become the canonical conflict store
80. Current same-session `recurrence_aggregate_candidates` items may now also expose one read-only `reviewed_memory_conflict_contract`:
  - one `reviewed_memory_conflict_contract`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - `conflict_target_categories`
  - `conflict_visibility_stage = contract_only_not_resolved`
  - `audit_trace_expectation = operator_visible_local_transition_required`
  - deterministic `defined_at = last_seen_at`
81. Keep the shipped `reviewed_memory_conflict_contract` narrower than reviewed-memory store/apply:
  - it must remain contract-only and read-only
  - it must not become a conflict resolver
  - it must not widen into cross-session counting
82. Fix `operator_auditable_reviewed_memory_transition` to one exact local transition-trace contract only:
  - operator audit must remain separate from current evidence traces and separate from conflict visibility itself
  - current append-only `task_log` may mirror the trace but must not become the canonical reviewed-memory audit store
83. Keep operator-audit target boundary exact:
  - the first operator-auditable transition scope stays `same_session_exact_recurrence_aggregate_only`
  - the first transition action vocabulary stays fixed at:
    - `future_reviewed_memory_apply`
    - `future_reviewed_memory_stop_apply`
    - `future_reviewed_memory_reversal`
    - `future_reviewed_memory_conflict_visibility`
84. Keep operator audit narrower than state or resolver mechanics:
  - it must not auto-apply
  - it must not auto-disable
  - it must not auto-rollback
  - it must not auto-resolve
  - it must not auto-repair
85. Keep operator audit separate from current shipped contracts:
  - current `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, and `reviewed_memory_conflict_contract` remain basis refs or neighboring contracts, not transition results
  - current `candidate_review_record` must not become the transition record by itself
  - approval-backed save support, historical adjuncts, review acceptance, queue presence, and task-log replay alone must not create canonical transition state
86. Current same-session `recurrence_aggregate_candidates` items may now also expose one read-only `reviewed_memory_transition_audit_contract`:
  - one `reviewed_memory_transition_audit_contract`
  - `audit_version = first_reviewed_memory_transition_identity_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - `transition_action_vocabulary`
  - `transition_identity_requirement = canonical_local_transition_id_required`
  - `operator_visible_reason_boundary = explicit_reason_or_note_required`
  - `audit_stage = contract_only_not_emitted`
  - `audit_store_boundary = canonical_transition_record_separate_from_task_log`
  - `post_transition_invariants = aggregate_identity_and_contract_refs_retained`
  - deterministic `defined_at = last_seen_at`
87. Keep the shipped `reviewed_memory_transition_audit_contract` narrower than reviewed-memory store/apply:
  - it must remain contract-only and read-only
  - it must not become a transition state machine
  - it must not widen into cross-session counting
88. Keep current shipped boundary / rollback / disable / conflict / transition-audit objects separated from same-session unblock satisfaction:
  - each current object means only `contract exists`
  - object existence must not count as `satisfied`
  - approval-backed save support, historical adjuncts, review acceptance, queue presence, and `task_log` mirror existence must remain outside satisfaction basis
89. Fix first same-session unblock semantics as binary and all-required:
  - unblock may occur only when all five reviewed-memory preconditions are satisfied through later machinery
  - the first widened vocabulary should stay binary:
    - `blocked_all_required`
    - `unblocked_all_required`
  - partial satisfaction remains blocked-only in the current phase
90. Keep the first unblocked target narrower than apply:
  - keep `reviewed_memory_planning_target_ref.target_label = eligible_for_reviewed_memory_draft_planning_only`
  - interpret it as reviewed-memory draft planning only for one exact same-session aggregate
  - do not treat it as emitted transition record, reviewed-memory apply result, repeated-signal promotion, or cross-session counting
91. Keep source-message review, approval-backed save, and `task_log` separate from aggregate-level unblock satisfaction:
  - `candidate_review_record` may support confidence only and must not replace aggregate-level readiness
  - `review_queue_items` presence must not act as readiness
  - approval-backed save remains supporting evidence only
  - `task_log` remains mirror / appendix only, not canonical transition satisfaction
92. The shipped readiness surface should stay one read-only `reviewed_memory_unblock_contract`:
  - exact `required_preconditions`
  - binary `unblock_status`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `partial_state_policy = partial_states_not_materialized`
  - deterministic `evaluated_at`
  - current object existence still does not mean satisfied capability outcome
93. The shipped separate satisfaction surface should stay one read-only `reviewed_memory_capability_status`:
  - `capability_version = same_session_reviewed_memory_capabilities_v1`
  - exact `required_preconditions`
  - `capability_outcome`
    - current shipped state = `unblocked_all_required`
    - no later wider capability-outcome state is currently defined in the MVP slice
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `partial_state_policy = partial_states_not_materialized`
  - deterministic `evaluated_at`
  - do not overwrite the shipped `reviewed_memory_unblock_contract`
  - keep this surface smaller than emitted transition records and reviewed-memory apply
  - current truthful `unblocked_all_required` requires one separate internal `reviewed_memory_capability_source_refs`:
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
    - deterministic `evaluated_at`
    - keep it internal and additive, not a shipped payload object
  - current truthful `unblocked_all_required` also requires one separate now-materialized read-only `reviewed_memory_capability_basis` above that source family:
    - `basis_version = same_session_reviewed_memory_capability_basis_v1`
    - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - exact `required_preconditions`
    - `basis_status = all_required_capabilities_present`
    - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
    - deterministic `evaluated_at`
  - current implementation may now evaluate that internal source family for the same aggregate, and it now resolves one real `boundary_source_ref` backer for the same exact aggregate against the `검토 메모 적용 시작` trigger affordance
  - current implementation now also materializes one internal same-aggregate `reviewed_memory_reversible_effect_handle` only from one exact matching shared target plus the current exact rollback contract, and it now resolves `rollback_source_ref` only as one exact ref to that same handle
  - current implementation now also mints one exact payload-hidden canonical local proof-record/store entry for the current exact aggregate state inside the same-session internal `reviewed_memory_local_effect_presence_proof_record_store` boundary, and the proof-record helper can now consume only that exact same-aggregate entry while keeping `first_seen_at` alone, source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay outside the lower canonical proof-record layer
  - current implementation now also materializes one internal `reviewed_memory_local_effect_presence_proof_boundary` helper result for that same exact aggregate only from that exact same-aggregate proof-record/store entry while reusing the same `applied_effect_id` plus `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source_instance` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source-instance result only from one exact matching proof-boundary result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_fact_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate fact-source result only from one exact matching fact-source-instance result while reusing the same `applied_effect_id` and `present_locally_at`
  - the exact later local proof boundary beneath that fact-source-instance helper now stays one shared internal `reviewed_memory_local_effect_presence_proof_boundary` above one smaller canonical local proof record/store that mints one exact payload-hidden `applied_effect_id` plus same-instant `present_locally_at` for the current exact aggregate state, and the fact-source-instance layer now stays fixed directly above that proof boundary
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event` helper for that same exact aggregate, and it now materializes one internal same-aggregate event result only from one exact matching fact-source result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event_producer` helper for that same exact aggregate, and it now materializes one internal same-aggregate producer result only from one exact matching event result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_event_source` helper for that same exact aggregate, and it now materializes one internal same-aggregate event-source result only from one exact matching producer result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_local_effect_presence_record` helper for that same exact aggregate, and it now materializes one internal same-aggregate source-consumer record only from one exact matching event-source helper result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_applied_effect_target` helper for that same exact aggregate, and it now materializes one internal same-aggregate shared target only from one exact matching source-consumer helper result while reusing the same `applied_effect_id` and `present_locally_at`
  - current implementation now also evaluates one internal `reviewed_memory_reversible_effect_handle` helper for that same exact aggregate, and it now materializes one internal same-aggregate rollback-capability handle only from one exact matching shared target plus the current exact rollback contract
  - the exact future rollback-capability backer for that unresolved ref should stay one internal local `reviewed_memory_reversible_effect_handle`:
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
    - deterministic `defined_at`
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
    - deterministic `present_locally_at`
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
    - deterministic `present_locally_at`
  - the exact later local event above that fact source and beneath that producer helper should stay one shared internal `reviewed_memory_local_effect_presence_event`:
    - `event_version = first_same_session_reviewed_memory_local_effect_presence_event_v1`
    - `event_scope = same_session_exact_recurrence_aggregate_only`
    - one `aggregate_identity_ref`
    - exact supporting refs
    - one matching `boundary_source_ref`
    - `effect_target_kind = applied_reviewed_memory_effect`
    - `event_capability_boundary = local_effect_presence_only`
    - `event_stage = presence_observed_local_only`
    - one local `applied_effect_id`
    - deterministic `present_locally_at`
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
    - deterministic `present_locally_at`
  - the current raw-event helper `reviewed_memory_local_effect_presence_event` now materializes only from one exact matching `reviewed_memory_local_effect_presence_fact_source`
  - the current producer helper `reviewed_memory_local_effect_presence_event_producer` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event`
  - the current event-source helper `reviewed_memory_local_effect_presence_event_source` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event_producer`
  - the current source-consumer helper `reviewed_memory_local_effect_presence_record` now materializes only from one exact matching `reviewed_memory_local_effect_presence_event_source`
  - the current target helper now materializes only from that exact matching source-consumer helper result
  - that target should stay shared by later rollback and later disable handles while each handle still keeps its own contract linkage and capability meaning
  - the full internal `reviewed_memory_capability_source_refs` family is now complete with all five refs resolved
  - current implementation now probes and emits this basis layer during aggregate serialization because one truthful matching capability source family exists for the same exact aggregate
  - current contract-object existence alone, `candidate_review_record`, queue presence, approval-backed save support, historical adjuncts, and `task_log` replay alone must not materialize that rollback-capability handle, that shared applied-effect target, the capability source family, that basis object, or `unblocked_all_required`
  - capability-path opening alone must not mint `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, or `reviewed_memory_transition_record`
94. Keep the shipped planning-only target centralized on one shared aggregate-level ref:
  - the current aggregate item exposes one additive `reviewed_memory_planning_target_ref`
  - shipped shape:
    - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
    - `target_label = eligible_for_reviewed_memory_draft_planning_only`
    - `target_scope = same_session_exact_recurrence_aggregate_only`
    - `target_boundary = reviewed_memory_draft_planning_only`
    - deterministic `defined_at = last_seen_at`
  - the shared ref is now the only current planning-target source
  - the duplicated target echo fields have now been removed together in one cleanup-only pass
  - do not reintroduce one or two fallback target strings in later slices
  - do not add a separate post-cleanup compatibility note as a fallback surface; ordinary current docs and ordinary `/work` closeouts should keep only the shared-ref-only truth
95. The first emitted-transition-record layer is now implemented as one separate aggregate-level read-only surface (shipped):
  - one `reviewed_memory_transition_record`
  - `transition_record_version = first_reviewed_memory_transition_record_v1`
  - one `canonical_transition_id`
  - one `transition_action` from the shipped fixed vocabulary
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - one `aggregate_identity_ref`
  - exact supporting refs
  - one explicit `operator_reason_or_note`
  - `record_stage = emitted_record_only_not_applied`
  - `task_log_mirror_relation = mirror_allowed_not_canonical`
  - one local `emitted_at`
  - persisted on the session under `reviewed_memory_emitted_transition_records`
  - emitted only at the enabled aggregate-card submit boundary; reviewed-memory apply is NOT triggered
96. Keep the emitted-transition-record layer smaller than reviewed-memory apply:
  - keep the shipped `reviewed_memory_transition_audit_contract` contract-only
  - emitted transition record must not equal `blocked_all_required` / `unblocked_all_required`
  - emitted transition record must not equal reviewed-memory apply result
  - emitted transition record must not equal repeated-signal promotion, cross-session counting, or user-level memory
97. Keep canonical transition identity separate from `task_log` replay:
  - `task_log` may mirror one emitted transition record, but only as append-only evidence / appendix
  - `task_log` replay alone must not define canonical transition state
  - approval-backed save support, historical adjuncts, review acceptance, queue presence, and task-log replay alone remain outside emitted-transition-record basis
98. The emitted-record layer is now shipped; keep it truthful:
  - current shipped payload now emits one `reviewed_memory_transition_record` at the enabled aggregate-card submit boundary
  - `record_stage = emitted_record_only_not_applied` means the record is present but reviewed-memory apply has NOT occurred
  - current implementation must not synthesize the object from current read-only surfaces without an actual enabled-submit action
  - the current aggregate serializer and focused regression now enforce correct emission only at the enabled-submit boundary
99. Keep the first truthful emitted action to one exact first trigger only:
  - the first emitted-transition-record implementation may materialize only for `future_reviewed_memory_apply`
  - it must require one exact same-session aggregate already at truthful `unblocked_all_required`
  - it must require one real `canonical_transition_id`
  - it must require one explicit `operator_reason_or_note`
  - it must require one local `emitted_at`
100. Keep the first materialization slice narrower than later transition vocabulary:
  - `future_reviewed_memory_stop_apply` is now implemented (it is no longer later); `future_reviewed_memory_reversal` is now also implemented (it is no longer later): after stop-apply the aggregate card shows an `적용 되돌리기` button; clicking it changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; aggregate identity, supporting refs, and contracts are retained
  - `future_reviewed_memory_conflict_visibility` is now also implemented (it is no longer later): after the effect is reversed the aggregate card shows a `충돌 확인` button; clicking it creates a separate conflict-visibility transition record with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, evaluated `conflict_entries` and `conflict_entry_count`, and `source_apply_transition_ref`; the conflict visibility record is separate from the apply transition record and does not mutate it
  - first-round `task_log` mirroring stays optional; canonical emitted record remains sufficient by itself
101. Keep the shipped operator-visible `future_reviewed_memory_apply` trigger-source affordance narrow before reopening enabled submit or emitted-record materialization:
  - do not synthesize `reviewed_memory_transition_record` from current contract existence, support traces, or `task_log` replay
  - keep the shipped `reviewed_memory_transition_audit_contract` unchanged and contract-only
  - emit no record until one real `canonical_transition_id`, one explicit `operator_reason_or_note`, and one local `emitted_at` can be sourced honestly
102. Keep the first operator-visible `future_reviewed_memory_apply` trigger-source layer as one separate aggregate-level surface:
  - choose `Option A`
  - feed it only from `recurrence_aggregate_candidates`
  - keep it in the existing shell session stack as one section adjacent to `검토 후보`
  - do not place it on source-message cards
  - do not place it in `review_queue_items`
103. The aggregate-card submit boundary is now enabled when `capability_outcome = unblocked_all_required`:
  - show the action label `검토 메모 적용 시작`
  - keep it disabled while `reviewed_memory_capability_status.capability_outcome = blocked_all_required`
  - keep it disabled while `reviewed_memory_transition_audit_contract.audit_stage = contract_only_not_emitted` or while the reason note is empty
  - show a mandatory `operator_reason_or_note` textarea on the aggregate card when unblocked; submit button stays disabled until the note is non-empty
  - clicking the enabled submit now emits one `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied`; reviewed-memory apply is NOT triggered
  - `reviewed_memory_transition_record` is absent while blocked; emitted only at the enabled submit boundary
  - truthful capability basis alone must not be backfilled from this visible disabled affordance
104. Keep trigger-source meaning exact and separate:
  - trigger source means later aggregate-level reviewed-memory transition initiation only
  - trigger source must not mean `reviewed_memory_transition_record` already emitted
  - trigger source must not mean reviewed-memory apply result, repeated-signal promotion, cross-session counting, or user-level memory
105. Keep source-message review separate from aggregate-level trigger source:
  - `review_queue_items` remains source-message candidate review surface only
  - `candidate_review_record` remains one source-message reviewed-but-not-applied trace only
  - source-message `accept` must not be reinterpreted as aggregate-level reviewed-memory apply trigger
106. Keep `canonical_transition_id`, `operator_reason_or_note`, and `emitted_at` generation bound to one later enabled aggregate-card submit:
  - do not derive them from contract existence
  - do not derive them from queue presence or `candidate_review_record`
  - do not derive them from approval-backed save support, historical adjuncts, or `task_log` replay
107. Keep `task_log` mirror-only even after the trigger-source layer is fixed:
  - task-log mirroring may remain optional in the first trigger-source round
  - `task_log` is evidence / appendix only
  - canonical transition state must remain outside `task_log`
108. `disable_source_ref` is now resolved for the same exact aggregate (shipped this round):
  - backed by the existing `reviewed_memory_disable_contract` plus the shared `reviewed_memory_applied_effect_target`
  - materializes only when both the disable contract and the applied-effect target truthfully match the same exact aggregate scope
  - the existing rollback-side handle and resolved `rollback_source_ref` stay unchanged
  - `conflict_source_ref` is now also resolved (shipped same day), backed by `reviewed_memory_conflict_contract` plus shared `reviewed_memory_applied_effect_target`
  - `conflict_source_ref` and `transition_audit_source_ref` are now also resolved (shipped same day)
  - the full internal `reviewed_memory_capability_source_refs` family is now complete with all five refs
109. `conflict_source_ref` is now resolved for the same exact aggregate (shipped this round):
  - backed by the existing `reviewed_memory_conflict_contract` plus the shared `reviewed_memory_applied_effect_target`
  - materializes only when both the conflict contract and the applied-effect target truthfully match the same exact aggregate scope
  - the existing rollback-side handle, resolved `rollback_source_ref`, and resolved `disable_source_ref` stay unchanged
110. `transition_audit_source_ref` is now resolved for the same exact aggregate (shipped this round):
  - backed by the existing `reviewed_memory_transition_audit_contract` plus the shared `reviewed_memory_applied_effect_target`
  - materializes only when both the transition-audit contract and the applied-effect target truthfully match the same exact aggregate scope
  - the existing rollback-side handle, resolved `rollback_source_ref`, resolved `disable_source_ref`, and resolved `conflict_source_ref` stay unchanged
  - the full internal `reviewed_memory_capability_source_refs` family is now complete with all five refs resolved in the store-backed path
  - `reviewed_memory_capability_basis` is now materialized above the complete source family; `capability_outcome` is now `unblocked_all_required`
111. The truthful same-aggregate `unblocked_all_required` capability path is now implemented (shipped this round):
  - `capability_outcome` is now `unblocked_all_required` for aggregates with a materialized basis and complete internal source family
  - the aggregate's exact `first_seen_at` anchor stays necessary-only through the lower proof chain; `first_seen_at` alone, source-message review acceptance, review-queue presence, approval-backed save support, historical adjuncts, and `task_log` replay remain outside the canonical proof or fact layer
  - the current payload-visible `reviewed_memory_capability_basis` remains the lower capability layer and is not reinterpreted as the readiness result alone
  - one truthful aggregate-level `reviewed_memory_transition_record` is now emitted at the enabled aggregate-card submit boundary; the reviewed-memory apply boundary is now also shipped above this emitted record: `record_stage` transitions from `emitted_record_only_not_applied` to `applied_pending_result` with `applied_at` added via POST `/api/aggregate-transition-apply`; the apply result is now also shipped: `결과 확정` confirms the result and transitions `record_stage` to `applied_with_result`, creating `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = result_recorded_effect_pending`, and `result_at`; the memory effect on future responses is now active (`result_stage = effect_active`); active effects are stored on the session as `reviewed_memory_active_effects`; future responses include a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply (`future_reviewed_memory_stop_apply`) is now also shipped: after the effect is active the aggregate card shows an `적용 중단` button; clicking it changes `record_stage` to `stopped`, sets `apply_result.result_stage` to `effect_stopped`, removes the effect from `reviewed_memory_active_effects`, and future responses no longer include the `[검토 메모 활성]` prefix

## Later, After The Memory Phase

1. Choose one narrow approval-gated local operator surface.
2. Define action approval, audit, and rollback requirements for that surface.
3. Extend logs and evals so later actions remain observable and reversible.
4. Decide which action traces can safely become future personalization assets.

## Long-Term, Not Current Contract

1. Personalized local model layer
2. Proprietary model layer or other adaptive model layer
3. Promotion of high-quality local traces into reusable training or ranking assets

## Data Assets To Accumulate Now

### Already Available
1. Source document references
2. Evidence items and summary chunks
3. Approval request / approval outcome traces
4. Feedback labels and reasons
5. Session history and active context
6. Web investigation traces when the secondary mode is used
7. Grounded-brief artifact trace anchors on assistant messages
8. Artifact-linked approval, write, and feedback-related trace detail when applicable

### Next To Add
1. More corrected output pairs from repeated explicit corrected-text submission and corrected-save execution
2. More optional reject-note records from repeated use of the shipped same-card content-verdict note surface
3. Read-only `session_local_memory_signal` projections derived from the existing grounded-brief source-message anchor and linked approval/save traces
4. Richer scoped reason records for correction / reject / reissue outcomes beyond the current minimum labels
5. Reviewable durable-candidate queue items
6. Source-message `candidate_review_record` traces before any reviewed-memory or user-level-memory store
7. Later reviewed scope selections
8. Scope suggestion traces and broader-scope justifications
9. Conflict-resolution and rollback traces
10. Approval-backed save support traces kept distinct from explicit confirmation
11. Eval-ready / not-eval-ready eligibility markers by fixture family
12. Workflow-level eval fixtures, trace-completeness summaries, and scores

## Not Implemented

1. OCR
2. separate grounded-brief artifact store beyond the current source-message outcome and content-verdict capture
3. structured correction-memory schema
4. durable preference memory
5. approval-gated local program operation
6. personalized local model training

## Partial / Opt-In

1. SQLite backend (`storage_backend='sqlite'`): opt-in seam for session, artifact, preference, task-log stores. JSON backend remains default. Corrections store is still JSON-only. Full migration and default rollout are deferred.

## Do Not Build Now

1. vendor-centered product framing around one external model runtime
2. generic web-chatbot expansion
3. web-search-first positioning
4. broad local program automation
5. autonomous destructive actions
6. cloud-first collaboration or account systems

## OPEN QUESTION

1. If `durable_candidate` later leaves the source-message surface, should it keep reusing the current source-message candidate id or mint a new durable-scope id at that boundary?
2. Should the default recurrence rule stay at two grounded briefs for every candidate category, or vary by category later?
3. Which exact local-store, stale-resolution, and reviewed-memory preconditions should be required before any cross-session recurrence aggregation opens?
4. Should the current fixed `confidence_marker = same_session_exact_key_match` remain enough until same-session unblock semantics can be satisfied truthfully, or should a later second conservative level be added only after that boundary opens?
5. Should the shipped `reviewed_memory_boundary_draft` keep repeating the fixed reviewed-scope label long term, or could a later normalization collapse it into `aggregate_identity_ref` plus supporting refs only?
6. Should later category-specific tuning vary approval-backed-save weight beyond the baseline weak-content / medium-path rule?
