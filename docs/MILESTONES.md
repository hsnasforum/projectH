# Milestones

## Framing

### Current Product
- The shipped contract remains a local-first document assistant web MVP with response feedback capture, grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, artifact-linked reject/reissue reason traces, and the first reviewed-memory slice (review queue, aggregate apply trigger, emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility).
- Web investigation remains a permission-gated secondary mode (disabled/approval/enabled per session) under the document-first guardrail.
- The current release candidate is the `app.web` browser shell; pipeline/controller/operator tooling remains outside the release gate.

### Current Reviewed-Memory Boundary
- The first reviewed-memory slice is shipped: review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility.

### Next Phase
- The next phase extends the shipped reviewed-memory boundary into broader structured correction memory and durable preference memory for document work. Cross-session memory remains later.

### Long-Term North Star
- The long-term direction is a teachable local personal agent with later approval-gated local action.

## Completed

### Internal Operator Runtime Slice
- outside the shipped browser release gate, internal pipeline tooling now uses a supervisor-owned run-scoped runtime surface (`status.json`, `events.jsonl`, `receipts/`)
- `controller.server`, `pipeline_gui`, and `pipeline-launcher.py` now read runtime status as thin clients instead of using direct pane/log/file-scan status inference
- duplicate/receipted `STATUS: implement` handoffs, plus handoffs whose referenced `/work` is already matched by a `STATUS: verified` `/verify`, stay on the debug `compat.control_slots` surface only; canonical `control` drops back to `none` so launcher/controller do not show stale `implement` while every lane is already `READY`, and watcher returns to verify follow-up for next-control cleanup instead of redispatching the completed handoff
- CLI/GUI/TUI start paths now share the read-only doctor preflight for required launch checks, and forced stop cleanup returns success once supervisors are gone and status/orphan cleanup is complete
- `tmux` remains available for attach/debug through `TmuxAdapter`, not as the upper-layer state authority
- 오래 방치된 `operator_request.md`는 watcher가 Codex re-triage로 다시 넘기고, supervisor canonical `control` block은 그 재심사 동안 `needs_operator`를 숨겨 internal controller/launcher가 같은 stop에 고정되지 않게 합니다
- `pr_merge_gate` 같은 실제 PR merge publication boundary는 PR merge 전에는 gate 후보로 숨기거나 verify follow-up에 반복 재전달하지 않고 active `needs_operator` / `pr_boundary`로 유지하며, 참조 PR이 이미 merged로 확인되면 `pr_merge_completed` recovery로 stale operator wait를 내립니다. control `HEAD`가 merged PR head와 다르면 `pr_merge_head_mismatch` recovery로 내려 새 PR/control 정정을 유도합니다
- the cozy controller runtime is loaded from `controller/index.html` via a single `<script src="/controller-assets/js/cozy.js">` tag, so polling, sidebar rendering, log modal input/tail refresh, localStorage warning wiring, and idle-roam test hooks live under shared `/controller-assets/js/` ownership instead of one standalone inline runtime copy
- controller has dedicated Playwright smoke (`e2e/playwright.controller.config.mjs`, `make controller-test`) covering the shared cozy module load, scene feature hooks for the time-of-day window / pneumatic tube / courier packet-owl / pettable cat-audio path via `window.getSceneDebug()` and `window.testPetCat()`, the `#storage-warn` toolbar chip, event-log storage warning when browser storage is blocked, deduplicated repeated `/api/runtime/status` fetch failures with one recovery event after reconnect, runtime-owned automation attention detail in the Incident Room, agent-card `data-fatigue` observability, deterministic `fatigued`/`coffee` state transitions via `window.setAgentFatigue` test hook, zone-bounded idle roam (home desk zone) via `window.testPickIdleTargets` + `window.getRoamBounds` test hooks, zone-isolation stacking avoidance via `window.testAntiStacking` test hook (delegates to `testPickIdleTargets` because separate desk zones already keep agents apart), and `window.testHistoryPenalty` returning an empty array because zone-bounded idle roam uses continuous micro-roam rather than discrete spot history; smoke port is configurable via `CONTROLLER_SMOKE_PORT` (default `8781`)

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
- response origin badge with separate answer-mode badge for web investigation, source-role trust labels, and verification strength tags in origin detail
- applied-preferences badge (`선호 N건 반영`) on assistant messages when `applied_preferences` is non-empty, with tooltip showing preference descriptions
- streaming progress and cancel

### Milestone 3: Core QA And Trace Baseline
- Python regression suite
- Playwright smoke suite (scenario 1 now also covers response copy button state with clipboard write verification, per-message timestamps, source filename in both quick-meta and transcript meta, note-path default-directory placeholder, and `문서 요약` source-type label in both quick-meta and transcript meta; browser file picker scenario now also covers source filename and `문서 요약` source-type label in both quick-meta and transcript meta; folder-search scenario now also covers `선택 결과 요약` source-type label and multi-source count-based metadata in both quick-meta and transcript meta, plus response detail preview panel alongside summary body with both cards' ordered labels, full-path tooltips, match badges, and snippet text content, and transcript preview panel with item count, both cards' ordered labels, full-path tooltips, match badges, and snippet text content; general chat scenario covers negative source-type label contract; dedicated claim-coverage panel rendering contract scenario with leading status tags, actionable hints, source role with trust level labels, color-coded fact-strength summary bar, and dedicated plain-language focus-slot reinvestigation explanation including reinforced / regressed / still single-source / still unresolved with natural Korean particle normalization)
- `fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다` browser smoke covering the in-answer fact-strength summary bar's `.fact-count.conflict` badge, with `정보 상충` rendered between the strong and weak groups and no regression to the pre-CONFLICT 3-badge composition
- `live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다` browser smoke covering transcript/live-session `.meta` count-summary composition through `formatClaimCoverageSummary`, with `사실 검증 교차 확인 1 · 정보 상충 1 · 단일 출처 1 · 미확인 1` rendered in stable join order
- search-only response browser smoke with transcript preview cards, hidden body text, `selected-copy` button visibility/click/notice/clipboard regression coverage, full-path tooltip on preview card ordered labels, and match-type badge plus content snippet text in both response detail and transcript
- stable mock-baseline Playwright launch contract with dedicated mock webServer startup and no preexisting-server reuse on the smoke port
- late flip after explicit original-draft save browser smoke
- corrected-save first bridge browser smoke
- corrected-save late reject / re-correct browser smoke
- rejected content-verdict browser smoke
- candidate-linked explicit confirmation browser smoke covering response-card separation, save-support distinction, `검토 후보` appearance, `검토 수락`/`거절`/`보류` review actions, reviewed-but-not-applied queue removal, and later stale-clear behavior
- review-queue `reject`/`defer` browser smoke covering quick-meta(`검토 거절됨`/`검토 보류됨`), transcript-meta, follow-up retention, stale-clear parity with `accept`, and payload `review_action`/`review_status` verification
- same-session recurrence aggregate browser smoke covering separate `검토 메모 적용 후보` placement, `검토 메모 적용 시작` enabled with mandatory reason textarea when `capability_outcome = unblocked_all_required` (disabled while blocked or note empty), preserved separation from `검토 후보`, emitted `reviewed_memory_transition_record` with `record_stage = emitted_record_only_not_applied` on enabled submit, `검토 메모 적용 실행` apply button visible after transition record emission, clicking apply changes `record_stage` to `applied_pending_result` and adds `applied_at` via POST `/api/aggregate-transition-apply`, `결과 확정` button visible after apply boundary, clicking it changes `record_stage` to `applied_with_result` and creates `apply_result` with `result_version = first_reviewed_memory_apply_result_v1`, `applied_effect_kind = reviewed_memory_correction_pattern`, `result_stage = effect_active`, and `result_at`, and confirmed the memory effect is now active (`result_stage = effect_active`) with active effects stored on the session as `reviewed_memory_active_effects` and future responses including a `[검토 메모 활성]` prefix with the operator's reason and pattern fingerprint; stop-apply (`future_reviewed_memory_stop_apply`) is now also implemented: after the effect is active the aggregate card shows an `적용 중단` button; clicking it changes `record_stage` to `stopped`, sets `apply_result.result_stage` to `effect_stopped`, removes the effect from `reviewed_memory_active_effects`, and future responses no longer include the `[검토 메모 활성]` prefix; reversal (`future_reviewed_memory_reversal`) is now also implemented: after the effect is stopped the aggregate card shows an `적용 되돌리기` button; clicking it changes `record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; aggregate identity, supporting refs, and contracts are retained; reversal is separate from stop-apply; conflict visibility (`future_reviewed_memory_conflict_visibility`) is now also implemented: after the effect is reversed the aggregate card shows a `충돌 확인` button; clicking it creates a separate conflict-visibility transition record with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, evaluated `conflict_entries` and `conflict_entry_count`, and `source_apply_transition_ref`; the conflict visibility record is separate from the apply transition record; hard page reload continuity is now verified at six lifecycle points: (1) after transition record emission — reloaded session still shows emitted helper text, payload continuity (`record_stage = emitted_record_only_not_applied`, `applied_at` absent, `apply_result` absent, `reviewed_memory_active_effects` absent or empty), apply button visible and enabled, and a post-reload follow-up does not include `[검토 메모 활성]`; (2) after `검토 메모 적용 실행` — reloaded session still shows applied-pending helper text, payload continuity (`record_stage = applied_pending_result`, `applied_at` present, `apply_result` absent, `reviewed_memory_active_effects` absent or empty), `결과 확정` button visible and enabled, and a post-reload follow-up does not include `[검토 메모 활성]`; (3) after `결과 확정` with active effect — reloaded session still shows the active-effect result indicator, helper text, payload continuity (`record_stage = applied_with_result`, `result_stage = effect_active`, `reviewed_memory_active_effects` present), and a post-reload follow-up still includes `[검토 메모 활성]`; (4) after `적용 중단` — reloaded session still shows the stopped indicator, helper text, payload continuity (`record_stage = stopped`, `result_stage = effect_stopped`, `reviewed_memory_active_effects` absent or empty), and a post-reload follow-up does not include `[검토 메모 활성]`; (5) after `적용 되돌리기` — reloaded session still shows the reversed indicator, helper text, payload continuity (`record_stage = reversed`, `result_stage = effect_reversed`, `reviewed_memory_active_effects` absent or empty), and a post-reload follow-up does not include `[검토 메모 활성]`; (6) after the persisted `reversed` + `conflict_visibility_checked` state — reloaded session still shows the `검토 메모 적용 후보` section with `충돌 확인 완료` and `적용 되돌림 완료` badges, the conflict-checked helper text, and payload continuity (`reviewed_memory_transition_record.record_stage = reversed`, `reviewed_memory_conflict_visibility_record.record_stage = conflict_visibility_checked`)
- web-search history card header badge browser smoke covering answer-mode badge, verification-strength badge with CSS class, source-role trust badge compact label with trust class, and investigation progress summary text when `claim_coverage_progress_summary` is non-empty
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
- latest-update noisy-community natural-reload reload-only (no follow-up) browser smoke covering `WEB` badge, `최신 확인` answer-mode badge, `보조 커뮤니티`, `brunch` negative in origin detail, response body, context box + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention, and zero-count `.meta` no-leak
- history-card entity-card noisy single-source initial-render browser smoke covering visible `다시 불러오기` button, history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2`, no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`, and `출시일` / `2025` / `blog.example.com` noisy single-source leakage negative at initial render (no click reload, no natural reload, no follow-up)
- history-card entity-card actual-search initial-render browser smoke covering visible `다시 불러오기` button, history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2`, and no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta` (no click reload, no natural reload, no follow-up)
- history-card entity-card dual-probe initial-render browser smoke covering visible `다시 불러오기` button, history-card `.meta` exactly `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary, and no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta` (no click reload, no natural reload, no follow-up)
- history-card latest-update noisy community source initial-render browser smoke covering visible `다시 불러오기` button, history-card `.meta` count exactly `0`, no `사실 검증` text leak via accidental `.meta` creation, and `보조 커뮤니티` / `brunch` noisy leakage negative at initial render (no click reload, no natural reload, no follow-up)
- history-card latest-update mixed-source initial-render browser smoke covering visible `다시 불러오기` button, history-card `.meta` count exactly `0`, and no `사실 검증` text leak via accidental `.meta` creation (no click reload, no natural reload, no follow-up)
- history-card latest-update single-source initial-render browser smoke covering visible `다시 불러오기` button, history-card `.meta` count exactly `0`, and no `사실 검증` text leak via accidental `.meta` creation (no click reload, no natural reload, no follow-up)
- history-card latest-update news-only initial-render browser smoke covering visible `다시 불러오기` button, history-card `.meta` count exactly `0`, and no `사실 검증` text leak via accidental `.meta` creation (no click reload, no natural reload, no follow-up)
- history-card entity-card store-seeded actual-search initial-render browser smoke covering visible `다시 불러오기` button, history-card `.meta` count exactly `0`, and no `사실 검증` text leak via accidental `.meta` creation (no click reload, no natural reload, no follow-up)
- history-card entity-card store-seeded actual-search 자연어 reload-only browser smoke covering visible `다시 불러오기` button, history-card `.meta` count exactly `0`, no `사실 검증` text leak, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity
- history-card entity-card store-seeded actual-search `다시 불러오기` click reload-only browser smoke covering visible `다시 불러오기` button, history-card `.meta` count exactly `0`, no `사실 검증` text leak, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity
- history-card entity-card store-seeded actual-search `다시 불러오기` follow-up browser smoke covering history-card `.meta` count exactly `0`, no `사실 검증` text leak, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity drift prevention
- history-card entity-card store-seeded actual-search `다시 불러오기` second-follow-up browser smoke covering history-card `.meta` count exactly `0`, no `사실 검증` text leak, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity drift prevention
- history-card entity-card store-seeded actual-search 자연어 reload chain (자연어 reload → follow-up → second follow-up) browser smoke covering history-card `.meta` count exactly `0`, no `사실 검증` text leak, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity drift prevention
- history-card entity-card zero-strong-slot `다시 불러오기` browser smoke covering history-card `.meta` exactly `사실 검증 미확인 5` missing-only count-summary, no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`, and `WEB` / `설명 카드` / `설명형 단일 출처` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity
- history-card entity-card zero-strong-slot `다시 불러오기` second-follow-up browser smoke covering history-card `.meta` exactly `사실 검증 미확인 5` missing-only count-summary drift prevention, and `WEB` / `설명 카드` / `설명형 단일 출처` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity drift prevention
- history-card entity-card zero-strong-slot 자연어 reload second-follow-up browser smoke covering history-card `.meta` exactly `사실 검증 미확인 5` missing-only count-summary drift prevention, and `WEB` / `설명 카드` / `설명형 단일 출처` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity drift prevention
- history-card entity-card dual-probe `다시 불러오기` reload browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary, no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` / `pearlabyss.com/200` / `pearlabyss.com/300` visible continuity
- history-card entity-card dual-probe `다시 불러오기` second-follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary drift prevention, no leading/trailing separator artifact in the count-summary line, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` visible continuity drift prevention
- entity-card dual-probe 자연어 reload browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary, no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` visible continuity
- entity-card dual-probe 자연어 reload second-follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary drift prevention, no leading/trailing separator artifact in the count-summary line, and `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` visible continuity drift prevention
- history-card entity-card actual-search `다시 불러오기` click reload browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary, and no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`
- history-card entity-card actual-search `다시 불러오기` follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary drift prevention, and no leading/trailing separator artifact in the count-summary line
- history-card entity-card actual-search `다시 불러오기` second-follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary drift prevention, and no leading/trailing separator artifact in the count-summary line
- entity-card actual-search 자연어 reload browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary, and no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`
- entity-card actual-search 자연어 reload follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary drift prevention, and no leading/trailing separator artifact in the count-summary line
- entity-card actual-search 자연어 reload second-follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary drift prevention, and no leading/trailing separator artifact in the count-summary line
- history-card entity-card noisy single-source `다시 불러오기` click reload browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary, and no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`
- history-card entity-card noisy single-source `다시 불러오기` follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary drift prevention, and no leading/trailing separator artifact in the count-summary line
- history-card entity-card noisy single-source `다시 불러오기` second-follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary drift prevention, and no leading/trailing separator artifact in the count-summary line
- entity-card noisy single-source 자연어 reload browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary, and no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`
- entity-card noisy single-source 자연어 reload follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary drift prevention, and no leading/trailing separator artifact in the count-summary line
- entity-card noisy single-source 자연어 reload second-follow-up browser smoke covering history-card `.meta` exactly `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary drift prevention, and no leading/trailing separator artifact in the count-summary line
- history-card entity-card single-source `다시 불러오기` click reload browser smoke covering stored `{weak:1, missing:1}` count-summary plus `단일 출처 상태 1건, 미확인 1건.` progress summary composed into history-card `.meta` exactly `사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건.`, with count-summary appearing before progress summary, no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`, and no leading/trailing separator artifact in the composed line
- history-card entity-card single-source `다시 불러오기` follow-up browser smoke covering stored `{weak:1}` count-summary plus `단일 출처 상태 1건.` progress summary composed into history-card `.meta` exactly `사실 검증 단일 출처 1 · 단일 출처 상태 1건.`, with count-summary appearing before progress summary, no answer-mode label leak inside `.meta`, and no leading/trailing separator artifact
- history-card entity-card single-source `다시 불러오기` second-follow-up browser smoke covering stored `{weak:1}` count-summary plus `단일 출처 상태 1건.` progress summary composed into history-card `.meta` exactly `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` drift prevention, with count-summary appearing before progress summary, no answer-mode label leak inside `.meta`, and no leading/trailing separator artifact
- history-card entity-card single-source 자연어 reload second-follow-up browser smoke covering stored `{weak:1}` count-summary plus `단일 출처 상태 1건.` progress summary composed into history-card `.meta` exactly `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` drift prevention, with count-summary appearing before progress summary, no answer-mode label leak inside `.meta`, and no leading/trailing separator artifact
- `web-search history card header badges` investigation mixed count+progress composition browser smoke covering multi-category count-summary plus non-empty progress summary composed into history-card `.meta` exactly `사실 검증 교차 확인 2 · 단일 출처 1 · 혼합 지표: 교차 확인과 단일 출처가 함께 관찰되었습니다.`, with count-summary appearing before progress summary, no `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak inside `.meta`, and no leading/trailing separator artifact in the composed line
- `history-card summary가 non-zero conflict count를 정보 상충 segment로 렌더링합니다` browser smoke covering history-card `.meta` count-summary composition exactly `사실 검증 교차 확인 1 · 정보 상충 2 · 단일 출처 1`, with the non-zero CONFLICT segment appearing between strong and weak counts and no answer-mode label leak inside `.meta`
- `web-search history card header badges` general label+count+progress composition browser smoke covering general answer-mode plus multi-category count-summary plus non-empty progress summary composed into history-card `.meta` exactly `일반 검색 · 사실 검증 교차 확인 2 · 단일 출처 1 · 일반 지표: 커뮤니티 단서와 교차 확인이 함께 관찰되었습니다.`, with stable `label → count → progress` composition order, no `혼합 지표:` / `설명 카드` / `최신 확인` investigation answer-mode leak inside `.meta`, and no leading/trailing separator artifact in the composed line
- `web-search history card header badges` general label+count-only composition browser smoke covering general answer-mode plus single-category count-summary plus empty progress summary composed into history-card `.meta` exactly `일반 검색 · 사실 검증 교차 확인 2`, with label followed only by the count-only segment, no `일반 진행:` / `혼합 지표:` / `일반 지표:` / `설명 카드` / `최신 확인` absent segment leak inside `.meta`, and no leading/trailing separator artifact in the composed line
- `web-search history card header badges` general label+progress-only composition browser smoke covering general answer-mode plus empty count-summary plus non-empty progress summary composed into history-card `.meta` exactly `일반 검색 · 일반 진행: 커뮤니티 단서가 단일 출처 상태로 남아 있습니다.`, with label followed only by the progress-only segment, no `사실 검증` / `혼합 지표:` / `일반 지표:` / `설명 카드` / `최신 확인` absent segment leak inside `.meta`, and no leading/trailing separator artifact in the composed line
- history-card entity-card click reload → browser composer (`#user-text` + `submit-request`) plain follow-up (`이 결과 한 문장으로 요약해줘`) browser smoke covering the `/api/chat/stream` POST payload omitting `load_web_search_record_id` after the click-reload step, `#claim-coverage-box` visible with `#claim-coverage-text` containing the stored entity-card `장르` / `[단일 출처]` slot, and history-card `.meta` exactly `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` retained across the plain follow-up
- history-card latest-update click reload → browser composer (`#user-text` + `submit-request`) plain follow-up (`이 결과 한 문장으로 요약해줘`) browser smoke covering the `/api/chat/stream` POST payload omitting `load_web_search_record_id` after the click-reload step, `#claim-coverage-box` hidden, and history-card `.meta` count `0` retained across the plain follow-up
- entity-card noisy single-source claim natural-reload + click-reload follow-up/second-follow-up exclusion + provenance exact-field retention: `출시일`, `2025`, `blog.example.com` 본문/detail 미노출, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지, source_paths/context box에 `blog.example.com` provenance 포함
- PDF text-layer support: readable text-layer PDF → visible summary body with `문서 요약` label + context box/quick meta/transcript meta PDF filename
- OCR-not-supported guidance: scanned/image-only PDF → visible response guidance with `요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`
- browser file picker scanned/image-only PDF OCR-not-supported guidance smoke covering visible response guidance with exact strings `요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`
- browser folder picker scanned PDF + readable file mixed search count-only partial-failure notice + preview exact-field + selected-path/copy + transcript hidden smoke
- browser file picker readable text-layer PDF success summary smoke covering OCR guidance 미노출 + visible summary body with extracted text + context box/quick meta/transcript meta `readable-text-layer.pdf` + `문서 요약` label
- browser folder picker mixed scanned-PDF search-plus-summary partial-failure + preview exact-field + transcript preview exact-field smoke
- response feedback capture
- local web-search history storage
- SQLite browser smoke baseline (`e2e/playwright.sqlite.config.mjs`): opt-in sqlite backend parity gate covering recurrence aggregate emitted-apply-confirm lifecycle, stale-candidate retirement before apply start, post-confirm active lifecycle survival through supporting correction supersession, post-confirm recorded-basis label survival through supporting correction supersession, stop-reverse-conflict cleanup, document-loop save/correction/verdict continuity (saved history vs late reject verdict, reject keeps approval then explicit save supersedes, corrected-save first bridge snapshot at request time, corrected-save stays frozen after later reject + re-correction), core document productivity loop (summary + evidence + summary chunks, browser file picker summary, browser folder picker search, search-only hidden-body + preview-card), PDF/OCR document workflow (scanned/image-only PDF OCR-not-supported guidance, mixed scanned+readable folder search count-only partial-failure notice, mixed scanned+readable folder search+summary partial-failure notice with readable preview, readable text-layer PDF normal summary), reviewed-memory candidate/review-queue surface (candidate confirmation separate from save support and later-correction stale clear, review-queue reject/defer quick-meta + transcript-meta + stale-clear parity with accept, review-queue reject-defer aggregate support visibility), core approval save path (save request reissue before approval, approved write produces the note on disk), core chat shell (streaming cancel interrupts the visible response flow, plain general-chat response omits document-only source-type labels), claim-coverage panel (leading status tags with actionable hints, reinvestigation-target slot progress state, reinforced slot after reinvestigation, regressed slot after reinvestigation), web-search history card header badges (answer-mode + verification-strength + source-role trust badges with `.meta` count/progress composition), history-card initial-render contract (latest-update noisy/mixed/single/news-only zero-count empty-meta no-leak, entity-card noisy/actual-search/dual-probe/store-seeded count-summary meta), history-card click-reload / reload-only contract (entity-card + latest-update WEB badge, answer-mode badges, verification labels, source-role trust badges, source paths, noisy-source exclusion, store-seeded reload-only empty-meta no-leak), and history-card click-reload first-follow-up contract (entity-card + latest-update WEB badge, answer-mode badges, verification labels, source-role trust badges, source paths, noisy-source exclusion, store-seeded follow-up empty-meta no-leak), and history-card click-reload second-follow-up contract (entity-card + latest-update WEB badge, answer-mode badges, verification labels, source-role trust badges, source paths, dual-probe mixed count-summary meta retention, noisy-source exclusion, store-seeded second-follow-up empty-meta no-leak), and history-card natural-reload reload-only contract (`방금 검색한 결과 다시 보여줘` triggered entity-card + latest-update WEB badge, answer-mode badges, verification labels, source-role trust badges, source paths/provenance retention, zero-strong-slot continuity, noisy-source exclusion, store-seeded natural-reload empty-meta no-leak), and history-card natural-reload follow-up / second-follow-up chain contract (entity-card + latest-update WEB badge, answer-mode badges, verification labels, source-role trust badges, source paths/provenance retention, zero-strong-slot missing-only count-summary drift-prevention, dual-probe mixed count-summary meta retention, noisy-source exclusion, store-seeded natural-reload chain empty-meta no-leak), and history-card click-reload composer plain follow-up contract (entity-card top-level claim_coverage retention and latest-update empty claim_coverage surfaces retention through the real browser composer path without `load_web_search_record_id`)

## In Progress

### Milestone 4: Secondary-Mode Investigation Hardening
- claim-based entity-card shaping (history-card progress summary surfacing shipped)
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
  - one same-source-message `candidate_review_record` may now be recorded through `accept`, `reject`, or `defer`
  - all three outcomes stay reviewed-but-not-applied and do not open user-level memory
- keep durable candidates reviewable and separate from future user-level memory
- keep reviewed-memory store and user-level memory later than the shipped review action slice

### Milestone 7: Reviewable Durable Candidate Surface
- implemented first slice:
  - one local pending review queue surface for eligible `durable_candidate` records
  - one compact existing-shell `검토 후보` section fed only by current session `review_queue_items`
  - one same-source-message `candidate_review_record` may now be recorded through `accept`, `reject`, `defer`, or `edit`
  - all four outcomes stay reviewed-but-not-applied and the matching pending item leaves the queue
- Axis 2 shipped: `CandidateReviewAction.EDIT = "edit"` -> status `"edited"` with optional `reason_note` storage (seqs 807-808)
- Axis 4 shipped: `suggested_scope` optional free-text field added to `candidate_review_record` across 4 layers (seqs 818-819); `CandidateReviewSuggestedScope` StrEnum (`message_only`, `family_scoped`, `global_preference`) defined in `core/contracts.py` + `storage/session_store.py` optional validation (seq 849)
- still later inside this milestone:
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
- Axis 1 shipped: `core/eval_contracts.py` — `EvalFixtureFamily` StrEnum (7 families), `EVAL_QUALITY_AXES` frozenset (6 axes), `EVAL_FIXTURE_FAMILY_AXES` mapping, `EvalArtifactCoreTrace` TypedDict (seq 826)
- Axis 2 shipped: first service fixture `correction_reuse_001.json` + `.gitignore` `!data/eval/` exception (seqs 830-831)
- Axis 3 shipped: `eval/fixture_loader.py` unit helper + `scope_suggestion_safety_001.json` fixture (seq 835)
- Axis 4 shipped: remaining 5 service fixtures completing all 7 families (seq 837); `suggested_scope` value constraints and family-specific trace extensions deferred until reviewed-memory planning opens
- Axis 5 shipped: `tests/test_eval_loader.py` (7 unit tests: all-family load + _validate() reject paths) + `eval/__init__.py` `load_fixture` package-level export (seq 843); `CandidateReviewSuggestedScope` enum and e2e stage remain deferred
- Axis 6 shipped: `core/eval_contracts.py` family-specific TypedDicts (`CorrectionReuseTrace`, `ApprovalFrictionTrace`, `ReviewabilityTrace`, `ScopeSafetyTrace`, `RollbackabilityTrace`, `ConflictDeferTrace`, `ExplicitVsSaveSupportTrace`) + `EVAL_FAMILY_TRACE_CLASS` mapping + `eval/__init__.py` export (seq 853); `CandidateReviewSuggestedScope` enum and e2e stage remain deferred
- Axis 7 shipped: all 7 service fixtures enriched with family-specific TypedDict fields per seq 853 TypedDicts (seq 858); e2e eval stage remains deferred
- Axis 8 shipped: `eval/fixture_loader.py` extended with `EVAL_FAMILY_TRACE_CLASS`-based validation — unknown key rejection and isinstance type-check for family-specific fields via `typing.get_type_hints()`; `tests/test_eval_loader.py` +2 tests (9 total) (seq 862); e2e eval stage remains deferred

## Later, After The Memory Phase

### Milestone 9: Approval-Gated Local Operator Foundation
- choose one narrow operator surface
- define action approval, audit, and rollback expectations
- keep local actions observable and reversible
- Operator action contract shipped: `OperatorActionKind` StrEnum (`local_file_edit`, `shell_execute`, `session_mutation`) + `OperatorActionContract` TypedDict (5 fields, total=False) in `core/contracts.py` (seq 866); action execution, approval flow, and storage wire-up deferred
- Storage & approval wiring shipped: `OperatorActionRecord` TypedDict + `ApprovalKind.OPERATOR_ACTION` in `core/contracts.py`; `record_operator_action_request()` + session-reload normalization (`_normalize_pending_approval_record`) in `storage/session_store.py` (seq 871)
- Execution stub shipped: `core/operator_executor.py` — `execute_operator_action()` read-only preview for `local_file_edit` (10 lines), ValueError for other kinds; `_execute_pending_approval` operator_action branch in `core/agent_loop.py` (seq 875)
- Outcome & audit storage shipped: `operator_action_history` session field + `record_operator_action_outcome()` in `storage/session_store.py`; outcome written after successful execution in `core/agent_loop.py` (seq 879)
- Failure outcome audit shipped: failed operator actions now recorded in `operator_action_history` with `status="failed"` + `error` field before returning error response in `core/agent_loop.py` (seq 883); Milestone 9 Axes 1–5 complete
- **Milestone 9 closed** (seqs 866–883): observable and reversible `local_file_edit` action foundation established; actual file write, rollback, UI approval card, `shell_execute`/`session_mutation` execution deferred to a future milestone

### Milestone 10: Local Operator Operation
- enable actual file write for `local_file_edit` under explicit approval
- implement first rollback logic for reversible local actions
- verify audit trail integrity for end-to-end operator effects
- Local file edit active write shipped: `content: str` in contracts; `execute_operator_action()` performs `Path.write_text()` (seq 893)
- Reversible backup mechanism shipped: `is_reversible=True` → backup saved to `backup/operator/`; `backup_path` preserved in `operator_action_history` (seq 897)
- Audit trail verification shipped: end-to-end integration test exercises full request → execute → outcome flow; all 5 history fields verified (seq 901)
- **Milestone 10 closed** (seqs 893–901): local file operation and backup foundation established; actual rollback restore and sandbox path restrictions remain deferred

### Milestone 11: Operator Action Reversibility & Sandbox
- Rollback restore shipped: `rollback_operator_action(record)` reads `backup_path`, restores `target_id`; missing backup → soft failure `restored=False` (seq 908)
- Path restriction sandbox shipped: `_validate_operator_action_target()` raises `ValueError` if `target_id` resolves outside `Path.cwd()`; all executor/audit tests updated to `dir="."` (seq 912)
- Rollback trace shipped: `rollback_approval_id` dispatch + `_execute_operator_rollback()` records `status="rolled_back"` in `operator_action_history`; `get_operator_action_from_history()` added to `SessionStore` (seq 916)
- **Milestone 11 closed** (seqs 908–916): operator action reversibility and sandbox complete; frontend rollback trigger and backup retention policy remain deferred

### Why This Is Later
- Program operation should follow stable correction and preference memory, not precede it.
- The system must prove alignment on document work before it expands into action.

## Long-Term

### Milestone 12: Personalized Local Model Layer
- promote high-quality local traces into personalization assets
- evaluate whether a local adaptive model layer is justified
- keep deployment and rollback safe and measurable

### Preconditions
- enough grounded-brief correction pairs
- enough preference traces
- enough approval / rejection traces
- enough workflow-level eval data

#### Shipped Infrastructure (Axes 1–6, 2026-04-23)
- Axis 1 (6838aba, seq 921): trace audit baseline — `scripts/audit_traces.py`, `get_global_audit_summary()` (267 sessions, 137 correction pairs)
- Axis 2 (701166b, seq 925): trace export utility — `scripts/export_traces.py`, `stream_trace_pairs()`
- Axis 3 (966fdb4, seq 929+933): quality scoring + threshold recalibration — `_is_high_quality()` (`0.05 ≤ score ≤ 0.98`); 137/137 pairs high-quality
- Axis 4 (215096d, seq 935): asset promotion — `scripts/promote_assets.py` → `CorrectionStore.promote_correction()`; 137 pairs promoted
- Axis 5 (c3e46ab, seq 941): preference visibility — `audit_traces.py` PreferenceStore counts + `data/preference_assets.jsonl`; 23 candidate preferences
- Axis 6 (dbfbec0, seq 944): trace evaluation — `scripts/evaluate_traces.py`; model layer: JUSTIFIED (137 pairs ≥100, 100% HQ ≥50)
- **Milestone 12 closed** (seqs 921–944): personalization pipeline infrastructure + evaluation complete; model-layer deployment and approval trace collection deferred

### Milestone 13: Applied Preference Effectiveness Tracking
- track which active preferences are applied to responses and correction traces
- measure whether applied preferences improve later corrections before widening memory automation
- keep preference activation thresholded and auditable while the safety loop is validated

#### Guardrails
- repeated-signal promotion is limited to `cross_session_count >= 3` auto-activation for `CANDIDATE` preferences
- cross-session counting remains local preference evidence, not broader user-level memory
- `ACTIVE`, `REJECTED`, and `PAUSED` preferences remain on their existing lifecycle state during threshold checks

#### Shipped Infrastructure (Axes 1–6, 2026-04-23)
- Axis 1 (8cea2f1, seq 958): applied preference tracking in session + trace export — `app/handlers/chat.py` stores `applied_preference_ids` in `update_last_message()`; `storage/session_store.py` yields `applied_preference_ids` in `stream_trace_pairs()`; 57 unit tests
- Axis 2 (a4f4cbd, seq 962): correction link — `storage/correction_store.py` `record_correction()` stores `applied_preference_ids`; `app/handlers/feedback.py` passes ids from session message; 58 unit tests
- Axis 3 (399122f, seq 966): effectiveness metric baseline — `storage/session_store.py` `get_global_audit_summary()` adds `personalized_response_count` / `personalized_correction_count`; `scripts/audit_traces.py` displays personalization correction rate; 59 unit tests
- Axis 4 (fc86577, seq 970): per-preference reliability — `get_global_audit_summary()` adds `per_preference_stats` map (`applied_count`/`corrected_count` per fingerprint); `scripts/audit_traces.py` displays per-preference correction rates sorted descending; 60 unit tests
- Axis 5 (80fe1dd, seq 974): preference reliability API — `list_preferences_payload()` enriches each record with `reliability_stats` (`applied_count`/`corrected_count` via `per_preference_stats`); SQLiteSessionStore fallback returns 0 counts; frontend display shipped as Axis 5b (ebd82cb, seq 16)
- Axis 5b (ebd82cb, seq 16): preference reliability frontend — `PreferencePanel.tsx` renders 적용 N회 · 교정 M회 from live `reliability_stats`; `api/client.ts` adds optional `reliability_stats` field
- Axis 6 (seq 21): auto-activation — `storage/preference_store.py` auto-activates `CANDIDATE` preferences to `ACTIVE` when `cross_session_count >= 3`, while leaving other lifecycle states unchanged

### Milestone 14: Personalization Integrity and Trace Quality Integration
- keep personalization infrastructure consistent across local storage backends before adding user-visible memory expansion
- integrate trace quality and preference lifecycle surfaces only after backend parity is truthful
- keep cross-session preference handling bounded to reviewed evidence and existing lifecycle states

#### Guardrails
- backend parity comes before user-visible expansion
- no user-level memory widening in this milestone definition
- SQLite and JSON preference lifecycle behavior must not diverge on activation thresholds

#### Shipped Infrastructure (Axis 1, 2026-04-23)
- Axis 1 (seq 24): SQLite preference auto-activation parity — `storage/sqlite_store.py` `SQLitePreferenceStore` increments `cross_session_count` for new reviewed-candidate source refs and auto-activates `CANDIDATE` preferences when `cross_session_count >= 3`, matching JSON-backed `PreferenceStore` while leaving `ACTIVE`, `REJECTED`, and `PAUSED` statuses unchanged
- Axis 2 (seq 27): quality integration — `core/delta_analysis.py` exports `is_high_quality()`; `storage/preference_store.py` stores `avg_similarity_score` during `promote_from_corrections`; `list_preferences_payload` enriches with `quality_info`; `PreferencePanel.tsx` displays 고품질 badge
- Axis 3 (seq 30): review queue quality integration — `serializers.py` `_build_review_queue_items` enriches each item with `quality_info`; `ReviewQueueItem` type added to `client.ts`; `ChatArea.tsx` shows 고품질 N건 count in review badge

### Milestone 15: Personalization Stability and Review Surface Expansion
- stabilize quality data foundation across all storage backends before UI expansion
- Axis 1, 2, 3 ordered: backend parity → smoke coverage → review queue UX

#### Guardrails
- no user-level memory widening
- SQLite and JSON preference quality behavior must not diverge

#### Shipped Infrastructure (Axis 1, 2026-04-23)
- Axis 1 (seq 33): SQLite quality parity — `record_reviewed_candidate_preference` accepts `avg_similarity_score` in both JSON and SQLite backends; `aggregate.py` computes score from `correction_store` before accept; `quality_info` now populated for reviewed-candidate preferences
- Axis 2 (seq 37): quality integration smoke tests — `web-smoke.spec.mjs` gains two targeted scenarios verifying `quality_info` shape in review queue items (API contract) and `quality-count` badge visibility (browser DOM, conditional on mock correction score range)
- Axis 3 (seq 40): review queue list UI — `ReviewQueuePanel.tsx` renders individual items with statement, 고품질 badge, and accept/defer/reject actions; `Sidebar.tsx` includes panel above `PreferencePanel`; `ChatArea` review badge becomes clickable button (`data-testid="review-queue-badge"`); `postCandidateReview` extended with `candidate_id` + `candidate_updated_at`; smoke test confirms badge click → panel → accept flow

### Milestone 16: Review Evidence Enrichment and Decision Clarity
- make review candidates easier to judge before broader preference management work
- keep enrichment read-only until the user explicitly accepts/defer/rejects a candidate
- Axis 1, 2, 3 ordered: correction evidence → source/effect context → targeted regression guard

#### Guardrails
- no user-level memory widening
- no automatic preference status changes from evidence display alone
- review queue enrichment must stay compact and local to existing candidate evidence

#### Shipped Infrastructure (Axes 1–3, 2026-04-23)
- Axis 1 (seq 43): review evidence enrichment — expose compact `delta_summary` on each `review_queue_items[]` entry and render a single-line correction pattern in `ReviewQueuePanel`
- Axis 2 (seq 44): UI resilience — `handleCandidateReview` in `App.tsx` surfaces review action errors via `addToast("error", ...)`, matching the existing handler pattern
- Axis 3 (seq 47): integrity consolidation — `OllamaModelAdapter` caches `list_models()` result; `_routed_model` degrades gracefully through HEAVY→MEDIUM→LIGHT when target model unavailable; `vite.config.ts` outputs fixed-name assets (`index.js`/`index.css`); full smoke gate confirmed passing (139 tests)

### Milestone 17: Personalization Refinement — Editing and Evidence Detail
- transition from fixed observation to active user control of preference wording
- Axis 1, 2, 3 ordered: statement editing → evidence detail view → release stabilization

#### Guardrails
- no new backend API routes (reuse `/api/candidate-review` with optional statement payload)
- no user-level memory widening beyond current preference lifecycle
- edit path only affects description/statement, not fingerprint or lifecycle

#### Shipped Infrastructure (Axes 1-3, 2026-04-23)
- Axis 1 (seq 50): inline statement editing in `ReviewQueuePanel`; `aggregate.py` uses `statement_override` when provided; `postCandidateReview` extended with optional statement param; smoke test confirms edited text appears in preference
- Axis 2 (seq 54): detailed evidence view — `serializers.py` `_build_review_queue_items` adds `original_snippet` / `corrected_snippet` (≤400 chars) from the first correction with both source and corrected text; `ReviewQueueItem` carries the fields; `ReviewQueuePanel` adds `상세 보기` / `접기` to compare original and corrected snippets without rich diff styling
- Axis 3 (seq 55, verify lane): release stabilization — full `make e2e-test` smoke gate confirmed **141 passed** (20.2m) on 2026-04-23; includes all M17 Axis 1-2 scenarios; branch `feat/watcher-turn-state` is release-ready pending operator PR merge approval

- **Milestone 17 closed** (Axes 1–3): review statement editing, evidence detail view, and release gate complete

### Milestone 18: Cross-Session Signal Infrastructure
- establish SQLite correction store parity as the foundation for efficient cross-session recurrence discovery
- Axis 1, 2, 3 ordered: SQLite correction store → SQL recurrence indexing → review queue global candidates

#### Guardrails
- no user-visible feature changes in Axis 1 (backend-only)
- JSON CorrectionStore remains the default until explicit SQLite backend switch
- migration is additive (INSERT OR IGNORE) and safe to re-run

#### Shipped Infrastructure (Axes 1-3, 2026-04-23)
- Axis 1 (seq 60): SQLiteCorrectionStore — `record_correction`, `get`, `find_by_fingerprint`, `find_by_artifact`, `find_by_session`, `list_recent`; corrections table schema already existed; `migrate_json_to_sqlite` updated to migrate 8,000+ correction JSON files
- Axis 2 (seq 63): SQL recurrence indexing & server wiring — `SQLiteCorrectionStore.find_recurring_patterns()` uses `GROUP BY delta_fingerprint HAVING COUNT(*) >= 2`; `app/web.py` sqlite branch wires `SQLiteCorrectionStore(db)` replacing JSON fallback
- Axis 3 (seq 66): global candidate review UI — `_build_review_queue_items` appends cross-session recurring patterns not yet in `PreferenceStore` as `is_global=True` `ReviewQueueItem`s; `ReviewQueuePanel` shows `범용` badge; `submit_candidate_review` handles `source_message_id="global"` path; smoke test verifies `is_global` field presence

- **Milestone 18 closed** (Axes 1–3): SQLite correction store parity, SQL recurrence indexing + server wiring, global candidate review UI complete

### Milestone 19: Durable Preference Depth and Interaction Integrity
- stabilize and enrich the lifecycle of learned personalization rules
- Axis 1, 2, 3 ordered: evidence persistence → discovery integrity → post-learning refinement

#### Guardrails
- no user-level memory widening beyond current preference lifecycle
- snippets are read-only display; no fingerprint or lifecycle changes

#### Shipped Infrastructure (Axes 1-3, 2026-04-23)
- Axis 1 (seq 69): preference evidence persistence — `promote_from_corrections` and `record_reviewed_candidate_preference` store `original_snippet` / `corrected_snippet` (≤400 chars) from source corrections; `aggregate.py` passes snippets on accept; `PreferenceRecord` type updated; `PreferencePanel.tsx` adds `상세 보기` / `접기` toggle
- Axis 2 (seq 72): discovery integrity guards — `find_recurring_patterns()` global path uses `COUNT(DISTINCT session_id) >= 2`; `_build_review_queue_items` deduplicates global candidates by statement against preference descriptions and session-local items; global candidates get real `quality_info` from corrections; global accept path respects `statement_override`
- Axis 3 (seq 75): durable preference editing — `update_description()` in JSON and SQLite stores; `POST /api/preferences/update-description` endpoint; `PreferencePanel.tsx` inline edit mode (`편집`, textarea, `저장` / `취소`); M19 milestone closed

- **Milestone 19 closed** (Axes 1–3): evidence persistence, discovery integrity, and post-learning refinement complete

### Milestone 20: Personalization Scaling and Conflict Integrity
- transition the system into a production-ready, high-performance state
- Axis 1, 2, 3 ordered: SQLite default + migration → conflict detection → release consolidation

#### Guardrails
- JSON backend preserved via `LOCAL_AI_STORAGE_BACKEND=json` env override
- migration is idempotent (`INSERT OR IGNORE`); startup migration never blocks server

#### Shipped Infrastructure (Axes 1-3, 2026-04-23)
- Axis 1 (seq 78): SQLite default — `config/settings.py` default changed to `"sqlite"`; `app/web.py` sqlite branch conditionally runs `migrate_json_to_sqlite` for corrections on first startup; migration idempotency verified by test
- Axis 2 (seq 81): preference conflict detection — `list_preferences_payload` enriches each preference with `conflict_info` (`has_conflict` + `conflicting_preference_ids`) using Jaccard word-token similarity > 0.7 between ACTIVE preferences; `PreferencePanel.tsx` shows `⚠ 충돌` badge and activate confirmation when conflicts exist
- Axis 3 (seq 84/85, verify lane): release consolidation smoke gate — fixed 6 failing E2E tests caused by cross-session fingerprint collision in test fixtures and stale global-candidate assertions; full `make e2e-test` confirmed **142 passed (7.5m)** on 2026-04-23

- **Milestone 20 closed** (Axes 1–3): SQLite default + migration, preference conflict detection, and release consolidation smoke gate complete

### Milestone 21: Personalization Maturity and Release Bundle

#### Shipped Infrastructure (Axes 1-3, 2026-04-23)
- Axis 1 (seq 87): SQLite correction lifecycle parity — `SQLiteCorrectionStore` now implements `confirm_correction`, `promote_correction`, `activate_correction`, `stop_correction` matching JSON `CorrectionStore` contract; 5 new unit tests cover status column and `data` JSON blob updates plus missing-id behavior
- Axis 2 (seq 90): durable global reject persistence — `record_reviewed_candidate_preference` accepts optional `status=` parameter; global reject path in `submit_candidate_review` records REJECTED preference, permanently silencing the fingerprint via existing `_build_review_queue_items` dedup
- Axis 3 (seq 91, verify lane): release gate — full `make e2e-test` confirmed **142 passed (8.3m)** on 2026-04-23; no regressions from Axes 1–2 backend changes

- **Milestone 21 closed** (Axes 1–3): SQLite correction lifecycle parity, durable global reject persistence, and release gate complete

### Milestone 22: Correction Lifecycle Integrity
- close the M21 open risk: invalid state transitions silently succeeded in `SQLiteCorrectionStore`
- Axis 1, 2, 3 ordered: state-order guard → global reject browser coverage → release gate

#### Guardrails
- guard returns `None` (not raise) to match the existing missing-record convention
- JSON `CorrectionStore` is not guarded in this axis; SQLite remains the default backend
- do not change the four public lifecycle methods; only `_transition()` needs the guard

#### Shipped Infrastructure (Axes 1-3, 2026-04-24)
- Axis 1 (seq 94): state-order guard — `CORRECTION_STATUS_TRANSITIONS` from `core/contracts.py` is now enforced in `SQLiteCorrectionStore._transition()`; invalid transitions return `None`; 3 new unit tests cover out-of-order, from-stopped, and valid-chain behavior
- Axis 2 (seq 95): global reject permanence smoke — Playwright API-level test verifies that a rejected global candidate (`message_id="global"`, `review_action="reject"`) does not reappear in any subsequent session's `review_queue_items`; uses `createQualityReviewQueueItem` across 4 sessions with a unique recurring corrected text
- Axis 3 (seq 96, verify lane): release gate — full `make e2e-test` confirmed **143 passed (10.1m)** on 2026-04-24; new global reject permanence scenario (test #141) passes; total count increased from 142 to 143

- **Milestone 22 closed** (Axes 1–3): SQLite correction lifecycle state-order guard, global reject permanence browser coverage, and release gate complete

### Milestone 23: Correction Lifecycle Integrity — JSON Parity

#### Guardrails
- guard returns `None` (not raise) — same convention as M22 Axis 1 SQLite guard
- do not change the four public lifecycle methods; only `_transition()` needs the guard
- existing `test_lifecycle_transitions` already covers the valid chain; add only invalid-transition tests

#### Shipped Infrastructure (Axis 1, 2026-04-24)
- Axis 1 (seq 98): JSON CorrectionStore state-order guard — `CORRECTION_STATUS_TRANSITIONS` from `core/contracts.py` enforced in `CorrectionStore._transition()`; invalid transitions return `None`; 2 new unit tests cover out-of-order and from-stopped cases

- **Milestone 23 closed** (Axis 1): JSON CorrectionStore state-order guard complete; both JSON and SQLite correction lifecycle paths now enforce `CORRECTION_STATUS_TRANSITIONS`

### Milestone 24: Correction Lifecycle Observability

#### Guardrails
- audit output is read-only; no lifecycle state is mutated
- JSON and SQLite stores both get parity implementation
- script change uses the JSON CorrectionStore default path (`data/corrections`)

#### Shipped Infrastructure (Axis 1, 2026-04-24)
- Axis 1 (seq 101): `list_incomplete_corrections()` — returns corrections with RECORDED/CONFIRMED/PROMOTED status; JSON store uses `_scan_all()` filter; SQLite store uses `WHERE status IN (…)` query; `scripts/audit_traces.py` prints incomplete count and first 5 entries

- **Milestone 24 closed** (Axis 1): correction lifecycle observability complete; both stores expose `list_incomplete_corrections()`; audit script surfaces count

### Milestone 25: Preference Lifecycle Audit

#### Guardrails
- audit endpoint is read-only; no preference state is mutated
- conflict pair detection reuses the existing `_jaccard_word_similarity` threshold (> 0.7)
- frontend audit summary is compact (one line); do not add a separate audit panel

#### Shipped Infrastructure (Axes 1-2, 2026-04-24)
- Axis 1 (seq 102): GET `/api/preferences/audit` — returns total preference count, counts by status, and `conflict_pair_count`; `PreferencePanel.tsx` shows compact audit summary line above the preference list
- Axis 2 (seq 103, verify lane): release gate — full `make e2e-test` confirmed **143 passed (10.7m)** on 2026-04-24; no regressions from Axis 1 frontend change

- **Milestone 25 closed** (Axes 1–2): preference lifecycle audit endpoint, compact summary UI, and release gate complete

### Milestone 26: Global Candidate E2E Test Isolation

#### Guardrails
- production server startup path is unchanged; isolation is Playwright config only
- `data/notes/` and `data/web-search/` stay at repo defaults (same as `playwright.sqlite.config.mjs` convention)
- within a run, test-level fixture uniqueness conventions still apply (no per-test DB reset)

#### Shipped Infrastructure (Axes 1-2, 2026-04-24)
- Axis 1 (seq 104): `playwright.config.mjs` now uses `fs.mkdtempSync()` to create a fresh SQLite DB per run via `LOCAL_AI_SQLITE_DB_PATH`; mirrors the pattern already in `playwright.sqlite.config.mjs`
- Axis 2 (seq 105, verify lane): release gate — full `make e2e-test` confirmed **143 passed (6.5m)** with fresh-DB isolation; faster than prior runs (10.7m) due to empty DB at start

- **Milestone 26 closed** (Axes 1–2): global candidate E2E test isolation complete; both default and SQLite Playwright configs now use per-run fresh SQLite DB

### Milestone 27: Correction Adoption Tracking

#### Guardrails
- no schema changes; `find_adopted_corrections()` reads existing `status` + `activated_at` fields only
- `scripts/audit_traces.py` output change is additive (one new line); no existing output removed

#### Shipped Infrastructure (Axis 1, 2026-04-24)
- Axis 1 (seq 107): `find_adopted_corrections()` added to `CorrectionStore` (JSON) and `SQLiteCorrectionStore`; `scripts/audit_traces.py` now prints `Adopted corrections (ACTIVE): N`

#### Shipped Infrastructure (Axis 2, 2026-04-24)
- Axis 2 (seq 110): `/api/preferences/audit` now includes `adopted_corrections_count`; `PreferencePanel` audit row shows `활성 교정 N개` when N > 0

### Milestone 28: Structural Owner Bundle

#### Guardrails
- write/transition paths only; read-only display surfaces (e.g. _build_active_round) are out of scope
- no changes to supervisor.py active_round selection (advisory confirmed read-surface cohesion)
- `.pipeline/state/jobs/` subdirectory isolation: already shipped in schema.py + verify_fsm.py + watcher_core.py; no Axis needed

#### Shipped Infrastructure (Axes 1–2, 2026-04-24)
- Axis 1 (seq 117): `verify_fsm.StateMachine.step_verify_close_chain()` — VERIFY_RUNNING close chain single-owner in FSM; `WatcherCore._poll()` delegates to dedicated method; generic `step()` blocked by replay test
- Axis 2 (seq 118): `verify_fsm.StateMachine.release_verify_lease_for_archive()` — lease release for archive-matching VERIFY_PENDING path moved from direct `watcher_core.lease.release()` to FSM delegation; direct call blocked by replay test

- **Milestone 28 closed** (Axes 1–2): FSM single-owner for VERIFY_RUNNING close chain and lease release; advisory seq 120 confirmed Axis 3 not needed

### Milestone 29: Reviewed-Memory Loop Refinement

#### Guardrails
- bridge는 handler layer에서만; storage layer (`correction_store.py`, `preference_store.py`) 변경 없음
- preference 활성화·승인 흐름 변경 없음 (candidate 생성까지만)
- UI 버튼은 `available_to_sync_count > 0`일 때만 노출 (이미 동기화된 경우 숨김)

#### Shipped Infrastructure (Axes 1–3, 2026-04-24)
- Axis 1 (seq 127): `PreferenceHandlerMixin.sync_adopted_corrections_to_candidates()` + `POST /api/corrections/sync-adopted-to-candidates` — adopted correction → preference candidate backend bridge
- Axis 2 (seq 128): `PreferencePanel` `data-testid="sync-adopted-btn"` — 버튼 노출, 클릭 후 inline 피드백, audit reload
- Axis 3 (seq 129): `get_preference_audit()` `available_to_sync_count` — 실제 동기화 가능 수 반환; 버튼 조건 교체

- **Milestone 29 closed** (Axes 1–3): reviewed-memory loop 중 correction adoption → preference candidate 연결 완료

### Milestone 30: Watcher Core Structural Decomposition

#### Goal
`watcher_core.py`의 legacy 부채 제거 및 순수 파싱 로직을 별도 모듈로 분리.

#### Guardrails
- `pipeline_runtime/` 수정 없음
- `tests/test_watcher_core.py` 기존 테스트 계약 유지 (mock.patch target 포함)
- 보존 함수 4개 (`_line_looks_like_input_prompt`, `_pane_text_has_gemini_ready_prompt`, `_pane_has_input_cursor`, `_pane_has_working_indicator`) 수정 없음

#### Shipped Infrastructure (Axes 1–3, 2026-04-25)
- Axis 1 (seq 136-137): pane-surface stub 7개 (`_capture_pane_text`, `wait_for_pane_settle`, 등) 제거; 내부 호출 `_shared_*`로 교체; 202 unit tests PASS
- Axis 2 (seq 141-142): `_LegacyPatchableSharedCall` 프록시 및 `_install_legacy_patch_target` 7회 호출 제거; `tests/test_watcher_core.py` legacy patch target 112곳 → canonical `_shared_*` 마이그레이션; 202 unit tests PASS
- Axis 3 (seq 144-145): 신호 추출 순수 함수 11개 + regex 상수 12개 → `watcher_signals.py` 신규 모듈 분리; `watcher_core.py` import 교체로 기존 `watcher_core.*` 이름 바인딩 유지; `tests/test_watcher_signals.py` 신규 10개 테스트; 202 + 10 tests PASS; `watcher_core.py` 5001 → 4608 lines

- **Milestone 30 closed** (Axes 1–3): watcher_core legacy debt 제거 및 신호 추출 모듈 분리 완료

### Milestone 31: E2E Infrastructure + Reviewed-Memory Loop Smoke

#### Goal
M28–M30 bundle release gate 통과 및 reviewed-memory loop end-to-end 검증.

#### Guardrails
- E2E webServer spawn fix는 Makefile + playwright.config.mjs에 한정
- smoke test는 `e2e/tests/web-smoke.spec.mjs`에 1개 시나리오 추가

#### Shipped Infrastructure (Axes 1–2, 2026-04-25)
- Axis 1 (seq 148–151): E2E webServer spawn PermissionError 수정 — `e2e/playwright.config.mjs` `reuseExistingServer: true`, `Makefile` e2e-test pre-start server; M28–M30 bundle gate **146 E2E passed (6.0m)**, 216 unit tests OK
- Axis 2 (seq 154–155): reviewed-memory loop E2E smoke — correction → candidate accept → sync UI → real preference activation → `[모의 응답, 선호 1건 반영]` prefix; **147 E2E passed (6.6m)**

- **Milestone 31 closed** (Axes 1–2): release gate 통과 및 reviewed-memory loop end-to-end smoke 완료

### Milestone 32: Watcher Core Structural Decomposition (Dispatch)

#### Goal
`watcher_core.py` dispatch/tmux 헬퍼를 기존 `watcher_dispatch.py`로 분리.

#### Guardrails
- `pipeline_runtime/`, `tests/test_watcher_core.py` 수정 없음 (mock.patch 계약 유지)
- `watcher_dispatch.py` 기존 `DispatchIntent`, `WatcherDispatchQueue` 유지

#### Shipped Infrastructure (Axes 1–2, 2026-04-25)
- Axis 1 (seq 157–158): dispatch/tmux 헬퍼 13개 + 상수 3개 → `watcher_dispatch.py`; `watcher_core.py` re-export로 `mock.patch("watcher_core.tmux_send_keys")` 계약 유지; 216 unit tests OK
- Axis 2 (seq 160–161): `_watcher_core_compat` shim + 9개 thin wrapper 제거; `CodexDispatchConfirmationTest` patch 대상 `watcher_dispatch.*`로 정규화; 216 unit tests OK; `watcher_core.py` 5001 → ~4360 lines (M30 시작 대비)

- **Milestone 32 closed** (Axes 1–2): dispatch/tmux 구조 분리 및 compat shim 제거 완료

### Milestone 33: Watcher Core Structural Decomposition (State + Stabilizer)

#### Goal
`watcher_core.py`에서 coordination state 클래스와 artifact 안정화 로직을 별도 모듈로 분리.

#### Guardrails
- `tests/test_watcher_core.py` 수정 없음 (`watcher_core.*` re-export 계약 유지)
- `compute_file_sha256`, `StabilizeSnapshot`, `ArtifactStabilizer`는 Axis 2에서 처리

#### Shipped Infrastructure (Axes 1–2, 2026-04-25)
- Axis 1 (seq 163–164): `WatcherTurnState`, `LeaseData`, `ControlSignal`, `PaneLease`, `DedupeGuard`, `ManifestCollector` → `watcher_state.py` 신규 모듈; optional jsonschema import 포함; 216 unit tests OK
- Axis 2 (seq 166–167): `compute_file_sha256`, `StabilizeSnapshot`, `ArtifactStabilizer` → `watcher_stabilizer.py` 신규 모듈; 216 unit tests OK; watcher 모듈 패밀리 5개 완성: `watcher_core`(3977 lines) / `watcher_state`(364) / `watcher_dispatch`(640) / `watcher_signals`(450) / `watcher_stabilizer`(63)

- **Milestone 33 closed** (Axes 1–2): coordination state + artifact stabilizer 구조 분리 완료; watcher_core.py 5001 → 3977 lines (M30 시작 대비 -1024 lines)

### Milestone 34: Applied Preference Loop Visibility

#### Goal
chat 응답에 적용된 선호가 브라우저 새로고침 후에도 badge로 유지되도록 복원 경로 수정.

#### Guardrails
- backend preference store 스키마 변경 없음
- applied_preference_ids → applied_preferences 복원은 read-path만 변경

#### Shipped Infrastructure (Axes 1–2, 2026-04-25)
- Axis 1 (seq 172–173): `_serialize_session`에서 `applied_preference_ids` fingerprint → preference descriptions 복원; `MessageBubble.tsx` `data-testid="applied-preferences-badge"` 추가; E2E 시나리오 147에 badge assertion 추가
- Axis 2 (seq 175–176): M28–M34 bundle release gate **148 E2E passed (7.5m)**, 229 unit tests OK; Makefile stale-server kill 추가

- **Milestone 34 closed** (Axes 1–2): applied preference badge 복원 완료; 브라우저 새로고침 후에도 badge 표시

### Milestone 35: Interactive Applied Preference Management

#### Goal
applied-preferences badge를 클릭 가능한 interactive button으로 전환; popover에서 직접 선호를 관리(일시중지, description 편집, snippet 확인).

#### Guardrails
- backend `pausePreference`, `updatePreferenceDescription`, `fetchPreferences` API 기구현 재사용
- E2E 시나리오는 DB 누적 상태에 내성 있는 functional flow assertion으로 설계

#### Shipped Infrastructure (Axes 1–2, 2026-04-25)
- Axis 1 (seq 179–183): badge span → interactive button; popover 내 preference 목록 + `preference-pause-btn`; 외부 클릭 닫기; E2E 시나리오 148 추가 (badge click → popover → pause → status paused); **148 E2E passed (7.5m)**
- Axis 2 (seq 185–186): popover 내 `original_snippet`/`corrected_snippet` 표시 (`pref-original-snippet`, `pref-corrected-snippet`); description inline edit (`pref-description-edit`, 저장/취소); `fetchPreferences` on popover open; **148 E2E passed (7.5m)**, 229 unit tests OK

- **Milestone 35 closed** (Axes 1–2): applied preference badge interactive 관리 완료

### Milestone 36: Preference Pause Lifecycle Verification

#### Goal
pause 동작이 UI 상태 변경에서 끝나지 않고 실제 applied preference 카운트를 줄이며, 브라우저 새로고침 후에도 영속됨을 E2E로 검증.

#### Guardrails
- backend/frontend 로직 변경 없음 — E2E assertion 확장만
- accumulated DB 환경에서도 동작하는 count 기반 assertion (N-1) 사용

#### Shipped Infrastructure (Axes 1–2, 2026-04-25)
- Axis 1 (seq 192–193): pause 후 두 번째 chat → badge count N-1 확인 (148 E2E passed, 8.7m)
- Axis 2 (seq 195–196): page.reload() 후 세 번째 chat → count N-1 유지 확인 (148 E2E passed, 12.2m); PR #34 merge됨

- **Milestone 36 closed** (Axes 1–2): preference pause의 기능적 억제 효과 및 세션 재로드 영속성 검증 완료

### Milestone 37: Infrastructure Hardening + Preference Lifecycle Closure

#### Goal
SQLite migration rollout을 종결하고, preference resume/reject lifecycle 및 누적 DB 환경에서도 안정적인 reviewed-memory E2E assertion을 확보.

#### Guardrails
- M37 Axis 2는 E2E assertion 및 fixture cleanup 범위에 한정
- 누적 active preference cap 환경에서도 동작하는 count-agnostic assertion 유지
- release/publish 작업은 operator approval boundary를 통과한 뒤 수행

#### Shipped Infrastructure (Axes 1–2, 2026-04-25/26)
- Axis 1 (seq 204–205): `migrate_json_to_sqlite` 호출에 sessions/artifacts/preferences dirs 전달 완성; backlog truth-sync. 30 SQLite tests OK.
- Axis 2 (seq 207–213): preference resume/reject lifecycle E2E (시나리오 149) + count-agnostic fix (시나리오 147/148). 149 E2E passed (13.5m).

- **Milestone 37 closed** (Axes 1–2): SQLite 전체 마이그레이션 완성 + preference lifecycle (pause/resume/reject) E2E closure 완료

### Milestone 38: Test Infrastructure Robustness

#### Goal
`make e2e-test`가 서버 기동 상태와 무관하게 안정적으로 동작하도록 E2E 실행 환경 isolation을 구현하고 wrapper를 강화한다.

#### Guardrails
- 기존 Playwright 시나리오 수정 없이 서버 관리 레이어만 변경
- existing-server 재사용 경로 로직 검증; full E2E는 sandbox 제약으로 non-sandbox 확인 필요

#### Shipped Infrastructure (Axes 1–2, 2026-04-26)
- **Milestone 38 closed** (Axes 1–2): `e2e/start-server.sh` healthcheck wrapper 구현 (Axis 1, commit `da6d27e`, 150 passed); `set -e` 하드닝 + doc closure (Axis 2, commit `082f33e`).

### Milestone 39: Review Evidence Enrichment

#### Goal
운영자가 review queue 후보를 판단할 때 필요한 정성적 대화 맥락과 정량적 증거 강도를 함께 제공한다.

#### Guardrails
- 기존 `ReviewQueueItem` 필드 제거/수정 없이 additive 확장만 허용
- browser E2E는 sandbox 제약으로 unit test + TypeScript 타입 체크로 대체

#### Shipped Infrastructure (Axes 1–2, 2026-04-26)
- **Milestone 39 closed** (Axes 1–2): `context_turns` 직렬화 — 직전 3턴 대화 맥락 (Axis 1, commit `774dbe1`); `evidence_summary` 직렬화 — artifact/signal/confirmation/recurring session 카운트 (Axis 2, commit `c33af44`).

### Milestone 40: Review Auditability

#### Goal
운영자가 review queue 후보를 판단할 때 출처 세션과 결정 사유를 함께 확인해 감사 추적이 가능하게 한다.

#### Guardrails
- 기존 `ReviewQueueItem` 필드 제거/수정 없이 additive 확장만 허용
- durable candidate path의 `candidate_review_record`는 이미 `reason_note`를 처리하므로 수정 불필요
- browser E2E는 sandbox 제약으로 unit test + TypeScript 타입 체크로 대체

#### Shipped Infrastructure (Axes 1–2, 2026-04-26)
- **Milestone 40 closed** (Axes 1–2): `source_session_id`/`source_session_title` 직렬화 — review queue 항목에 출처 세션 연결 (Axis 1, commit `c660ae6`); `reason_note` UI 입력 + global `source_refs` 저장 — 결정 사유 감사 추적 (Axis 2, commit `1526d64`).

### Milestone 41: Preference Auditability & Visibility

#### Goal
Preference 관리 뷰에서 각 선호도가 어떤 세션에서, 어떤 결정 사유로 생성됐는지 운영자가 직접 확인할 수 있게 한다.

#### Guardrails
- 기존 `PreferenceRecord` 필드 제거/수정 없이 additive 확장만 허용
- preference store 스키마 직접 수정 없이 기존 source_refs 저장 구조 활용
- browser E2E는 sandbox 제약으로 unit test + TypeScript 타입 체크로 대체

#### Shipped Infrastructure (Axis 1, 2026-04-26)
- **Milestone 41 closed** (Axis 1): `session_title`/`reason_note`를 global + durable ACCEPT preference `source_refs`에 저장; `list_preferences_payload`에서 `review_reason_note`/`source_session_title` top-level 노출; `PreferencePanel`에 audit block 표시 (commit `19dcb94`).

### Milestone 42: Preference Status Management UI

#### Goal
PreferencePanel에서 status별 필터 탭을 제공해 candidate/active/paused 선호를
구분해서 볼 수 있게 한다.

#### Guardrails
- A1-γ (same-session prompt injection)는 이번 Milestone 범위 밖
- 기존 activate/pause/reject 버튼 동작 변경 없이 UI 레이어만 추가
- browser E2E는 sandbox 제약으로 unit test + TypeScript 타입 체크로 대체

#### Shipped Infrastructure (Axis 1, 2026-04-26)
- **Axis 1 shipped**: `list_preferences_payload`에 `paused_count`를 추가하고, `PreferencePanel`에 전체/후보/활성/일시중지 status 필터 탭과 탭별 count 표시를 추가.

### Milestone 43: Preference Transition Auditability

#### Goal
activate / pause / reject 상태 전환 시 사용자가 선택적 이유 메모(transition_reason)를
입력할 수 있게 하고, 서버가 이를 task log detail에 남긴다.

#### Guardrails
- preference store 내부 스키마 변경 없음
- cross-session persistence, cloud storage 범위 밖
- browser E2E는 sandbox 제약으로 TypeScript 타입 체크와 handler 단위 테스트로 대체

#### Shipped Infrastructure (Axis 1, 2026-04-26)
- `activate_preference`, `pause_preference`, `reject_preference` 핸들러에 선택적
  `transition_reason` 파라미터 추가; task log detail에 기록.
- `activatePreference`, `pausePreference`, `rejectPreference` API client 함수에
  `transitionReason?: string` 추가; 값이 있을 때만 payload에 포함.
- `PreferencePanel` `handleAction`: 전환 전 `window.prompt()`로 이유 수집;
  취소(`null`)이면 전환 중단, 기존 conflict confirm 및 reject fade-out 흐름 유지.

## Next 3 Implementation Priorities

1. **E2E 환경 개선 완료**: `e2e/start-server.sh` healthcheck wrapper no-server / existing-server 두 경로가 정적 감사(09c806d)로 확인됨. operator가 검증 수준을 release gate로 인정(Q1 Option A, operator_request 263). B1 gate closed (2026-04-26).
2. **M43 Axis 2 방향**: M43 Axis 1 이후 다음 preference auditability 확장 (transition_reason UI 개선 / audit depth / 기타)을 advisory에서 결정.

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
