# history-card entity-card reload-follow-up claim-coverage count-summary continuity tightening

## 변경 파일
- `tests/test_web_app.py` — simple entity-card reload 뒤 `load_web_search_record_id + user_text` follow-up 경로에서 `session.web_search_history[0].claim_coverage_summary` count dict 가 drift 없이 유지되는지 잠그는 focused 서비스 회귀 `test_handle_chat_load_web_search_record_id_entity_card_follow_up_preserves_claim_coverage_count_summary` 를 추가
- `e2e/tests/web-smoke.spec.mjs` — 기존 `history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다` 시나리오를 확장해, 시드 record 의 `claim_coverage`/progress-summary 에 맞춰 렌더된 history-item 에 `claim_coverage_summary: {strong:0, weak:1, missing:0}` 과 `claim_coverage_progress_summary: "단일 출처 상태 1건."` 을 추가하고, follow-up 전/후 모두 history-card `.meta` 가 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` 정확 문자열을 유지하는지 어서션

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-claim-coverage-count-summary-persistence-tightening.md`) 와 그 `/verify` 는 entity-card show-only reload 경로(`core/agent_loop.py:6370-6396`) 의 `claim_coverage_summary` store→serializer→browser persistence 를 `.meta` exact text 까지 잠갔음
- 같은 entity-card 가족 내부의 아직 잠기지 않은 current-risk 는 non-show-only follow-up 경로(`core/agent_loop.py:6398-6410`): `load_web_search_record_id + user_text` 조합으로 들어오는 follow-up 에서 `response.actions_taken` 에 `load_web_search_record` 가 prepend 되고 `response.response_origin` 은 stored origin 으로 채워지지만, 이 경로는 `_respond_with_active_context` 를 거쳐 session 을 재직렬화함 — 이 과정에서 `session.web_search_history` 의 `claim_coverage_summary` 가 show-only path 와 동일한 카운트로 유지되는지에 대한 명시적 회귀가 없었음
- browser 쪽에서도 기존 follow-up scenario(`e2e/tests/web-smoke.spec.mjs:1639-1754`) 는 WEB badge / answer-mode badge / origin detail 만 잠갔고, history-card `.meta` 의 `사실 검증 ...` count-summary 가 show-only reload 이후 follow-up 까지 유지되는지는 스모크에 없었음
- 이 슬라이스는 런타임 변경 없이 existing service-level follow-up regression 패턴과 existing browser follow-up scenario 를 각각 한 개씩 확장해 simple entity-card 가족의 first follow-up count-summary continuity 를 잠그는 범위임. latest-update / general reload, second follow-up, actual-search/dual-probe 가족은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` focused 서비스 회귀 추가**
   - `test_handle_chat_load_web_search_record_id_entity_card_follow_up_preserves_claim_coverage_count_summary`
     - mock `search_web` + simple entity-card record 로 `handle_chat({user_text})` 첫 호출 → baseline `claim_coverage_summary` dict 을 추출 (strong+weak+missing > 0 을 보장)
     - `handle_chat({load_web_search_record_id})` show-only reload 호출 → `session.web_search_history` 의 동일 record_id 항목에서 `claim_coverage_summary == baseline_counts` 을 잠금
     - `handle_chat({user_text + load_web_search_record_id})` follow-up 호출 → `response.actions_taken` 에 `load_web_search_record` 포함을 확인하고, `session.web_search_history` 의 동일 record_id 항목의 `claim_coverage_summary == baseline_counts` 을 다시 잠금
   - 기존 `test_handle_chat_load_web_search_record_id_entity_card_exact_fields` 와 동일한 `_FakeWebSearchTool`/`AppSettings`/`WebAppService` fixture 구성을 재사용했으며 신규 helper/import/fixture 파일은 추가하지 않음. baseline counts 를 함께 기록해 런타임 상 정확한 slot 카운트가 1 건만 되더라도 drift 여부를 엄격히 비교하도록 함
2. **`e2e/tests/web-smoke.spec.mjs` entity-card follow-up 시나리오 확장**
   - 렌더된 history item 에 `claim_coverage_summary: {strong: 0, weak: 1, missing: 0}` 과 `claim_coverage_progress_summary: "단일 출처 상태 1건."` 을 추가 — 시드 record 의 `claim_coverage: [{weak}]` 과 `claim_coverage_progress_summary: "단일 출처 상태 1건."` 에 정확히 대응되므로 클릭 이후 서버가 `list_session_record_summaries` 로 다시 직렬화해도 client-seeded 값과 동일한 결과가 나와 `.meta` 가 튀지 않음
   - show-only reload 클릭 직후 `.meta` 어서션 추가:
     - `toHaveCount(1)` / `toHaveText("사실 검증 단일 출처 1 · 단일 출처 상태 1건.")`
     - `not.toContainText("설명 카드")` / `not.toContainText("최신 확인")` / `not.toContainText("일반 검색")` — entity_card investigation 이므로 detailLines 가 answer-mode label 을 skip
     - `preFollowUpMetaText.startsWith("·") === false` / `endsWith("·") === false`
     - `preFollowUpMetaText.indexOf("사실 검증 단일 출처 1") < indexOf("단일 출처 상태 1건")` — count 라인이 progress 라인보다 앞에 오는 합성 순서 잠금
   - `sendRequest({ user_text, load_web_search_record_id })` follow-up 실행 이후에도 같은 `.meta` 정확 문자열과 leading/trailing separator artifact 부정 어서션을 한 번 더 반복 — store→serializer→reload follow-up path 에서 count-summary + progress-summary 합성이 유지됨을 end-to-end 로 잠금
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_follow_up_preserves_claim_coverage_count_summary` → `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다" --reporter=line` → `1 passed (6.4s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 `WebAppService.handle_chat` 경로에 순수 추가 회귀만 붙였고 기존 로직 변경이 없음. handoff 도 단일 focused regression + 기존 entity-card exact-fields 테스트만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 단일 follow-up scenario 한 개만 확장함
- 다른 latest-update / general / dual-probe / actual-search follow-up scenario — 이번 슬라이스는 simple entity-card first follow-up only 로 의도적으로 한정

## 남은 리스크
- browser `.meta` 잠금은 `formatClaimCoverageCountSummary({weak:1})` 이 정확히 `"단일 출처 1"` 을 내고 `detailLines.join(" · ")` 구분자가 ` · ` 라는 점에 의존함. 포맷(`app/static/app.js:2225-2232`) 이 바뀌면 이 스모크가 먼저 깨짐 — 다만 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- 서비스 회귀는 `baseline_counts` 에 첫 호출의 실제 mock entity-card 결과를 그대로 사용함. 향후 `_FakeWebSearchTool` 의 기본 응답이나 `_summarize_claim_coverage` 의 분류 기준이 바뀌어 slot 수가 0 이 되면 회귀 자체가 `assertGreater(..., 0)` 에서 먼저 실패해 원인을 빠르게 가리킴 — 이는 의도된 failure-first 설계
- follow-up 경로(`core/agent_loop.py:6398-6410`) 는 `_respond_with_active_context` 를 거쳐 `response_origin` 이 stored origin 없으면 내부에서 새로 만들어질 수 있음. 이번 라운드는 stored origin 이 있는 simple entity-card 경로만 잠그므로, stored origin 이 비어 있는 follow-up 케이스(response_origin 재구성 경로) 는 별도 가족으로 남겨둠
- second follow-up / latest-update follow-up / dual-probe follow-up / actual-search follow-up 에서 count-summary continuity 는 이 슬라이스 범위 밖이며, 각각 다른 `_infer_reloaded_answer_mode` 분기 및 source-role 필터링을 함께 고려해야 하므로 별도 라운드로 남겨둠
- client-seeded `claim_coverage_summary` 값이 record 의 실제 `_summarize_claim_coverage` 결과와 일치해야 pre-click 과 post-follow-up `.meta` 가 동일한 문자열을 유지함. 시드가 비대칭이면 follow-up 이후 서버 재직렬화에서 서로 다른 값이 나와 `.meta` 가 튈 수 있어, 이번 라운드는 두 값을 동일하게 맞춰 잠갔음
