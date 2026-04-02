# projectH

`projectH`는 **로컬 퍼스트 문서 비서 웹 MVP**입니다.
사용자는 로컬 파일을 읽고, 요약하고, 검색하고, 필요할 때만 승인 기반으로 저장할 수 있습니다. 웹 검색은 핵심 제품이 아니라 **보조 조사 모드**로 제한적으로 붙어 있습니다.

## Phase Split

### Current Shipped Contract
- 로컬 퍼스트 문서 비서 웹 MVP
- 핵심 루프: 문서 읽기 -> grounded summary -> 후속 질의 -> 승인 기반 저장
- 웹 조사는 secondary mode

### Next Phase Design Target
- `grounded brief` 1개를 공식 artifact로 고정
- 그 artifact를 기준으로 correction / approval / preference memory를 구조화
- 이 단계는 문서 설계 계약 고정 단계이며, 아직 모델 학습이나 프로그램 조작 구현 단계가 아닙니다

### Long-Term North Star
- 사용자가 가르치면 길들여지고, 나중에는 승인 기반 로컬 행동까지 확장되는 로컬 개인 에이전트
- 프로그램 조작과 모델 적응 계층은 그 이후 단계입니다

## Current Product Slice

현재 구현된 웹 MVP는 아래를 포함합니다.

- local web shell (`python3 -m app.web`)
- recent sessions / conversation timeline with per-message timestamps
- file summary / document search / general chat
- document search responses include a structured search result preview panel below the text body, showing each matched file's name (with full path tooltip), match type badge (`파일명 일치` / `내용 일치`), and a content snippet; both search-only and search-plus-summary responses carry the same `search_results` data
- approval-based save with default notes directory shown in the save-path placeholder
- reissue approval flow
- evidence / source panel with source-role trust labels on each evidence item
- summary source-type label (`문서 요약` for local document summary, `선택 결과 요약` for selected search results) in both quick-meta bar and transcript message meta; single-source responses show basename-based `출처 <filename>` in both surfaces, multi-source responses show count-based `출처 N개` instead of raw filenames; general chat responses carry no source-type label
- summary span / applied-range panel
- response origin badge with separate answer-mode badge for web investigation (`설명 카드` / `최신 확인`), source-role trust labels, and verification strength tags in origin detail
- copy-to-clipboard buttons: `본문 복사`, `저장 경로 복사`, `승인 경로 복사`, `검색 기록 경로 복사` (shared helper shows clipboard-specific failure notice on both success-path rejection and fallback failure)
- streaming progress + cancel
- response feedback capture
- grounded-brief artifact trace anchor on summary responses, save approvals, and relevant local traces
- normalized original-response snapshot, minimum `accepted_as_is` / `corrected` content-outcome capture, and minimum reject / reissue approval reason capture on grounded-brief traces
- small grounded-brief correction editor seeded with the current draft text, with explicit correction submit kept separate from save approval; correction submit also updates the session `active_context.summary_hint` so that subsequent follow-up responses and re-summaries in the same session use the corrected text as their basis
- current save approvals and save/write traces now expose `save_content_source = original_draft | corrected_text` plus explicit `source_message_id` anchoring to the original grounded-brief source message
- minimum corrected-save bridge action that stays always visible inside the correction area, stays disabled until a recorded `corrected_text` exists, creates a fresh approval from that recorded text, freezes the approval snapshot under a new `approval_id`, and reuses the same `artifact_id` / `source_message_id` with `save_content_source = corrected_text`
- one small candidate-linked confirmation action on the grounded-brief response card that appears only when the current `session_local_candidate` exists and persists one separate source-message `candidate_confirmation_record`
- one optional source-message-anchored `durable_candidate` projection plus one local `검토 후보` section fed only by current pending `review_queue_items`, with one `accept`-only reviewed-but-not-applied action that records source-message `candidate_review_record`
- one separate aggregate-level `검토 메모 적용 후보` section fed only by current same-session `recurrence_aggregate_candidates`, shown adjacent to `검토 후보` only when aggregates exist, with one visible-but-disabled `검토 메모 적용 시작` action per aggregate card plus blocked helper copy only
- short-summary, per-chunk chunk-note, and reduce prompts, plus the internal `summary_chunks` anchor-selection heuristic, now all reuse the same truthful source boundary already known to current call sites, so local file or uploaded-document summaries keep document-flow and narrative-friendly guidance with a strict source-anchored faithfulness rule (no fabricated events, no term substitution, no conclusions beyond what the text shows) while selected local search-result summaries keep source-backed synthesis guidance with multi-result summaries using comparative wording and single-result summaries using non-comparative wording, without adding a new mode toggle or classifier
- PDF text-layer reading with OCR-not-supported guidance
- uploaded folder search shows a count-only partial-failure notice when some files cannot be read, while still returning results from successfully read files
- permission-gated web investigation with local JSON history, answer-mode badges, color-coded verification-strength badges (entity-card verification badge is downgraded from strong when no claim slot has cross-verified status), and color-coded source-role trust badges in history cards
- claim coverage panel with status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`), actionable hints for weak or unresolved slots, source role with trust level labels, and a color-coded fact-strength summary bar above the response text for web investigation

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
  - `http://127.0.0.1:8765`

## Verification

- Unit/service regression:
  - `python3 -m unittest -v`
- Browser smoke install:
  - `make e2e-install`
- Browser smoke run:
  - `make e2e-test`

## Playwright Smoke Coverage

Current smoke scenarios:
1. file summary renders evidence, summary-range panels, per-message timestamps in the transcript, response copy button state with clipboard write verification, source filename in quick-meta and transcript meta, note-path default-directory placeholder, and `문서 요약` source-type label in both quick-meta and transcript meta
2. browser file picker summary flow with source filename and `문서 요약` source-type label in both quick-meta and transcript meta
3. browser folder picker search flow with `선택 결과 요약` source-type label and multi-source count-based metadata (`출처 2개`) in both quick-meta and transcript meta
4. approval reissue with changed save path
5. approval-backed note save
6. late flip after explicit original-draft save keeps saved history while latest content verdict changes
7. `내용 거절` content-verdict path with same-card reject-note update, pending approval preserved, and later explicit save supersession
8. corrected-save first bridge path
9. corrected-save saved snapshot remains while late reject and later re-correct move the latest state separately
10. candidate-linked explicit confirmation path stays outside approval UI, remains distinct from save support on the same source message, records `candidate_confirmation_record`, surfaces one `검토 후보` with `검토 수락`, records source-message `candidate_review_record`, removes the pending queue item without applying user-level memory, and clears the current-source traces again after a later correction
11. same-session recurrence aggregate path renders one separate `검토 메모 적용 후보` section only after an aggregate exists, keeps `검토 메모 적용 시작` visible but disabled, keeps the queue-side `검토 수락` separate, and preserves `reviewed_memory_transition_record` absence
12. streaming cancel
13. general chat negative source-type label contract (no `문서 요약` / `선택 결과 요약` in quick-meta or transcript meta)
14. claim-coverage panel rendering contract with `[교차 확인]`, `[단일 출처]`, `[미확인]` leading status tags and actionable hints
15. web-search history card header badges: answer-mode badge (`설명 카드` / `최신 확인`), verification-strength badge (`검증 강` / `검증 중` / `검증 약` with CSS class), source-role trust badge compact label (`공식 기반(높음)` / `보조 기사(보통)` / `보조 커뮤니티(낮음)` with trust class)
16. history-card `다시 불러오기` 클릭 후 reloaded response의 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source-role detail 유지 확인

`make e2e-test` launches a dedicated Playwright web server for smoke with inherited `LOCAL_AI_MODEL_PROVIDER` / `LOCAL_AI_OLLAMA_MODEL` overrides cleared, `LOCAL_AI_MODEL_PROVIDER=mock` reapplied, and existing servers on the smoke port not reused. Shell overrides such as `LOCAL_AI_MODEL_PROVIDER=ollama` therefore do not change the automated baseline. Other runtimes remain optional and are validated separately.

## Safety Defaults

- local-first by default
- write actions require explicit approval
- overwrite is rejected by default; when a save target already exists, the approval card shows an overwrite warning and the user can explicitly approve the overwrite, which then replaces the existing file
- web search is permission-gated, read-only, and logged
- OCR is not enabled in the current MVP
- structured correction / preference memory is not yet implemented; the current memory foundation is limited to grounded-brief trace anchoring, normalized original-response snapshots, explicit `corrected_text` submission plus minimum `accepted_as_is` / `corrected` / `rejected` outcome capture on the source message, one source-message `content_reason_record` for explicit `내용 거절` plus optional same-card reject-note updates, and approval-linked `approval_reason_record` traces for reject / reissue
- the shipped candidate-linked reuse confirmation remains separate from approval-backed save support: it is stored as one source-message `candidate_confirmation_record`, leaves `session_local_candidate` unchanged, may materialize one source-message `durable_candidate` plus one pending `review_queue_items` entry, and now allows only one reviewed-but-not-applied `accept` action that writes source-message `candidate_review_record` without opening user-level memory
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
