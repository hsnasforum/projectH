# projectH

`projectH`는 **로컬 퍼스트 문서 비서 웹 MVP**입니다.
사용자는 로컬 파일을 읽고, 요약하고, 검색하고, 필요할 때만 승인 기반으로 저장할 수 있습니다. 웹 검색은 핵심 제품이 아니라 **보조 조사 모드**로 제한적으로 붙어 있습니다.

## Phase Split

### Current Shipped Contract
- 로컬 퍼스트 문서 비서 웹 MVP
- 핵심 루프: 문서 읽기 -> grounded summary -> 후속 질의 -> 승인 기반 저장
- 응답 피드백 수집, grounded-brief trace anchor, corrected-outcome capture, corrected-save bridge, reject/reissue reason traces
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

위 제외 항목들은 현재 repo 안에 함께 존재하지만, 이번 릴리즈 게이트의 기본 판정 대상은 아닙니다.

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
- one optional source-message-anchored `durable_candidate` projection plus one local `검토 후보` section fed only by current pending `review_queue_items`, with one `accept`-only reviewed-but-not-applied action that records source-message `candidate_review_record`
- one separate aggregate-level `검토 메모 적용 후보` section fed only by current same-session `recurrence_aggregate_candidates`, shown adjacent to `검토 후보` only when aggregates exist, with one visible-but-disabled `검토 메모 적용 시작` action per aggregate card plus blocked helper copy only
- short-summary, per-chunk chunk-note, and reduce prompts, plus the internal `summary_chunks` anchor-selection heuristic, now all reuse the same truthful source boundary already known to current call sites, so local file or uploaded-document summaries keep document-flow and narrative-friendly guidance with a strict source-anchored faithfulness rule (no fabricated events, no term substitution, no conclusions beyond what the text shows) while selected local search-result summaries keep source-backed synthesis guidance with multi-result summaries using comparative wording and single-result summaries using non-comparative wording, without adding a new mode toggle or classifier
- PDF text-layer reading: readable text-layer PDF는 visible summary body로 정상 요약되고(`문서 요약` label, context box/quick meta/transcript meta에 PDF 파일명 표시), scanned/image-only PDF는 visible OCR-not-supported guidance(`요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`)를 반환
- uploaded folder search shows a count-only partial-failure notice when some files cannot be read, while retaining readable-file result preview (search-only and search-plus-summary both preserve preview cards with ordered label, full-path tooltip, match badge, and snippet for successfully read files)
- permission-gated web investigation with local JSON history, answer-mode badges, color-coded verification-strength badges (entity-card verification badge is downgraded from strong when no claim slot has cross-verified status), and color-coded source-role trust badges in history cards
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
11. candidate-linked explicit confirmation path stays outside approval UI, remains distinct from save support on the same source message, records `candidate_confirmation_record`, surfaces one `검토 후보` with `검토 수락`, records source-message `candidate_review_record`, removes the pending queue item without applying user-level memory, and clears the current-source traces again after a later correction
12. same-session recurrence aggregate path renders one separate `검토 메모 적용 후보` section only after an aggregate exists, keeps `검토 메모 적용 시작` visible but disabled, keeps the queue-side `검토 수락` separate, and preserves `reviewed_memory_transition_record` absence
13. streaming cancel
14. general chat negative source-type label contract (no `문서 요약` / `선택 결과 요약` in quick-meta or transcript meta)
15. claim-coverage panel rendering contract with `[교차 확인]`, `[단일 출처]`, `[미확인]` leading status tags, actionable hints, and focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved with natural Korean particle normalization)
16. web-search history card header badges: answer-mode badge (`설명 카드` / `최신 확인`), verification-strength badge (`검증 강` / `검증 중` / `검증 약` with CSS class), source-role trust badge compact label (`공식 기반(높음)` / `보조 기사(보통)` / `보조 커뮤니티(낮음)` with trust class)
17. history-card entity-card `다시 불러오기` 클릭 후 reloaded response의 `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source-role detail 유지 확인
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
