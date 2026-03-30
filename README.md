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
- recent sessions / conversation timeline
- file summary / document search / general chat
- approval-based save
- reissue approval flow
- evidence / source panel
- summary span / applied-range panel
- response origin badge
- streaming progress + cancel
- response feedback capture
- grounded-brief artifact trace anchor on summary responses, save approvals, and relevant local traces
- normalized original-response snapshot, minimum `accepted_as_is` / `corrected` content-outcome capture, and minimum reject / reissue approval reason capture on grounded-brief traces
- small grounded-brief correction editor seeded with the current draft text, with explicit correction submit kept separate from save approval
- current save approvals and save/write traces now expose `save_content_source = original_draft | corrected_text` plus explicit `source_message_id` anchoring to the original grounded-brief source message
- minimum corrected-save bridge action that stays always visible inside the correction area, stays disabled until a recorded `corrected_text` exists, creates a fresh approval from that recorded text, freezes the approval snapshot under a new `approval_id`, and reuses the same `artifact_id` / `source_message_id` with `save_content_source = corrected_text`
- one small candidate-linked confirmation action on the grounded-brief response card that appears only when the current `session_local_candidate` exists and persists one separate source-message `candidate_confirmation_record`
- one optional source-message-anchored `durable_candidate` projection plus one local `검토 후보` section fed only by current pending `review_queue_items`, with one `accept`-only reviewed-but-not-applied action that records source-message `candidate_review_record`
- one separate aggregate-level `검토 메모 적용 후보` section fed only by current same-session `recurrence_aggregate_candidates`, shown adjacent to `검토 후보` only when aggregates exist, with one visible-but-disabled `검토 메모 적용 시작` action per aggregate card plus blocked helper copy only
- short-summary and long-summary prompts, plus the internal `summary_chunks` anchor-selection heuristic, now all reuse the same truthful source boundary already known to current call sites, so local file or uploaded-document summaries keep document-flow and narrative-friendly guidance while selected local search-result summaries keep source-backed synthesis guidance without adding a new mode toggle or classifier
- PDF text-layer reading with OCR-not-supported guidance
- permission-gated web investigation with local JSON history

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
1. file summary renders evidence and summary-range panels
2. browser file picker summary flow
3. browser folder picker search flow
4. approval reissue with changed save path
5. approval-backed note save
6. late flip after explicit original-draft save keeps saved history while latest content verdict changes
7. `내용 거절` content-verdict path with same-card reject-note update, pending approval preserved, and later explicit save supersession
8. corrected-save first bridge path
9. corrected-save saved snapshot remains while late reject and later re-correct move the latest state separately
10. candidate-linked explicit confirmation path stays outside approval UI, remains distinct from save support on the same source message, records `candidate_confirmation_record`, surfaces one `검토 후보` with `검토 수락`, records source-message `candidate_review_record`, removes the pending queue item without applying user-level memory, and clears the current-source traces again after a later correction
11. same-session recurrence aggregate path renders one separate `검토 메모 적용 후보` section only after an aggregate exists, keeps `검토 메모 적용 시작` visible but disabled, keeps the queue-side `검토 수락` separate, and preserves `reviewed_memory_transition_record` absence
12. streaming cancel

`make e2e-test` launches a dedicated Playwright web server for smoke with inherited `LOCAL_AI_MODEL_PROVIDER` / `LOCAL_AI_OLLAMA_MODEL` overrides cleared, `LOCAL_AI_MODEL_PROVIDER=mock` reapplied, and existing servers on the smoke port not reused. Shell overrides such as `LOCAL_AI_MODEL_PROVIDER=ollama` therefore do not change the automated baseline. Other runtimes remain optional and are validated separately.

## Safety Defaults

- local-first by default
- write actions require explicit approval
- overwrite is rejected by default
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
