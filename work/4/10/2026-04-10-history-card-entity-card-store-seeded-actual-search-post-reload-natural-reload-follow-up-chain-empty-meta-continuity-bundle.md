# history-card entity-card store-seeded actual-search post-reload natural-reload follow-up-chain empty-meta continuity bundle

## 변경 파일
- `tests/test_web_app.py` — 신규 서비스 회귀 `test_handle_chat_entity_card_store_seeded_actual_search_post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak` 추가. 기존 store-seeded click-reload 회귀들(`:16978`, CONTROL_SEQ 46 에서 추가된 `:17071`) 은 전혀 건드리지 않음. 신규 회귀는 `WebSearchStore.save(...)` 를 `claim_coverage` 파라미터 없이 호출 → click reload → 자연어 reload → first follow-up → second follow-up 네 단계의 전체 체인을 수행하고, 공통 헬퍼 `_assert_empty_meta_continuity(result, stage)` 로 **네 단계 모두** (각 단계마다, 마지막 단계에서만이 아님) `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}`, 빈 `claim_coverage_progress_summary`, `verification_label == "설명형 다중 출처 합의"`, `response_origin.answer_mode == "entity_card"`, `source_roles == ["백과 기반"]`, 그리고 `active_context.source_paths` 에 두 위키 URL 이 유지되는지 잠금
- `e2e/tests/web-smoke.spec.mjs` — 신규 브라우저 시나리오 `history-card entity-card store-seeded actual-search 자연어 reload 체인에서 empty-meta no-leak contract가 유지됩니다` 를 기존 store-seeded click-reload first/second follow-up 시나리오 바로 뒤, 기존 runtime-backed first-follow-up 시나리오 앞에 삽입. 디스크 record 에 `claim_coverage: []` + 빈 progress 를 시드하고, `renderSearchHistory` item 에는 `claim_coverage_summary` / `claim_coverage_progress_summary` 를 **전혀 seed 하지 않음**. click reload → natural reload → first follow-up → second follow-up 흐름 이후 기존 origin/answer-mode/origin-detail/source-path 연속성 어서션과 `historyCard.locator(".meta") toHaveCount(0)` + `historyCard not.toContainText("사실 검증")` no-leak 잠금을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-store-seeded-actual-search-click-reload-second-follow-up-empty-meta-no-leak-bundle.md`) 는 store-seeded actual-search 가족의 **click-reload** chain (click reload → first follow-up → second follow-up) 을 전 구간 잠갔음. 본 라운드는 동일 가족의 **post-reload 이후 자연어 reload** 분기를 추가로 잠그는 범위임
- `storage/web_search_store.py:316-317` 의 `_summarize_claim_coverage` 는 `WebSearchStore.save(...)` 가 `claim_coverage` 파라미터 없이 호출되면 `list_session_record_summaries` 단계에서 `{strong:0, weak:0, missing:0}` 을 반환함. `app/serializers.py:280-287` 은 이 zero-count dict 를 그대로 직렬화하고, `app/static/app.js:2954-2969` 의 history card 렌더러는 investigation entity_card 에 대해 answer-mode label 을 skip + `formatClaimCoverageCountSummary({0,0,0})` = 빈 문자열이므로 `detailLines` 가 비어 `.meta` detail node 자체가 생성되지 않음. 이 no-leak 계약이 자연어 reload 체인 전 구간에 걸쳐 유지되는지에 대한 명시적 회귀/스모크가 없었음
- 기존 coverage 상태:
  - store-seeded actual-search coverage 는 click-reload 가족만 존재 (`tests/test_web_app.py:16978`, `:17071`, `e2e/tests/web-smoke.spec.mjs:3596`, `:3721`)
  - runtime-backed actual-search natural-reload coverage 는 별도로 존재 (`tests/test_web_app.py:18282`, `:18350`, `:18421`, `e2e/tests/web-smoke.spec.mjs:6895`, `:7025`, `:7110`)
  - 두 축이 만나는 store-seeded × natural-reload 조합은 본 라운드 이전까지 비어 있었음
- 이 슬라이스는 런타임 변경 없이 service 회귀 한 개와 browser 시나리오 한 개를 **신규 추가** 해 store-seeded × natural-reload chain 분기를 bounded bundle 로 잠그는 범위임. runtime-backed strong-plus-missing, 다른 natural-reload 가족, dual-probe, zero-strong, latest-update, noisy, general, docs, pipeline 은 의도적으로 범위 밖
- handoff 는 "blocked sentinel did not provide a usable diagnostic reason" 을 명시해 CONTROL_SEQ 47 의 비-신호 sentinel 에 근거해 escalate 하지 말라고 지시했고, 본 라운드는 그 지침에 따라 동일 scope 를 재검증 없이 구현함. 또한 test 이름은 `..._post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak` 로 명시해 체인 구조와 계약을 한 이름에 모두 담음

## 핵심 변경
1. **`tests/test_web_app.py` 신규 서비스 회귀**
   - `test_handle_chat_entity_card_store_seeded_actual_search_post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak`
     - `WebSearchStore(base_dir=...)` 로 store 를 생성하고 `store.save(session_id, query, permission, results, summary_text, pages=[], response_origin={...})` 를 **`claim_coverage` 파라미터 없이** 호출해 record 를 시드
     - `_FakeWebSearchTool([])` 로 service 를 초기화해 체인 단계에서 실제 web search 가 실행되지 않도록 함
     - `store.list_session_record_summaries(session_id)[0]["record_id"]` 로 record_id 를 추출
     - 내부 공통 헬퍼 `_assert_empty_meta_continuity(result, stage)` 를 정의해 각 단계에서 다음을 일괄 잠금 (handoff 가 "at each meaningful stage you traverse, not only at the end" 라고 명시함):
       - `result["ok"]` 참
       - `result["response"]["actions_taken"]` 에 `load_web_search_record` 포함
       - `active_context.source_paths` 에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`, `https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89` 포함
       - `response_origin.answer_mode == "entity_card"`, `verification_label == "설명형 다중 출처 합의"`, `source_roles == ["백과 기반"]`
       - `web_search_history` 의 해당 record_id 항목이 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}`, 빈 `claim_coverage_progress_summary`, `verification_label == "설명형 다중 출처 합의"`
     - 네 단계 순차 실행:
       - `first` = click reload (`load_web_search_record_id` only, show-only) → `_assert_empty_meta_continuity(first, "click reload")`
       - `second` = 자연어 reload (`user_text: "방금 검색한 결과 다시 보여줘"`, no `load_web_search_record_id`) → `_assert_empty_meta_continuity(second, "natural reload")`
       - `third` = 첫 follow-up (`user_text: "이 검색 결과 요약해줘"` + `load_web_search_record_id`) → `_assert_empty_meta_continuity(third, "first follow-up")`
       - `fourth` = 두 번째 follow-up (`user_text: "더 자세히 알려줘"` + `load_web_search_record_id`) → `_assert_empty_meta_continuity(fourth, "second follow-up")`
   - 기존 `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` (CONTROL_SEQ 45 완료), `test_handle_chat_entity_card_store_seeded_actual_search_reload_second_follow_up_preserves_empty_meta_no_leak` (CONTROL_SEQ 46 완료) 는 **전혀 건드리지 않음** (handoff 지시)
   - `WebSearchStore` / `AppSettings` / `WebAppService` / `FileReaderTool` / `FileSearchTool` / `WriteNoteTool` / `_FakeWebSearchTool` fixture 는 재사용, 신규 helper/import/fixture 파일 없음
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오**
   - 신규 테스트 이름: `history-card entity-card store-seeded actual-search 자연어 reload 체인에서 empty-meta no-leak contract가 유지됩니다`
   - 직전 라운드(CONTROL_SEQ 46) 에서 추가한 store-seeded second-follow-up 시나리오 바로 뒤, 기존 runtime-backed `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(...)` 시나리오 앞에 삽입해 store-seeded 가족이 click-reload first-follow-up + click-reload second-follow-up + natural-reload chain 세 시나리오로 파일 내에서 인접 배치되도록 함
   - 디스크 record 에 `claim_coverage: []` + 빈 `claim_coverage_progress_summary` 시드
   - `renderSearchHistory` item 에는 `claim_coverage_summary` / `claim_coverage_progress_summary` 를 **전혀 seed 하지 않음** (의도된 설계 — client seed 가 붙으면 pre-click `.meta` 가 생성될 수 있어 no-leak 잠금이 false-fail 할 수 있음)
   - 흐름:
     - `renderSearchHistory` → `다시 불러오기` 클릭 (show-only reload)
     - `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` 자연어 reload
     - `sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id }, "follow_up")` 첫 follow-up
     - `sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id }, "follow_up")` 두 번째 follow-up
   - second follow-up 이후 기존 어서션 유지:
     - `#response-origin-badge === "WEB"` + `web` class
     - `#response-answer-mode-badge` visible + `"설명 카드"`
     - `#response-origin-detail` 이 `설명형 다중 출처 합의` + `백과 기반` 포함
     - `#context-box` 가 `namu.wiki` + `ko.wikipedia.org` 포함 (source-path 연속성)
   - 신규 empty-meta no-leak 어서션:
     - `historyCard.locator(".meta") toHaveCount(0)` — 자연어 reload 체인 이후에도 detail `.meta` 가 전혀 생성되지 않음
     - `historyCard not.toContainText("사실 검증")` — accidental `.meta` creation 으로 count line 이 leak 되는 경우 방어 double-guard
   - 기존 store-seeded click-reload first/second follow-up 시나리오와 runtime-backed actual-search 시나리오는 **전혀 건드리지 않음** (handoff 지시)
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
3. runtime-backed strong-plus-missing / 다른 natural-reload 가족 / dual-probe / zero-strong / latest-update / noisy / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_store_seeded_actual_search_post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary` → 두 테스트 모두 `ok` (네 단계 체인 모두에서 zero-count + 빈 progress + stored label + source-path continuity 가 `_assert_empty_meta_continuity` 로 잠겼고, `list_session_record_summaries` 기본 계약도 함께 통과)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "store-seeded actual-search.*자연어 reload.*empty-meta|store-seeded actual-search.*자연어 reload.*follow-up" --reporter=line` → `1 passed (6.8s)` (신규 자연어 reload 체인 시나리오 한 개가 정규식에 매칭되어 실행; `ok`)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 store-seeded 자연어 reload 체인 회귀 **한 개를 신규 추가** 했고 기존 로직/회귀의 외부 동작을 전혀 바꾸지 않음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 신규 시나리오 한 개만 추가함
- 기존 store-seeded click-reload / runtime-backed actual-search / dual-probe / zero-strong / latest-update / noisy / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 신규 서비스 회귀의 정확 dict equality (`{"strong": 0, "weak": 0, "missing": 0}`) 는 `_summarize_claim_coverage([])` 가 `{strong:0, weak:0, missing:0}` 을 내는 현재 `storage/web_search_store.py:316-317` 구현에 의존함. 해당 기본값이 None 또는 추가 key 를 포함하도록 바뀌면 네 단계 중 해당 equality 가 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계이며, 같은 stage 에 대해 `_assert_empty_meta_continuity` 가 네 번 호출되어 stage 별 실패 메시지가 서로 구분됨
- 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 false-fail 됨. 같은 가정이 이전 latest-update / store-seeded click-reload empty-meta 라운드들에서도 사용 중이라 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 badge/summary 영역에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- store-seeded 경로에서 `renderSearchHistory` item 에 `claim_coverage_summary` 를 seed 하지 않는 것이 의도된 설계임. seed 하면 client-side 에서 `.meta` 가 생성될 수 있어 `toHaveCount(0)` 어서션이 false-fail 할 수 있음 — 이 의도는 코드 주석으로 명시해 두었음
- CONTROL_SEQ 45, 46 (store-seeded click-reload), 본 CONTROL_SEQ 48 (store-seeded post-reload natural-reload chain) 가 같은 store-seeded 가족 내부의 click-reload vs natural-reload 분기를 각각 잠가 store-seeded × actual-search × entity-card 조합이 browser + service 양쪽에서 end-to-end 로 닫힘
- handoff 가 명시한 대로 네 단계 **각각** (click reload → natural reload → first follow-up → second follow-up) 에서 `_assert_empty_meta_continuity` 가 호출되므로, 중간 단계에서 zero-count 분기가 깨지는 경우에도 stage 이름이 어서션 메시지에 포함되어 실패 지점이 명확함. 이는 "assert the same stored zero-count branch at each meaningful stage you traverse, not only at the end" 요구를 직접 구현함
- CONTROL_SEQ 47 의 sentinel 은 `<short_reason>` placeholder 만 담고 있어 진단 근거가 불충분했고, handoff 48 은 그 sentinel 에 근거해 escalate 하지 말라고 명시함. 본 라운드는 그 지침대로 동일 scope 를 재검토 없이 구현했으며, 테스트 이름을 `..._post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak` 로 변경해 handoff 의 required verification command 와 정확히 일치시킴
- 시나리오/회귀를 신규 추가했으므로 기존 coverage 와 겹치지 않고 파일 내에서 store-seeded 가족이 click-reload first/second follow-up → 자연어 reload chain 세 시나리오로 인접 배치되어 향후 reader 가 두 가족 경계(`store-seeded` vs runtime-backed, `click-reload` vs `natural-reload`) 를 시각적으로 구분할 수 있음
