# history-card entity-card reload-second-follow-up claim-coverage count-summary continuity tightening

## 변경 파일
- `tests/test_web_app.py` — 기존 first-follow-up 회귀를 mirror 해 두 번째 `load_web_search_record_id + user_text` follow-up 까지 `session.web_search_history` 의 `claim_coverage_summary` dict 가 baseline 과 동일하게 유지되는지 잠그는 `test_handle_chat_load_web_search_record_id_entity_card_second_follow_up_preserves_claim_coverage_count_summary` 추가
- `e2e/tests/web-smoke.spec.mjs` — 신규 시나리오 `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다` 추가. 동일 simple single-source entity-card seed/fixture shape 를 재사용해 show-only reload → 첫 follow-up → 두 번째 follow-up 흐름을 실행하고, 마지막 follow-up 이후에도 history-card `.meta` 가 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` 정확 문자열과 합성 순서를 유지하는지 잠금

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-reload-follow-up-claim-coverage-count-summary-continuity-tightening.md`) 와 그 `/verify` 는 simple entity-card 가족의 show-only reload 와 **첫 번째** follow-up 에서 `claim_coverage_summary` persistence 를 잠갔음
- 같은 simple entity-card click-reload 가족 내부의 아직 잠기지 않은 current-risk 는 **두 번째** follow-up 경로: `core/agent_loop.py:6398-6410` 은 `load_web_search_record_id + user_text` 를 받는 각 turn 마다 반복적으로 reload-follow-up path 를 타며, 두 번째 follow-up 에서 stored record 의 `claim_coverage` 가 서로 다른 답변 텍스트나 active_context 재작성 와중에 드리프트되지 않는지에 대한 명시적 회귀가 없었음
- 다른 actual-search / dual-probe / zero-strong 가족은 이미 second-follow-up continuity 커버리지가 있으므로, 가장 작은 남은 gap 은 동일 깊이의 simple single-source 가족 — 이 슬라이스는 그 gap 을 한 라운드에 닫는 범위임
- 이 슬라이스는 런타임 변경 없이 existing first-follow-up 회귀/시나리오 패턴을 그대로 확장해 second-follow-up 경로를 잠그는 범위이며, latest-update / general / actual-search / dual-probe / zero-strong / stored-origin-missing fallback 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` focused 서비스 회귀 추가**
   - `test_handle_chat_load_web_search_record_id_entity_card_second_follow_up_preserves_claim_coverage_count_summary`
     - 첫 `handle_chat({user_text})` 호출 → baseline `claim_coverage_summary` dict 추출 (strong+weak+missing > 0 보장)
     - `handle_chat({load_web_search_record_id})` show-only reload 호출
     - `handle_chat({user_text + load_web_search_record_id})` 첫 follow-up 호출 → `actions_taken` 에 `load_web_search_record` 포함 확인, `session.web_search_history` 의 동일 record 항목 `claim_coverage_summary == baseline_counts` 잠금
     - `handle_chat({user_text + load_web_search_record_id})` **두 번째 follow-up** 호출 → 동일하게 `actions_taken` 에 `load_web_search_record` 포함 확인, `session.web_search_history` 의 동일 record 항목 `claim_coverage_summary == baseline_counts` 재잠금
   - 기존 first-follow-up 회귀 (`test_handle_chat_load_web_search_record_id_entity_card_follow_up_preserves_claim_coverage_count_summary`) 와 동일한 `_FakeWebSearchTool` / `AppSettings` / `WebAppService` fixture 구성을 그대로 재사용했고 신규 helper/import/fixture 파일은 추가하지 않음. 두 번째 follow-up 은 첫 follow-up 과 다른 `user_text` (`"장르만 한 줄로 다시 정리해줘"`) 를 사용해 turn 이 실제로 두 번 발생하는지 확인함
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오 추가**
   - 시나리오 이름: `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다`
   - 기존 first-follow-up 시나리오(`:1639-1785`) 의 seed record (`response_origin` 에 `provider/badge/label/answer_mode/verification_label/source_roles` 포함, `claim_coverage: [{weak}]`, `claim_coverage_progress_summary: "단일 출처 상태 1건."`) 모양을 그대로 재사용
   - 동일하게 `renderSearchHistory` item 에 `claim_coverage_summary: {strong:0, weak:1, missing:0}` 과 `claim_coverage_progress_summary: "단일 출처 상태 1건."` 을 seed 해, reload 후 server 재직렬화 결과가 client seed 와 완전히 일치하도록 맞춤
   - 흐름:
     - `renderSearchHistory` → `다시 불러오기` 클릭 (show-only reload)
     - `#response-origin-badge === "WEB"` / `#response-answer-mode-badge === "설명 카드"` 확인
     - `sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id })` 첫 follow-up 실행 후 badge 유지 및 `.meta === "사실 검증 단일 출처 1 · 단일 출처 상태 1건."` 잠금
     - `sendRequest({ user_text: "장르만 한 줄로 다시 정리해줘", load_web_search_record_id })` **두 번째 follow-up** 실행
     - 두 번째 follow-up 이후 `#response-origin-badge === "WEB"` + `web` class, `#response-answer-mode-badge === "설명 카드"`, `#response-origin-detail` 가 `설명형 단일 출처` 와 `백과 기반` 을 포함하는지 확인
     - `.meta` 가 여전히 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` 정확 문자열이고, `not.toContainText("설명 카드")`/`"최신 확인"`/`"일반 검색"` 로 answer-mode label 누출 없음, `startsWith("·") === false` / `endsWith("·") === false`, `indexOf("사실 검증 단일 출처 1") < indexOf("단일 출처 상태 1건")` 로 count 라인이 progress 라인보다 앞에 오는 합성 순서 잠금
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_follow_up_preserves_claim_coverage_count_summary` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_second_follow_up_preserves_claim_coverage_count_summary` → `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다" --reporter=line` → `1 passed (6.5s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 `handle_chat` 경로에 순수 추가 회귀만 붙였고 기존 로직 변경이 없음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 단일 신규 isolated scenario 하나만 추가함
- 다른 first-follow-up/latest-update/general/actual-search/dual-probe/zero-strong 시나리오 — 이번 슬라이스는 simple entity-card second follow-up only 로 의도적으로 한정

## 남은 리스크
- 브라우저 `.meta` 잠금은 `formatClaimCoverageCountSummary({weak:1})` 이 `"단일 출처 1"` 을 내고 `detailLines.join(" · ")` separator 가 ` · ` 라는 점에 의존함. 포맷(`app/static/app.js:2225-2232`) 이 바뀌면 이 스모크가 먼저 깨짐 — 다만 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- 서비스 회귀의 `baseline_counts` 는 첫 호출의 실제 mock entity-card 결과를 그대로 사용함. `_FakeWebSearchTool` 기본 응답이나 `_summarize_claim_coverage` 분류 기준이 바뀌어 slot 수가 0 이 되면 `assertGreater(..., 0)` 에서 먼저 실패해 원인을 빠르게 가리킴 — 의도된 failure-first 설계
- 두 번째 follow-up 의 `user_text` 는 첫 follow-up 과 다른 문자열 (`"장르만 한 줄로 다시 정리해줘"`) 을 사용함. 향후 `handle_chat` 내부에서 해당 문자열을 별도 intent 로 해석해 reload-follow-up path 가 아닌 다른 경로로 빠지면 회귀의 `actions_taken` 단언에서 먼저 실패해 원인을 빠르게 가리킴
- latest-update / general / actual-search / dual-probe / zero-strong / stored-origin-missing fallback 가족의 second-follow-up 경로는 이 슬라이스 범위 밖이며 각각 다른 `_infer_reloaded_answer_mode` 분기와 source-role 필터링을 함께 고려해야 하므로 별도 라운드로 남겨둠
- client-seeded `claim_coverage_summary` 값이 record 의 실제 `_summarize_claim_coverage` 결과와 일치해야 pre/post `.meta` 가 동일 문자열을 유지함. 시드가 비대칭이면 follow-up 이후 서버 재직렬화에서 서로 다른 값이 나와 `.meta` 가 튈 수 있어, 이번 라운드는 두 값을 동일하게 맞춰 잠갔음
