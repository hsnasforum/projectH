# projectH

`projectH`는 **로컬 퍼스트 문서 비서 웹 MVP**이며, 첫 번째 reviewed-memory slice (review queue `검토 후보`, aggregate apply trigger `검토 메모 적용 후보`, emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility)가 출하되어 있습니다.
사용자는 로컬 파일을 읽고, 요약하고, 검색하고, 필요할 때만 승인 기반으로 저장할 수 있습니다. 웹 검색은 핵심 제품이 아니라 **보조 조사 모드**로 제한적으로 붙어 있습니다.

## Phase Split

### Current Shipped Contract
- 로컬 퍼스트 문서 비서 웹 MVP
- 핵심 루프: 문서 읽기 -> grounded summary -> 후속 질의 -> 승인 기반 저장
- 응답 피드백 수집, grounded-brief trace anchor, corrected-outcome capture, corrected-save bridge, reject/reissue reason traces
- review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility
- 웹 조사는 secondary mode

## Release Candidate Scope

현재 릴리즈 후보 범위는 **`python3 -m app.web` 기준 문서 비서 본체**입니다.

- 포함:
  - `/app` 웹 셸
  - 로컬 문서 읽기 / 요약 / 검색
  - 세션 / 승인 기반 저장
  - evidence / source / grounded-brief trace
  - 웹 조사 secondary mode
- 제외:
  - `controller.server`
  - `pipeline_gui/`
  - `windows-launchers/`
  - `_data/` 기반 pipeline/token collector tooling

repo 안의 internal/operator tooling은 릴리즈 게이트 밖이지만 계속 유지됩니다. 현재 internal pipeline runtime은 `supervisor`가 run-scoped `status.json` / `events.jsonl` / `receipt`를 단일 writer로 관리하고, `controller.server`, `pipeline_gui`, `pipeline-launcher.py`는 그 surface만 읽는 thin-client 경계를 사용합니다. `tmux`는 attach/debug substrate로만 남고, 상위 계층은 pane/log/file scan을 current truth로 사용하지 않습니다. degraded 상태는 대표 `degraded_reason`과 전체 `degraded_reasons` 목록으로 함께 노출됩니다. `pipeline_gui` 운영 화면은 오른쪽 파일 박스를 `라운드 기록`으로 표시하고, generic한 "산출물 없음" 식 wording 대신 최신 `/work`·`/verify`와 현재 라운드 receipt 미기록 상태를 구분해 보여줍니다. 이때 최신 `/work`·`/verify`는 각각 `work/<month>/<day>/YYYY-MM-DD-*.md`, `verify/<month>/<day>/YYYY-MM-DD-*.md` 형식의 canonical round note만 가리키며, `work/README.md`나 `verify/README.md` 같은 metadata 문서는 최신 artifact로 surface하면 안 됩니다.

위 제외 항목들은 현재 repo 안에 함께 존재하지만, 이번 릴리즈 게이트의 기본 판정 대상은 아닙니다.

### Current Reviewed-Memory Boundary
- `grounded brief` 1개가 공식 artifact로 고정됨
- review queue (`검토 후보`)와 aggregate apply trigger (`검토 메모 적용 후보`)는 이미 출하
- emitted/apply/result/active-effect 경로 및 stop-apply / reversal / conflict-visibility도 이미 출하

### Next Phase Design Target
- 출하된 reviewed-memory 기반 위에 broader structured correction memory를 구조화
- durable preference memory, cross-session memory, user-level memory는 아직 미출하
- 이 단계는 문서 설계 계약 고정 단계이며, 아직 모델 학습이나 프로그램 조작 구현 단계가 아닙니다

### Long-Term North Star
- 사용자가 가르치면 길들여지고, 나중에는 승인 기반 로컬 행동까지 확장되는 로컬 개인 에이전트
- 프로그램 조작과 모델 적응 계층은 그 이후 단계입니다

## Current Product Slice

현재 구현된 웹 MVP는 아래를 포함합니다. (review queue `검토 후보`, aggregate apply trigger `검토 메모 적용 후보`, reviewed-memory active-effect 경로 포함)

- local web shell (`python3 -m app.web`)
- response feedback capture
- grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, and artifact-linked reject/reissue reason traces
- recent sessions / conversation timeline with per-message timestamps
- file summary / document search / general chat
- document search responses include a structured search result preview panel showing each matched file's ordered label (with full path tooltip), match type badge (`파일명 일치` / `내용 일치`), and a content snippet; both search-only and search-plus-summary responses carry the same `search_results` data; search-only responses hide the redundant text body in both the transcript and the response detail box, letting the preview cards serve as the primary surface; search-only responses also show a `선택 경로 복사` button that copies the selected path list to clipboard with a `선택 경로를 복사했습니다` notice; search-plus-summary responses show the visible summary body alongside preview cards in both the response detail and the transcript
- approval-based save with default notes directory shown in the save-path placeholder
- reissue approval flow
- evidence / source panel with source-role trust labels on each evidence item
- summary source-type label (`문서 요약` for local document summary, `선택 결과 요약` for selected search results) in both quick-meta bar and transcript message meta; single-source responses show basename-based `출처 <filename>` in both surfaces, multi-source responses show count-based `출처 N개` instead of raw filenames; general chat responses carry no source-type label
- summary span / applied-range panel
- response origin badge with separate answer-mode badge for web investigation (`설명 카드` / `최신 확인`), source-role trust labels, and verification strength tags in origin detail
- applied-preferences badge (`선호 N건 반영`) on assistant messages when `applied_preferences` is non-empty, with tooltip showing preference descriptions
- copy-to-clipboard buttons: `본문 복사`, `저장 경로 복사`, `승인 경로 복사`, `검색 기록 경로 복사`, `경로 복사` (selected source paths panel); all share one helper that shows clipboard-specific failure notice on both success-path rejection and fallback failure
- streaming progress + cancel
- response feedback capture
- grounded-brief artifact trace anchor on summary responses, save approvals, and relevant local traces
- normalized original-response snapshot, minimum `accepted_as_is` / `corrected` content-outcome capture, and minimum reject / reissue approval reason capture on grounded-brief traces
- small grounded-brief correction editor seeded with the current draft text, with explicit correction submit kept separate from save approval; correction submit also updates the session `active_context.summary_hint` so that subsequent follow-up responses and re-summaries in the same session use the corrected text as their basis
- current save approvals and save/write traces now expose `save_content_source = original_draft | corrected_text` plus explicit `source_message_id` anchoring to the original grounded-brief source message
- minimum corrected-save bridge action that stays always visible inside the correction area, stays disabled until a recorded `corrected_text` exists, creates a fresh approval from that recorded text, freezes the approval snapshot under a new `approval_id`, and reuses the same `artifact_id` / `source_message_id` with `save_content_source = corrected_text`
- one small candidate-linked confirmation action on the grounded-brief response card that appears only when the current `session_local_candidate` exists and persists one separate source-message `candidate_confirmation_record`
- one optional source-message-anchored `durable_candidate` projection plus one local `검토 후보` section fed only by current pending `review_queue_items`, with `accept`/`reject`/`defer` review actions that record source-message `candidate_review_record`, remove the item from the pending queue, and persistently show the review outcome (`검토 수락됨`/`검토 거절됨`/`검토 보류됨`) on the source-message transcript meta
- one separate aggregate-level `검토 메모 적용 후보` section fed only by current same-session `recurrence_aggregate_candidates` (current-version only; retired automatically when any supporting correction is superseded before transition emit; record-backed lifecycle aggregates survive supersession), shown adjacent to `검토 후보` only when aggregates exist, with one visible-but-disabled `검토 메모 적용 시작` action per aggregate card plus blocked helper copy only; each aggregate card shows a visible review-support line (`검토 수락 N건 / 교정 M건 (거절·보류는 감사 기록만)`) derived from accept-only `supporting_review_refs`; transition-backed aggregate cards prefix the line with `[기록된 기준]` to indicate the displayed counts describe the persisted recorded basis behind the lifecycle card
- short-summary, per-chunk chunk-note, and reduce prompts, plus the internal `summary_chunks` anchor-selection heuristic, now all reuse the same truthful source boundary already known to current call sites, so local file or uploaded-document summaries keep document-flow and narrative-friendly guidance with a strict source-anchored faithfulness rule (no fabricated events, no term substitution, no conclusions beyond what the text shows) while selected local search-result summaries keep source-backed synthesis guidance with multi-result summaries using comparative wording and single-result summaries using non-comparative wording, without adding a new mode toggle or classifier
- PDF text-layer reading: readable text-layer PDF는 visible summary body로 정상 요약되고(`문서 요약` label, context box/quick meta/transcript meta에 PDF 파일명 표시), scanned/image-only PDF는 visible OCR-not-supported guidance(`요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`)를 반환
- uploaded folder search shows a count-only partial-failure notice when some files cannot be read, while retaining readable-file result preview (search-only and search-plus-summary both preserve preview cards with ordered label, full-path tooltip, match badge, and snippet for successfully read files)
- permission-gated web investigation with local JSON history, answer-mode badges, color-coded verification-strength badges (entity-card verification badge is downgraded from strong when no claim slot has cross-verified status), color-coded source-role trust badges, and investigation progress summary in history cards
- claim coverage panel with status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`), actionable hints for weak or unresolved slots, source role with trust level labels, a color-coded fact-strength summary bar above the response text, and a dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved) for web investigation

## Chosen Next-Phase Artifact

다음 단계의 공식 artifact는 `grounded brief`입니다.

- 현재 codebase가 이미 단일 문서를 읽고 요약 본문과 저장 미리보기를 만드는 흐름에 가장 잘 맞습니다
- evidence, summary chunks, approval preview, feedback을 한 단위에 묶기 쉽습니다
- memo보다 범용적이고, action-item note보다 좁지 않아서 correction memory의 기준 단위로 적합합니다

## Run

- CLI:
  - `python3 -m app.main README.md --provider mock`
- Local web shell:
  - `python3 -m app.web`
- Default URL:
  - `http://127.0.0.1:8765/app`
- Current shipped browser contract:
  - `/app` is the shipped web shell route
  - `/` redirects to `/app`
  - the shipped shell currently serves the existing template/static UI (`app/templates/index.html` + `/static/app.js`)
  - the React build remains preview-only at `/app-preview`, and its build assets are served from `/assets/*`
  - WSL에서 실행하면 Windows 브라우저 접근을 위해 기본 bind host를 `0.0.0.0`로 잡고, 시작 로그에 `Windows fallback: http://<WSL-IP>:8765/app`를 함께 출력합니다.
- Internal pipeline controller:
  - `python3 -m controller.server`
  - `http://127.0.0.1:8780/controller`
  - internal/operator tool only; not part of the current release-candidate browser contract
  - canonical runtime API는 `/api/runtime/status`, `/api/runtime/start|stop|restart`, `/api/runtime/capture-tail?lane=`, `/api/runtime/send-input`입니다.
  - controller/browser UI는 supervisor가 쓴 run-scoped runtime status만 읽고, direct pane/log/file scan을 current truth로 사용하지 않습니다.
  - stop은 graceful flush 우선입니다. CLI/controller는 먼저 final `STOPPED` status flush를 기다리고, timeout 뒤에만 강제 종료 fallback을 사용합니다. supervisor가 이미 사라진 orphan watcher/session만 남아 있으면 stop이 이를 정리하고 `status.json`을 `control=none`, `active_round=null`, watcher dead, lane `OFF`로 보정합니다.
  - 이미 receipt로 닫힌 duplicate `STATUS: implement` handoff는 debug용 `compat.control_slots`에는 남아도, canonical `control` block에서는 `none`으로 내려 controller가 `implement + all READY` 같은 stale 표기를 하지 않게 합니다.
  - recent runtime snapshot이 supervisor/pid 없이 불완전하게 남아 있거나, 같은 ambiguous snapshot에 `updated_at`까지 비어 있으면 controller는 이를 즉시 `STOPPED/BROKEN`으로 단정하지 않고 uncertain `DEGRADED`(`supervisor_missing_recent_ambiguous` / `supervisor_missing_snapshot_undated`)로 표기합니다.
  - `.pipeline/operator_request.md`는 `CONTROL_SEQ`, `REASON_CODE`, `OPERATOR_POLICY`, `DECISION_CLASS`, `DECISION_REQUIRED`, `BASED_ON_WORK`, `BASED_ON_VERIFY`를 top header로 함께 두는 편이 canonical입니다. supervisor는 `OPERATOR_POLICY` 우선, `REASON_CODE` 다음 순서로 publish/gate를 판정하고, 구조화 metadata가 없거나 알 수 없으면 fail-safe로 즉시 publish합니다.
  - 구조화 metadata가 있는 `needs_operator`만 24시간 gate 대상이 됩니다. `safety_stop`, `approval_required`, `truth_sync_required`는 즉시 publish하고, 그 밖의 gated candidate는 `autonomy.recovery|triage|hibernate|pending_operator`로 먼저 surface합니다.
  - gate된 operator candidate는 canonical `control` block에서는 `none`으로 내려가고, status의 `autonomy` block(`mode`, `block_reason`, `suppress_operator_until`, `operator_eligible` 등)으로만 노출됩니다. 오래 방치된 stop은 watcher가 Codex 재심사(`operator_wait_idle_retriage` 또는 gated follow-up)로 다시 넘깁니다.
  - browser log modal은 tail read-model 위에 bounded one-line lane input(`POST /api/runtime/send-input`)을 함께 제공합니다. permission/plan prompt처럼 operator 선택이 필요한 경우 현재 열린 lane에 `1`, `2`, `3` 같은 짧은 응답을 바로 보낼 수 있습니다. lane pause/resume/restart나 attach 같은 backend 미연결 액션은 계속 노출하지 않습니다.
  - Office View background는 `/controller-assets/background.png`를 우선 사용하고, 필요할 때만 `/controller-assets/generated/bg-office.png`로 fallback하며, sidebar `Scene` 상태와 event log로 load/fallback/error를 표시합니다.
  - `ready` / `idle` 상태 에이전트는 자기 데스크 존(`claude_desk`, `codex_desk`, `gemini_desk`) 안에서 zone-bounded 연속 micro-roam을 수행합니다. 각 에이전트는 `_pickIdleTarget()`이 자기 홈 존의 중심 주변에서 무작위 지점을 선택한 뒤 zone 경계로 clamp해 desk 밖 / 벽 / 가구 위에 서지 않도록 합니다. 존이 서로 분리되어 있으므로 idle 에이전트 사이의 겹침(stacking)이 자연스럽게 방지되고, 별도의 proximity anti-stacking이나 `_roamHistory` spot 방문 penalty는 더 이상 필요하지 않습니다. `window.testAntiStacking`은 zone-bounded 대응을 위해 `testPickIdleTargets`에 위임하고, `window.testHistoryPenalty`는 spot 기반 개념이 사라졌으므로 빈 배열을 반환합니다. `working` / `booting` / `broken` / `dead` 에이전트는 기존 desk/status 고정 동작을 유지합니다.
  - live fault / soak harness는 `python3 scripts/pipeline_runtime_gate.py ...` 경로를 사용합니다.
  - WSL에서 실행하면 Windows 브라우저 접근을 위해 기본 bind host를 `0.0.0.0`로 잡고, 브라우저 URL은 계속 `127.0.0.1` 기준으로 안내합니다.
  - 만약 Windows에서 `127.0.0.1:8780`이 안 열리면, 시작 로그에 함께 출력되는 `Windows fallback: http://<WSL-IP>:8780/controller` 주소를 사용하시면 됩니다.
  - Windows localhost 고정 매핑이 필요하면 관리자 PowerShell에서 `windows-launchers/configure-controller-portproxy.ps1`를 실행해 `127.0.0.1:8780 -> 현재 WSL IP:8780` portproxy를 잡을 수 있습니다.

## Verification

- Unit/service regression:
  - `python3 -m unittest -v`
- Browser smoke install:
  - `make e2e-install`
- Browser smoke run:
  - `make e2e-test`

## Playwright Smoke Coverage

Current smoke scenarios:
1. file summary renders evidence/source panel, summary span / applied-range panel, per-message timestamps in the transcript, response copy button state with clipboard write verification, source filename in quick-meta and transcript meta, note-path default-directory placeholder, and `문서 요약` source-type label in both quick-meta and transcript meta
2. browser file picker summary flow with source filename and `문서 요약` source-type label in both quick-meta and transcript meta
3. browser folder picker search flow with `선택 결과 요약` source-type label and multi-source count-based metadata (`출처 2개`) in both quick-meta and transcript meta, plus response detail preview panel alongside summary body with both cards' ordered labels, full-path tooltips, match badges (`파일명 일치` / `내용 일치`), and snippet text content, and transcript preview panel with item count, both cards' ordered labels, full-path tooltips, match badges (`파일명 일치` / `내용 일치`), and snippet text content
4. pure search-only response with transcript preview cards visible, transcript body text hidden, response detail box preview cards visible, response body text hidden, copy-text button hidden, `selected-copy` button visibility with click/notice/clipboard verification, full-path tooltip on preview card ordered labels, and match-type badge (`파일명 일치` / `내용 일치`) plus content snippet text on preview cards in both response detail and transcript
5. approval reissue with changed save path
6. approval-backed note save
7. late flip after explicit original-draft save keeps saved history while latest content verdict changes
8. `내용 거절` content-verdict path with same-card reject-note update, pending approval preserved, and later explicit save supersession
9. corrected-save first bridge path
10. corrected-save saved snapshot remains while late reject and later re-correct move the latest state separately
11. candidate-linked explicit confirmation path stays outside approval UI, remains distinct from save support on the same source message, records `candidate_confirmation_record`, surfaces one `검토 후보` with `검토 수락`/`거절`/`보류`, records source-message `candidate_review_record`, removes the pending queue item without applying user-level memory, retains review-outcome quick-meta on plain follow-up responses, and drops review-outcome quick-meta after a later correction creates a newer unreviewed context
12. same-session recurrence aggregate path renders one separate `검토 메모 적용 후보` section only after an aggregate exists, keeps `검토 메모 적용 시작` visible but disabled, keeps the queue-side review actions separate, preserves `reviewed_memory_transition_record` absence, after transition record emission, a hard page reload still shows the emitted helper text, payload continuity (`record_stage = emitted_record_only_not_applied`, `applied_at` absent, `apply_result` absent, `reviewed_memory_active_effects` absent or empty), apply button visible and enabled, and a post-reload follow-up does not include `[검토 메모 활성]`; after `검토 메모 적용 실행`, a hard page reload still shows the applied-pending helper text, payload continuity (`record_stage = applied_pending_result`, `applied_at` present, `apply_result` absent, `reviewed_memory_active_effects` absent or empty), `결과 확정` button visible and enabled, and a post-reload follow-up does not include `[검토 메모 활성]`; after `결과 확정` with active effect, a hard page reload still shows the active-effect result indicator, helper text, payload continuity (`record_stage = applied_with_result`, `result_stage = effect_active`, `reviewed_memory_active_effects` present), and a post-reload follow-up still includes `[검토 메모 활성]`; after `적용 중단`, a hard page reload still shows the stopped indicator and helper text, payload continuity (`record_stage = stopped`, `result_stage = effect_stopped`, `reviewed_memory_active_effects` absent or empty), and a post-reload follow-up does not include `[검토 메모 활성]`; after `적용 되돌리기`, a hard page reload still shows the reversed indicator and helper text, payload continuity (`record_stage = reversed`, `result_stage = effect_reversed`, `reviewed_memory_active_effects` absent or empty), and a post-reload follow-up does not include `[검토 메모 활성]`; after the full lifecycle reaches `reversed` + `conflict_visibility_checked`, a second hard page reload still shows the `검토 메모 적용 후보` section with `충돌 확인 완료` and `적용 되돌림 완료` badges, the conflict-checked helper text, and payload continuity (`reviewed_memory_transition_record.record_stage = reversed`, `reviewed_memory_conflict_visibility_record.record_stage = conflict_visibility_checked`)
13. streaming cancel
14. general chat negative source-type label contract (no `문서 요약` / `선택 결과 요약` in quick-meta or transcript meta)
15. claim-coverage panel rendering contract with `[교차 확인]`, `[단일 출처]`, `[미확인]` leading status tags, actionable hints, source role with trust level labels, color-coded fact-strength summary bar, and dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved with natural Korean particle normalization)
16. web-search history card header badges: answer-mode badge (`설명 카드` / `최신 확인`), verification-strength badge (`검증 강` / `검증 중` / `검증 약` with CSS class), source-role trust badge compact label (`공식 기반(높음)` / `보조 기사(보통)` / `보조 커뮤니티(낮음)` with trust class), investigation progress summary text when `claim_coverage_progress_summary` is non-empty
17. history-card entity-card `다시 불러오기` 클릭 후 history card의 investigation progress summary 표시 및 reloaded response의 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source-role detail 유지 확인
18. history-card latest-update `다시 불러오기` 클릭 후 reloaded response의 `WEB` origin badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source-role detail 유지 확인
19. history-card entity-card `다시 불러오기` 후 follow-up 질문에서 `WEB` badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source-role detail이 drift하지 않는지 확인
20. history-card latest-update `다시 불러오기` 후 follow-up 질문에서 `WEB` origin badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source-role detail이 drift하지 않는지 확인
21. history-card latest-update `다시 불러오기` 후 noisy community source(`보조 커뮤니티`, `brunch`)가 본문, origin detail, context box에 미노출되고, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`만 유지되는지 확인
22. history-card entity-card `다시 불러오기` 후 noisy single-source claim(`출시일`/`2025`/`blog.example.com`)이 미노출되고, `설명형 다중 출처 합의`, `백과 기반`, agreement-backed 사실 카드(`확인된 사실 [교차 확인]:`, `교차 확인`) 유지, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance가 유지되는지 확인
23. history-card entity-card `다시 불러오기` 후 dual-probe source path(`pearlabyss.com/200`, `pearlabyss.com/300`)가 context box에 유지되고, `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `공식 기반` · `백과 기반` source role이 유지되는지 확인
24. history-card latest-update `다시 불러오기` 후 mixed-source source path(`store.steampowered.com`, `yna.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source role이 유지되는지 확인
25. history-card latest-update single-source `다시 불러오기` 후 `단일 출처 참고` verification label과 `보조 출처` source role이 origin detail에 유지되는지 확인
26. history-card latest-update news-only `다시 불러오기` 후 `기사 교차 확인` verification label과 `보조 기사` source role이 origin detail에 유지되는지 확인
27. history-card latest-update news-only `다시 불러오기` 후 기사 source path(`hankyung.com`, `mk.co.kr`)가 context box에 유지되는지 확인
28. history-card latest-update single-source `다시 불러오기` 후 source path(`example.com/seoul-weather`)가 context box에 유지되는지 확인
29. history-card latest-update single-source `다시 불러오기` 후 follow-up 질문에서 `WEB` origin badge, `최신 확인` answer-mode badge, `단일 출처 참고` verification label, `보조 출처` source role이 drift하지 않는지 확인
30. history-card latest-update news-only `다시 불러오기` 후 follow-up 질문에서 `WEB` origin badge, `최신 확인` answer-mode badge, `기사 교차 확인` verification label, `보조 기사` source role이 drift하지 않는지 확인
31. history-card entity-card `다시 불러오기` 후 follow-up 질문에서 dual-probe source path(`pearlabyss.com/200`, `pearlabyss.com/300`)가 context box에 유지되고, `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `공식 기반` · `백과 기반` source role이 drift하지 않는지 확인
32. history-card latest-update mixed-source `다시 불러오기` 후 follow-up 질문에서 source path(`store.steampowered.com`, `yna.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source role이 drift하지 않는지 확인
33. history-card latest-update single-source `다시 불러오기` 후 follow-up 질문에서 source path(`example.com/seoul-weather`)가 context box에 유지되는지 확인
34. history-card latest-update news-only `다시 불러오기` 후 follow-up 질문에서 기사 source path(`hankyung.com`, `mk.co.kr`)가 context box에 유지되는지 확인
35. history-card entity-card zero-strong-slot `다시 불러오기` 후 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source role이 과장 없이 유지되고, source path(`namu.wiki`, `ko.wikipedia.org`)가 context box에 유지되는지 확인
36. history-card entity-card zero-strong-slot `다시 불러오기` 후 follow-up 질문에서 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source role이 drift하지 않고, source path(`namu.wiki`, `ko.wikipedia.org`)가 context box에 유지되는지 확인
37. history-card entity-card zero-strong-slot `다시 불러오기` 후 두 번째 follow-up 질문에서 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source role이 drift하지 않고, source path(`namu.wiki`, `ko.wikipedia.org`)가 context box에 유지되는지 확인
38. entity-card zero-strong-slot `방금 검색한 결과 다시 보여줘` browser 자연어 reload에서 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source role이 유지되고, source path(`namu.wiki`, `ko.wikipedia.org`)가 context box에 유지되는지 확인
39. entity-card zero-strong-slot browser 자연어 reload 후 follow-up에서 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source role이 drift하지 않고, source path(`namu.wiki`, `ko.wikipedia.org`)가 context box에 유지되는지 확인
40. entity-card 붉은사막 검색 결과 `방금 검색한 결과 다시 보여줘` browser 자연어 reload에서 noisy single-source claim(`출시일`/`2025`/`blog.example.com`) 미노출, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` 유지, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance가 유지되는지 확인
41. entity-card dual-probe `방금 검색한 결과 다시 보여줘` browser 자연어 reload에서 source path(`pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300`)가 context box에 유지되는지 확인
42. entity-card dual-probe `방금 검색한 결과 다시 보여줘` browser 자연어 reload에서 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `공식 기반` · `백과 기반` source role이 유지되는지 확인
43. entity-card dual-probe browser 자연어 reload 후 follow-up에서 source path(`pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300`)가 context box에 유지되는지 확인
44. entity-card dual-probe browser 자연어 reload 후 follow-up에서 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `공식 기반` · `백과 기반` source role이 drift하지 않는지 확인
45. entity-card 붉은사막 actual-search browser 자연어 reload 후 follow-up에서 source path(`namu.wiki`/`ko.wikipedia.org`)가 context box에 유지되고, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`이 drift하지 않는지 확인
46. entity-card 붉은사막 browser 자연어 reload에서 source path(`namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance)가 context box에 유지되는지 확인
47. entity-card 붉은사막 actual-search browser 자연어 reload 후 follow-up에서 source path(`namu.wiki`/`ko.wikipedia.org`) context box 유지 확인
48. history-card entity-card `다시 불러오기` 후 actual-search source path(`namu.wiki`, `ko.wikipedia.org`)가 context box에 유지되고, `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `백과 기반` source role이 유지되는지 확인
49. history-card entity-card `다시 불러오기` 후 follow-up 질문에서 actual-search source path(`namu.wiki`, `ko.wikipedia.org`)가 context box에 유지되고, `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `백과 기반` source role이 drift하지 않는지 확인
50. history-card entity-card `다시 불러오기` 후 두 번째 follow-up 질문에서 actual-search source path(`namu.wiki`, `ko.wikipedia.org`)가 context box에 유지되고, `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `백과 기반` source role이 drift하지 않는지 확인
51. history-card entity-card `다시 불러오기` 후 두 번째 follow-up 질문에서 dual-probe source path(`pearlabyss.com/200`, `pearlabyss.com/300`)가 context box에 유지되고, `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `공식 기반` · `백과 기반` source role이 drift하지 않는지 확인
52. entity-card dual-probe browser 자연어 reload 후 두 번째 follow-up에서 source path(`pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300`)가 context box에 유지되고, `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `공식 기반` · `백과 기반` source role이 drift하지 않는지 확인
53. entity-card 붉은사막 actual-search browser 자연어 reload 후 두 번째 follow-up에서 source path(`namu.wiki`/`ko.wikipedia.org`)가 context box에 유지되고, `WEB` badge, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`이 drift하지 않는지 확인
54. entity-card 붉은사막 browser 자연어 reload 후 follow-up에서 noisy single-source claim(`출시일`/`2025`/`blog.example.com`)이 미노출되고, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance continuity가 유지되는지 확인
55. entity-card 붉은사막 browser 자연어 reload 후 두 번째 follow-up에서 noisy single-source claim(`출시일`/`2025`/`blog.example.com`)이 미노출되고, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance continuity가 유지되는지 확인
56. history-card latest-update mixed-source `다시 불러오기` 후 두 번째 follow-up에서 source path(`store.steampowered.com`, `yna.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source role이 drift하지 않는지 확인
57. history-card latest-update single-source `다시 불러오기` 후 두 번째 follow-up 질문에서 source path(`example.com/seoul-weather`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `단일 출처 참고` verification label, `보조 출처` source role이 drift하지 않는지 확인
58. history-card latest-update news-only `다시 불러오기` 후 두 번째 follow-up 질문에서 기사 source path(`hankyung.com`, `mk.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `기사 교차 확인` verification label, `보조 기사` source role이 drift하지 않는지 확인
59. latest-update mixed-source `방금 검색한 결과 다시 보여줘` browser 자연어 reload에서 source path(`store.steampowered.com`, `yna.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source role이 drift하지 않는지 확인
60. latest-update single-source `방금 검색한 결과 다시 보여줘` browser 자연어 reload에서 source path(`example.com/seoul-weather`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `단일 출처 참고` verification label, `보조 출처` source role이 drift하지 않는지 확인
61. latest-update news-only `방금 검색한 결과 다시 보여줘` browser 자연어 reload에서 기사 source path(`hankyung.com`, `mk.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `기사 교차 확인` verification label, `보조 기사` source role이 drift하지 않는지 확인
62. latest-update mixed-source browser 자연어 reload 후 follow-up에서 source path(`store.steampowered.com`, `yna.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source role이 drift하지 않는지 확인
63. latest-update mixed-source browser 자연어 reload 후 두 번째 follow-up에서 source path(`store.steampowered.com`, `yna.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `공식+기사 교차 확인` verification label, `보조 기사` · `공식 기반` source role이 drift하지 않는지 확인
64. latest-update single-source browser 자연어 reload 후 follow-up에서 source path(`example.com/seoul-weather`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `단일 출처 참고` verification label, `보조 출처` source role이 drift하지 않는지 확인
65. latest-update single-source browser 자연어 reload 후 두 번째 follow-up에서 source path(`example.com/seoul-weather`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `단일 출처 참고` verification label, `보조 출처` source role이 drift하지 않는지 확인
66. latest-update news-only browser 자연어 reload 후 follow-up에서 기사 source path(`hankyung.com`, `mk.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `기사 교차 확인` verification label, `보조 기사` source role이 drift하지 않는지 확인
67. latest-update news-only browser 자연어 reload 후 두 번째 follow-up에서 기사 source path(`hankyung.com`, `mk.co.kr`)가 context box에 유지되고, `WEB` origin badge, `최신 확인` answer-mode badge, `기사 교차 확인` verification label, `보조 기사` source role이 drift하지 않는지 확인
68. latest-update noisy community source가 browser 자연어 reload 후 follow-up에서도 origin detail과 본문, context box에 `보조 커뮤니티`, `brunch` 미노출되고, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`만 유지되는지 확인
69. latest-update noisy community source가 browser 자연어 reload 후 두 번째 follow-up에서도 origin detail과 본문, context box에 `보조 커뮤니티`, `brunch` 미노출되고, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`만 유지되는지 확인
70. history-card latest-update noisy community source가 `다시 불러오기` 후 follow-up에서도 origin detail과 본문, context box에 `보조 커뮤니티`, `brunch` 미노출되고, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`만 유지되는지 확인
71. history-card latest-update noisy community source가 `다시 불러오기` 후 두 번째 follow-up에서도 origin detail과 본문, context box에 `보조 커뮤니티`, `brunch` 미노출되고, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`만 유지되는지 확인
72. entity-card noisy single-source claim(`출시일`/`2025`/`blog.example.com`)이 browser 자연어 reload 후 follow-up에서도 미노출되고, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance가 유지되는지 확인
73. entity-card noisy single-source claim(`출시일`/`2025`/`blog.example.com`)이 browser 자연어 reload 후 두 번째 follow-up에서도 미노출되고, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance가 유지되는지 확인
74. history-card entity-card noisy single-source claim(`출시일`/`2025`/`blog.example.com`)이 `다시 불러오기` 후 follow-up에서도 미노출되고, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance가 유지되는지 확인
75. history-card entity-card noisy single-source claim(`출시일`/`2025`/`blog.example.com`)이 `다시 불러오기` 후 두 번째 follow-up에서도 미노출되고, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance가 유지되는지 확인
76. 브라우저 파일 선택으로 scanned/image-only PDF를 선택하면 visible OCR 미지원 안내(`요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`)가 표시되는지 확인
77. 브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색하면 count-only partial-failure notice + readable file preview exact fields(`1. notes.txt`, `내용 일치`, `budget` snippet) + selected path/copy(`mixed-search-folder/notes.txt`) + hidden body + transcript preview + transcript body hidden이 유지되는지 확인
78. 브라우저 파일 선택으로 readable text-layer PDF를 선택하면 OCR guidance 미노출, visible summary body에 extracted text(`local-first approval-based document assistant`) 포함, context box + quick meta + transcript meta에 `readable-text-layer.pdf` 표시, quick meta + transcript meta `문서 요약` label이 유지되는지 확인
79. 브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색+요약하면 partial-failure notice + readable file preview exact fields(`1. notes.txt`, `mixed-search-folder/notes.txt` tooltip, `내용 일치`, `budget` snippet) + transcript preview exact fields가 유지되는지 확인
80. claim-coverage panel에서 재조사 대상(`is_focus_slot`) 슬롯이 단일 출처/미확인 상태일 때 전용 설명 라인(`아직 단일 출처 상태입니다`, `아직 확인되지 않았습니다`)이 표시되고, 비재조사 슬롯에는 미표시되는지 확인
81. claim-coverage panel에서 재조사 후 보강된(`improved`) 슬롯이 `재조사 결과: 단일 출처 → 교차 확인으로 보강되었습니다` 설명을 표시하는지 확인
82. claim-coverage panel에서 재조사 후 약해진(`regressed`) 슬롯이 `재조사 결과: 교차 확인 → 단일 출처로 약해졌습니다. 추가 교차 검증이 권장됩니다` 설명을 표시하는지 확인
83. history-card latest-update noisy community source가 `방금 검색한 결과 다시 보여줘` 자연어 reload-only 경로(후속 follow-up 없이)에서도 본문, origin detail, context box에 `보조 커뮤니티`, `brunch` 미노출되고, `WEB` origin badge, `최신 확인` answer-mode badge, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`만 유지되며, zero-count `.meta` no-leak이 유지되는지 확인
84. history-card entity-card noisy single-source initial-render 단계(click reload / 자연어 reload / follow-up 전)에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2`로 유지되며 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label이 `.meta`에 새지 않고, `출시일` / `2025` / `blog.example.com` noisy single-source 잔재가 history-card에 노출되지 않는지 확인
85. history-card entity-card actual-search initial-render 단계(click reload / 자연어 reload / follow-up 전)에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2`로 유지되며 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label이 `.meta`에 새지 않는지 확인
86. history-card entity-card dual-probe initial-render 단계(click reload / 자연어 reload / follow-up 전)에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta`가 정확히 `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary로 유지되며 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label이 `.meta`에 새지 않는지 확인
87. history-card latest-update noisy community source initial-render 단계(click reload / 자연어 reload / follow-up 전)에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta` count가 `0`이며 `사실 검증` text가 우발적 `.meta` 생성으로도 노출되지 않고, `보조 커뮤니티` / `brunch` noisy 잔재가 history-card에 노출되지 않는지 확인
88. history-card latest-update mixed-source initial-render 단계(click reload / 자연어 reload / follow-up 전)에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta` count가 `0`이며 `사실 검증` text가 우발적 `.meta` 생성으로도 노출되지 않는지 확인
89. history-card latest-update single-source initial-render 단계(click reload / 자연어 reload / follow-up 전)에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta` count가 `0`이며 `사실 검증` text가 우발적 `.meta` 생성으로도 노출되지 않는지 확인
90. history-card latest-update news-only initial-render 단계(click reload / 자연어 reload / follow-up 전)에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta` count가 `0`이며 `사실 검증` text가 우발적 `.meta` 생성으로도 노출되지 않는지 확인
91. history-card entity-card store-seeded actual-search initial-render 단계(click reload / 자연어 reload / follow-up 전)에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta` count가 `0`이며 `사실 검증` text가 우발적 `.meta` 생성으로도 노출되지 않는지 확인
92. history-card entity-card store-seeded actual-search 자연어 reload-only 단계에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta` count가 `0`, `사실 검증` text 미노출, `WEB` badge / `설명 카드` answer-mode badge / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity가 유지되는지 확인
93. history-card entity-card store-seeded actual-search `다시 불러오기` click reload-only 단계에서 `다시 불러오기` 버튼이 노출되고, history-card `.meta` count가 `0`, `사실 검증` text 미노출, `WEB` badge / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity가 유지되는지 확인
94. history-card entity-card store-seeded actual-search `다시 불러오기` 후 첫 follow-up 질문에서 history-card `.meta` count가 `0`, `사실 검증` text 미노출, `WEB` badge / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity가 drift하지 않는지 확인
95. history-card entity-card store-seeded actual-search `다시 불러오기` 후 두 번째 follow-up 질문에서 history-card `.meta` count가 `0`, `사실 검증` text 미노출, `WEB` badge / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity가 drift하지 않는지 확인
96. history-card entity-card store-seeded actual-search 자연어 reload 체인(자연어 reload → follow-up → 두 번째 follow-up)에서 history-card `.meta` count가 `0`, `사실 검증` text 미노출, `WEB` badge / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity가 drift하지 않는지 확인
97. history-card entity-card zero-strong-slot `다시 불러오기` 후 history-card `.meta`가 정확히 `사실 검증 미확인 5` missing-only count-summary로 유지되고, `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak 없이 `WEB` / `설명 카드` answer-mode badge / `설명형 단일 출처` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity가 유지되는지 확인
98. history-card entity-card zero-strong-slot `다시 불러오기` 후 두 번째 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 미확인 5` missing-only count-summary로 drift 없이 유지되고, `WEB` / `설명 카드` / `설명형 단일 출처` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity가 drift하지 않는지 확인
99. history-card entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 미확인 5` missing-only count-summary로 drift 없이 유지되고, `WEB` / `설명 카드` / `설명형 단일 출처` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` visible continuity가 drift하지 않는지 확인
100. history-card entity-card dual-probe `다시 불러오기` reload 단계에서 history-card `.meta`가 정확히 `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary로 유지되고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak 없이 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반`, `pearlabyss.com/200` / `pearlabyss.com/300` source path visible continuity가 유지되는지 확인
101. history-card entity-card dual-probe `다시 불러오기` 후 두 번째 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary로 drift 없이 유지되고, leading/trailing separator artifact가 count-summary line에 생기지 않으며 `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` visible continuity가 drift하지 않는지 확인
102. entity-card dual-probe 자연어 reload 단계에서 history-card `.meta`가 정확히 `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary로 유지되고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak 없이 `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` visible continuity가 유지되는지 확인
103. entity-card dual-probe 자연어 reload 후 두 번째 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary로 drift 없이 유지되고, leading/trailing separator artifact가 count-summary line에 생기지 않으며 `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` visible continuity가 drift하지 않는지 확인
104. history-card entity-card actual-search `다시 불러오기` click reload 단계에서 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 유지되고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없는지 확인
105. history-card entity-card actual-search `다시 불러오기` 후 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 drift 없이 유지되고, count-summary line에 leading/trailing separator artifact가 생기지 않는지 확인
106. history-card entity-card actual-search `다시 불러오기` 후 두 번째 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 drift 없이 유지되고, count-summary line에 leading/trailing separator artifact가 생기지 않는지 확인
107. entity-card actual-search 자연어 reload 단계에서 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 유지되고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없는지 확인
108. entity-card actual-search 자연어 reload 후 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 drift 없이 유지되고, count-summary line에 leading/trailing separator artifact가 생기지 않는지 확인
109. entity-card actual-search 자연어 reload 후 두 번째 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 drift 없이 유지되고, count-summary line에 leading/trailing separator artifact가 생기지 않는지 확인
110. history-card entity-card noisy single-source `다시 불러오기` click reload 단계에서 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 유지되고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없는지 확인
111. history-card entity-card noisy single-source `다시 불러오기` 후 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 drift 없이 유지되고, count-summary line에 leading/trailing separator artifact가 생기지 않는지 확인
112. history-card entity-card noisy single-source `다시 불러오기` 후 두 번째 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 drift 없이 유지되고, count-summary line에 leading/trailing separator artifact가 생기지 않는지 확인
113. entity-card noisy single-source 자연어 reload 단계에서 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 유지되고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없는지 확인
114. entity-card noisy single-source 자연어 reload 후 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 drift 없이 유지되고, count-summary line에 leading/trailing separator artifact가 생기지 않는지 확인
115. entity-card noisy single-source 자연어 reload 후 두 번째 follow-up 질문에서도 history-card `.meta`가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary로 drift 없이 유지되고, count-summary line에 leading/trailing separator artifact가 생기지 않는지 확인
116. history-card entity-card 단일 출처 `다시 불러오기` click reload 단계(stored `{weak:1, missing:1}` count-summary + `단일 출처 상태 1건, 미확인 1건.` progress summary)에서 history-card `.meta`가 정확히 `사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건.`로 유지되어 count-summary가 progress-summary 앞에 오고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없으며, leading/trailing separator artifact가 composed line에 생기지 않는지 확인
117. history-card entity-card 단일 출처 `다시 불러오기` 후 follow-up 질문 단계(stored `{weak:1}` count-summary + `단일 출처 상태 1건.` progress summary)에서 history-card `.meta`가 정확히 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.`로 유지되어 count-summary가 progress-summary 앞에 오고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없으며, leading/trailing separator artifact가 composed line에 생기지 않는지 확인
118. history-card entity-card 단일 출처 `다시 불러오기` 후 두 번째 follow-up 질문 단계(stored `{weak:1}` count-summary + `단일 출처 상태 1건.` progress summary)에서도 history-card `.meta`가 정확히 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.`로 drift 없이 유지되고, count-summary가 progress-summary 앞에 오며, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없고, leading/trailing separator artifact가 composed line에 생기지 않는지 확인
119. history-card entity-card 단일 출처 자연어 reload 후 두 번째 follow-up 질문 단계(stored `{weak:1}` count-summary + `단일 출처 상태 1건.` progress summary)에서도 history-card `.meta`가 정확히 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.`로 drift 없이 유지되고, count-summary가 progress-summary 앞에 오며, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없고, leading/trailing separator artifact가 composed line에 생기지 않는지 확인
120. `web-search history card header badges` investigation mixed count+progress composition 단계(multi-category count-summary + non-empty progress summary)에서 history-card `.meta`가 정확히 `사실 검증 교차 확인 2 · 단일 출처 1 · 혼합 지표: 교차 확인과 단일 출처가 함께 관찰되었습니다.`로 유지되어 count-summary가 progress-summary 앞에 오고, `.meta`에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak이 없으며, composed line에 leading/trailing separator artifact가 생기지 않는지 확인
121. `web-search history card header badges` general label+count+progress composition 단계(general answer-mode + multi-category count-summary + non-empty progress summary)에서 history-card `.meta`가 정확히 `일반 검색 · 사실 검증 교차 확인 2 · 단일 출처 1 · 일반 지표: 커뮤니티 단서와 교차 확인이 함께 관찰되었습니다.`로 유지되어 `label → count → progress` 순서가 고정되고, `.meta`에 `혼합 지표:` / `설명 카드` / `최신 확인` investigation answer-mode leak이 없으며, composed line에 leading/trailing separator artifact가 생기지 않는지 확인
122. `web-search history card header badges` general label+count-only composition 단계(general answer-mode + single-category count-summary + empty progress summary)에서 history-card `.meta`가 정확히 `일반 검색 · 사실 검증 교차 확인 2`로 유지되어 label 뒤에 count-only segment만 오고, `.meta`에 `일반 진행:` / `혼합 지표:` / `일반 지표:` / `설명 카드` / `최신 확인` absent segment leak이 없으며, composed line에 leading/trailing separator artifact가 생기지 않는지 확인
123. `web-search history card header badges` general label+progress-only composition 단계(general answer-mode + empty count-summary + non-empty progress summary)에서 history-card `.meta`가 정확히 `일반 검색 · 일반 진행: 커뮤니티 단서가 단일 출처 상태로 남아 있습니다.`로 유지되어 label 뒤에 progress-only segment만 오고, `.meta`에 `사실 검증` / `혼합 지표:` / `일반 지표:` / `설명 카드` / `최신 확인` absent segment leak이 없으며, composed line에 leading/trailing separator artifact가 생기지 않는지 확인
124. history-card entity-card `다시 불러오기` click reload 후 브라우저 composer(`#user-text` + `submit-request`)를 거친 plain follow-up(`이 결과 한 문장으로 요약해줘`) 요청이 `/api/chat/stream` POST payload에 `load_web_search_record_id`를 전혀 포함하지 않은 채 전송되고, follow-up 이후에도 `#claim-coverage-box`가 visible이며 `#claim-coverage-text`에 저장된 entity-card `장르` / `[단일 출처]` 슬롯과 history-card `.meta` 가 정확히 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.`로 drift 없이 유지되는지 확인
125. history-card latest-update `다시 불러오기` click reload 후 브라우저 composer(`#user-text` + `submit-request`)를 거친 plain follow-up(`이 결과 한 문장으로 요약해줘`) 요청이 `/api/chat/stream` POST payload에 `load_web_search_record_id`를 전혀 포함하지 않은 채 전송되고, follow-up 이후에도 `#claim-coverage-box`가 hidden이며 history-card `.meta` 카운트가 `0`으로 유지되는지 확인
126. review-queue `reject`/`defer` review action이 `accept`와 동일한 quick-meta(`검토 거절됨`/`검토 보류됨`), transcript-meta, follow-up retention, stale-clear 경로를 따르고, payload에 `review_action: reject`/`review_status: rejected` 및 `review_action: defer`/`review_status: deferred`가 기록되는지 확인

`make e2e-test` launches a dedicated Playwright web server for smoke with inherited `LOCAL_AI_MODEL_PROVIDER` / `LOCAL_AI_OLLAMA_MODEL` overrides cleared, `LOCAL_AI_MODEL_PROVIDER=mock` reapplied, and existing servers on the smoke port not reused. Shell overrides such as `LOCAL_AI_MODEL_PROVIDER=ollama` therefore do not change the automated baseline. Other runtimes remain optional and are validated separately.

### SQLite Browser Smoke (opt-in backend parity gate)

SQLite browser smoke uses a dedicated Playwright config (`e2e/playwright.sqlite.config.mjs`) that starts `app.web` on port 8880 with `LOCAL_AI_STORAGE_BACKEND=sqlite` and isolated temp dirs for the sqlite DB and writable state. It runs the same `web-smoke.spec.mjs` scenarios as the JSON-default smoke but under the sqlite storage backend.

Run: `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "<scenario>" --reporter=line`

Current sqlite browser smoke gate scenarios:
1. `same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다`
2. `same-session recurrence aggregate stale candidate retires before apply start`
3. `same-session recurrence aggregate active lifecycle survives supporting correction supersession`
4. `same-session recurrence aggregate recorded basis label survives supporting correction supersession`
5. `same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다`
6. `원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다`
7. `내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다`
8. `corrected-save first bridge path가 기록본 기준 승인 스냅샷으로 저장됩니다`
9. `corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다`
10. `파일 요약 후 근거와 요약 구간이 보입니다`
11. `브라우저 파일 선택으로도 파일 요약이 됩니다`
12. `브라우저 폴더 선택으로도 문서 검색이 됩니다`
13. `검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다`
14. `브라우저 파일 선택으로 scanned/image-only PDF를 선택하면 OCR 미지원 안내가 표시됩니다`
15. `브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색하면 count-only partial-failure notice가 표시됩니다`
16. `브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색+요약하면 partial-failure notice와 함께 readable file preview가 유지됩니다`
17. `브라우저 파일 선택으로 readable text-layer PDF를 선택하면 정상 요약이 됩니다`
18. `candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다`
19. `review-queue reject/defer는 accept와 동일한 quick-meta, transcript-meta, stale-clear 경로를 따릅니다`
20. `review-queue reject-defer aggregate support visibility`
21. `저장 요청 후 승인 경로를 다시 발급할 수 있습니다`
22. `승인 후 실제 note가 저장됩니다`
23. `스트리밍 중 취소 버튼이 동작합니다`
24. `일반 채팅 응답에는 source-type label이 붙지 않습니다`
25. `claim-coverage panel은 status tag와 행동 힌트를 올바르게 렌더링합니다`
26. `claim-coverage panel은 재조사 대상 슬롯의 진행 상태를 명확히 렌더링합니다`
27. `claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다`
28. `claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다`
29. `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다`
30. `history-card latest-update noisy community source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
31. `history-card entity-card noisy single-source initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다`
32. `history-card entity-card actual-search initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다`
33. `history-card entity-card dual-probe initial-render 단계에서 mixed count-summary meta contract가 유지됩니다`
34. `history-card latest-update mixed-source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
35. `history-card latest-update single-source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
36. `history-card latest-update news-only initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
37. `history-card entity-card store-seeded actual-search initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
38. `history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다`
39. `history-card latest-update 다시 불러오기 후 WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
40. `history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`
41. `history-card entity-card 다시 불러오기 후 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`
42. `history-card entity-card 다시 불러오기 후 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다`
43. `history-card entity-card 다시 불러오기 후 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다`
44. `history-card latest-update 다시 불러오기 후 mixed-source source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
45. `history-card latest-update single-source 다시 불러오기 후 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다`
46. `history-card latest-update news-only 다시 불러오기 후 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다`
47. `history-card entity-card store-seeded actual-search 다시 불러오기 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다`
48. `history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다`
49. `history-card latest-update 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 drift하지 않습니다`
50. `history-card latest-update noisy community source가 다시 불러오기 후 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`
51. `history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`
52. `history-card entity-card store-seeded actual-search 다시 불러오기 후 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다`
53. `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다`
54. `history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다`
55. `history-card latest-update mixed-source 다시 불러오기 후 follow-up 질문에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
56. `history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 drift하지 않습니다`
57. `history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 drift하지 않습니다`
58. `history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다`
59. `history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다`
60. `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다`
61. `history-card entity-card store-seeded actual-search 다시 불러오기 후 두 번째 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다`
62. `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다`
63. `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다`
64. `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe mixed count-summary meta가 truthfully 유지됩니다`
65. `history-card latest-update mixed-source 다시 불러오기 후 두 번째 follow-up 질문에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 drift하지 않습니다`
66. `history-card latest-update single-source 다시 불러오기 후 두 번째 follow-up 질문에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 drift하지 않습니다`
67. `history-card latest-update news-only 다시 불러오기 후 두 번째 follow-up 질문에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 drift하지 않습니다`
68. `history-card latest-update noisy community source가 다시 불러오기 후 두 번째 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`
69. `history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`
70. `history-card latest-update 자연어 reload noisy community 보조 커뮤니티 brunch 미노출 기사 교차 확인 보조 기사 hankyung mk 유지됩니다`
71. `history-card entity-card store-seeded actual-search 자연어 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다`
72. `entity-card zero-strong-slot 방금 검색한 결과 다시 보여줘 자연어 reload에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 유지됩니다`
73. `entity-card 붉은사막 검색 결과 자연어 reload에서 WEB badge, 설명 카드, noisy single-source claim(출시일/2025/blog.example.com) 미노출, 설명형 다중 출처 합의, 백과 기반 유지, namu.wiki/ko.wikipedia.org/blog.example.com provenance 유지됩니다`
74. `entity-card 붉은사막 자연어 reload에서 source path(namu.wiki, ko.wikipedia.org, blog.example.com provenance)가 context box에 유지됩니다`
75. `entity-card dual-probe 자연어 reload에서 source path(pearlabyss.com/200, pearlabyss.com/300)가 context box에 유지됩니다`
76. `entity-card dual-probe 자연어 reload에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다`
77. `latest-update mixed-source 자연어 reload에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
78. `latest-update single-source 자연어 reload에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다`
79. `latest-update news-only 자연어 reload에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다`
80. `history-card entity-card 자연어 reload 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다`
81. `history-card entity-card store-seeded actual-search 자연어 reload 체인에서 empty-meta no-leak contract가 유지됩니다`
82. `entity-card zero-strong-slot 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다 (browser natural-reload path)`
83. `entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu.wiki/ko.wikipedia.org가 drift하지 않습니다`
84. `entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 missing-only count-summary meta가 truthfully 유지됩니다`
85. `entity-card dual-probe 자연어 reload 후 follow-up에서 source path(pearlabyss.com/200, pearlabyss.com/300)가 context box에 유지됩니다`
86. `entity-card dual-probe 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다`
87. `entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 mixed count-summary meta가 truthfully 유지됩니다`
88. `entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 source path(pearlabyss.com/200, pearlabyss.com/300) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다`
89. `entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지됩니다`
90. `entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다`
91. `entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지되고 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다`
92. `entity-card 붉은사막 자연어 reload 후 follow-up에서 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance continuity가 유지됩니다`
93. `entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance continuity가 유지됩니다`
94. `latest-update mixed-source 자연어 reload 후 follow-up에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
95. `latest-update mixed-source 자연어 reload 후 두 번째 follow-up에서 source path(store.steampowered.com, yna.co.kr) + WEB badge, 최신 확인, 공식+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다`
96. `latest-update single-source 자연어 reload 후 follow-up에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다`
97. `latest-update single-source 자연어 reload 후 두 번째 follow-up에서 source path(example.com/seoul-weather) + WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다`
98. `latest-update news-only 자연어 reload 후 follow-up에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다`
99. `latest-update news-only 자연어 reload 후 두 번째 follow-up에서 기사 source path(hankyung.com, mk.co.kr) + WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다`
100. `latest-update noisy community source가 자연어 reload 후 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`
101. `latest-update noisy community source가 자연어 reload 후 두 번째 follow-up에서도 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`
102. `entity-card noisy single-source claim(출시일/2025/blog.example.com)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`
103. `entity-card noisy single-source claim(출시일/2025/blog.example.com)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`
104. `history-card entity-card click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 top-level claim_coverage를 유지합니다`
105. `history-card latest-update click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 empty claim_coverage surfaces를 유지합니다`

Note: The sqlite browser config keeps `LOCAL_AI_NOTES_DIR` and `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` at the repo defaults (`data/notes/`, `data/web-search/`) so saved-note and pre-seeded web-search record scenarios behave identically to the JSON-default path. The sqlite DB and corrections dir remain isolated per run.

### Controller Smoke (separate from app.web)

Controller smoke uses a dedicated Playwright config (`e2e/playwright.controller.config.mjs`) that starts `python3 -m controller.server` on port 8781 by default. The port can be overridden via `CONTROLLER_SMOKE_PORT`. These scenarios are internal/operator tooling tests and are not part of the `app.web` release gate.

Run: `make controller-test`

Direct equivalent: `cd e2e && CONTROLLER_SMOKE_PORT=<free-port> npx playwright test -c playwright.controller.config.mjs --reporter=line`

Override port: `CONTROLLER_SMOKE_PORT=8782 make controller-test`

Current controller smoke scenarios:
1. cozy runtime loads from shared `/controller-assets/js/cozy.js` module — asserts exactly one `<script src="/controller-assets/js/cozy.js">` tag on `/controller`, and that `window.getRoamBounds`, `window.setAgentFatigue`, `window.testPickIdleTargets`, `window.testAntiStacking`, and `window.testHistoryPenalty` are all reachable as functions from the shared module
2. controller shows `#storage-warn` chip (`⚠ 설정 비저장`) with expected tooltip when browser localStorage is blocked via `Storage.prototype` throw, and event log contains the one-time storage warning (`환경 설정 저장 불가`) exactly once
3. controller hides `#storage-warn` chip and event log contains no storage warning when browser localStorage is available
4. marquee text keeps moving when the polled runtime payload is unchanged — routes `/api/runtime/status` to a stable payload and asserts `#marquee-text` `transform` translateX decreases monotonically across two 2.5s samples so the marquee animation does not stall on repeated identical polls
5. agent cards expose `data-fatigue` attribute for fatigue observability — verifies that a working agent's sidebar card carries `data-agent` and `data-fatigue` attributes, with no `.agent-fatigue` indicator visible before the fatigue threshold is reached
6. `setAgentFatigue` hook transitions card to `fatigued` state — injects fatigue via `window.setAgentFatigue("Claude", "fatigued")` and asserts `data-fatigue="fatigued"` with `💦 피로 누적` label
7. `setAgentFatigue` hook transitions card to `coffee` state — injects coffee via `window.setAgentFatigue("Claude", "coffee")` and asserts `data-fatigue="coffee"` with `☕ 커피 충전 중` label
8. idle roam targets stay within the agent's home desk zone — forces 30 idle roam target picks via `window.testPickIdleTargets("Claude", 30)`, reads the home zone rect (`claude_desk`) from `window.getRoamBounds().zones`, and asserts every picked point lies inside that zone
9. zone-bounded agents inherently avoid stacking (separate desk zones) — places a phantom at the center of `codex_desk`, forces 50 picks via `window.testAntiStacking("Claude", cx, cy, 50)`, and asserts every pick still lies inside Claude's `claude_desk` zone because `testAntiStacking` delegates to `testPickIdleTargets` now that zone isolation already prevents stacking
10. zone-bounded idle roam uses continuous micro-roam (no spot history) — asserts `window.testHistoryPenalty("Claude", [0,1,2,3,4], 120)` returns an empty array because zone-bounded micro-roam no longer tracks spot history, and that `window.testPickIdleTargets("Claude", 20)` still yields 20 points inside the `claude_desk` zone

## Safety Defaults

- local-first by default
- write actions require explicit approval
- overwrite is rejected by default; when a save target already exists, the approval card shows an overwrite warning and the user can explicitly approve the overwrite, which then replaces the existing file
- web search is permission-gated, read-only, and logged
- OCR is not enabled in the current MVP
- structured correction / preference memory is not yet implemented; the current memory foundation is limited to grounded-brief trace anchoring, normalized original-response snapshots, explicit `corrected_text` submission plus minimum `accepted_as_is` / `corrected` / `rejected` outcome capture on the source message, one source-message `content_reason_record` for explicit `내용 거절` plus optional same-card reject-note updates, and approval-linked `approval_reason_record` traces for reject / reissue
- the shipped candidate-linked reuse confirmation remains separate from approval-backed save support: it is stored as one source-message `candidate_confirmation_record`, leaves `session_local_candidate` unchanged, may materialize one source-message `durable_candidate` plus one pending `review_queue_items` entry, and now supports `accept`/`reject`/`defer` reviewed-but-not-applied actions that write source-message `candidate_review_record` and persistently show the review outcome on the source-message transcript meta, without opening user-level memory
- corrected-save is implemented only as a minimum bridge action: it starts from the response-card correction area, stays visible but disabled until a correction is recorded, consumes recorded `corrected_text` only, and creates a fresh immutable approval snapshot without rebasing older pending approvals

## Where To Read Next

The current source-of-truth product docs live in the root `docs/` directory.
Files under `docs/recycle/` are retained drafts or historical notes unless explicitly promoted.

- product overview: [docs/project-brief.md](/home/xpdlqj/code/projectH/docs/project-brief.md)
- product rationale: [docs/PRODUCT_PROPOSAL.md](/home/xpdlqj/code/projectH/docs/PRODUCT_PROPOSAL.md)
- current product contract: [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md)
- architecture: [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md)
- acceptance and QA gates: [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md)
- milestones and backlog: [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md)
- next-phase design contract: [plandoc/2026-03-26-grounded-brief-memory-contract.md](/home/xpdlqj/code/projectH/plandoc/2026-03-26-grounded-brief-memory-contract.md)
