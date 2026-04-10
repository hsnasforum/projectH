# history-card entity-card store-seeded actual-search click-reload-second-follow-up empty-meta no-leak bundle

## 변경 파일
- `tests/test_web_app.py` — 신규 서비스 회귀 `test_handle_chat_entity_card_store_seeded_actual_search_reload_second_follow_up_preserves_empty_meta_no_leak` 추가. 기존 first-follow-up 테스트 (`test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths`) 는 건드리지 않음. 신규 회귀는 `WebSearchStore.save(...)` 를 `claim_coverage` 파라미터 없이 호출한 뒤 click reload → first follow-up → second follow-up 체인을 실행하고, 마지막 (second follow-up) 응답에서 `session.web_search_history` 의 해당 record 항목이 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}`, 빈 `claim_coverage_progress_summary`, `verification_label == "설명형 다중 출처 합의"` 를 유지하는지 확인 (stored response-origin 및 `active_context.source_paths` 연속성도 함께 잠금)
- `e2e/tests/web-smoke.spec.mjs` — 신규 브라우저 시나리오 `history-card entity-card store-seeded actual-search 다시 불러오기 후 두 번째 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다` 를 기존 store-seeded first-follow-up 시나리오 바로 뒤, 기존 runtime-backed first-follow-up 시나리오 앞에 삽입. 디스크 record 에 `claim_coverage: []` + 빈 progress 를 시드하고 `renderSearchHistory` item 에는 `claim_coverage_summary` / `claim_coverage_progress_summary` 를 **전혀 seed 하지 않음**. click reload → first follow-up → second follow-up 흐름 이후 WEB/설명 카드/origin detail/source-path 연속성 어서션과 `historyCard.locator(".meta") toHaveCount(0)` + `historyCard not.toContainText("사실 검증")` 잠금을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-store-seeded-actual-search-click-reload-follow-up-empty-meta-no-leak-bundle.md`) 는 store-seeded actual-search 가족의 **click-reload → first follow-up** empty-meta no-leak 계약을 잠갔음. 본 라운드는 같은 store-seeded 가족에서 **두 번째 follow-up** 까지 체인이 한 단계 확장된 edge 를 별도 bundle 로 잠그는 범위임
- `storage/web_search_store.py:316-317` 의 `_summarize_claim_coverage` 는 `WebSearchStore.save(...)` 가 `claim_coverage` 파라미터 없이 호출되면 `list_session_record_summaries` 단계에서 `{strong:0, weak:0, missing:0}` 을 반환하고, 이 zero-count dict 는 `app/serializers.py:280-287` 을 거쳐 그대로 직렬화됨
- `app/static/app.js:2954-2969` 의 history card 렌더러는 investigation entity_card 에 대해 answer-mode label 을 skip 하고, `formatClaimCoverageCountSummary({0,0,0})` 가 빈 문자열을 내므로 `detailLines` 는 비게 되어 `.meta` detail node 자체가 생성되지 않아야 함. 이 no-leak 계약은 second follow-up 이후에도 동일하게 유지되어야 하는데, 직접적인 회귀/스모크로 잠기지 않은 상태였음
- CONTROL_SEQ 32/42/44 는 runtime-backed strong-plus-missing (`{3, 0, 2}`) 분기의 browser second-follow-up 을 잠갔고, CONTROL_SEQ 45 는 store-seeded empty-meta 분기의 click-reload → first follow-up 을 잠갔음. 본 CONTROL_SEQ 46 은 store-seeded empty-meta 분기의 second follow-up edge 만 정확히 잠궈 actual-search 가족의 browser-side `.meta` 계약이 양쪽 분기에서 end-to-end 로 닫히도록 하는 범위임
- runtime-backed strong-plus-missing / natural reload / dual-probe / zero-strong / latest-update / noisy / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` 신규 서비스 회귀 추가**
   - `test_handle_chat_entity_card_store_seeded_actual_search_reload_second_follow_up_preserves_empty_meta_no_leak`
     - 기존 `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` (CONTROL_SEQ 45 완료) 바로 뒤에 배치해 store-seeded 가족 테스트가 인접하게 모이도록 함
     - `WebSearchStore(base_dir=...)` 로 store 를 생성하고 `store.save(session_id, query, permission, results, summary_text, pages=[], response_origin={...})` 를 **`claim_coverage` 파라미터 없이** 호출해 record 를 시드
     - `_FakeWebSearchTool([])` 로 service 를 초기화해 follow-up 단계에서 실제 web search 가 실행되지 않도록 함 (store-seeded 경로를 순수하게 exercise)
     - `store.list_session_record_summaries(session_id)[0]["record_id"]` 로 record_id 를 추출
     - 네 번의 `service.handle_chat({...})` 호출을 순차 실행:
       - `first` = click reload (`load_web_search_record_id` only, show-only)
       - `second` = first follow-up (`user_text: "이 검색 결과 요약해줘"` + `load_web_search_record_id`)
       - `third` = second follow-up (`user_text: "더 자세히 알려줘"` + `load_web_search_record_id`)
     - `third` 응답 단계에서 다음을 잠금:
       - `active_context.source_paths` 에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`, `https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89` 포함
       - `response_origin.answer_mode == "entity_card"`, `verification_label == "설명형 다중 출처 합의"`, `source_roles == ["백과 기반"]`
       - `followup_entry = next((item for item in third["session"]["web_search_history"] if item.get("record_id") == record_id), None)` + `assertIsNotNone`
       - `followup_entry.get("claim_coverage_summary") or {} == {"strong": 0, "weak": 0, "missing": 0}`
       - `str(followup_entry.get("claim_coverage_progress_summary") or "") == ""`
       - `followup_entry["verification_label"] == "설명형 다중 출처 합의"`
   - 기존 first-follow-up 테스트 (`:16978`) 는 handoff 지시대로 **전혀 건드리지 않음**
   - `WebSearchStore` / `AppSettings` / `WebAppService` / `FileReaderTool` / `FileSearchTool` / `WriteNoteTool` / `_FakeWebSearchTool` fixture 는 재사용, 신규 helper/import/fixture 파일 없음
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오 추가**
   - 신규 테스트 이름: `history-card entity-card store-seeded actual-search 다시 불러오기 후 두 번째 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다`
   - 직전 라운드에서 추가한 `history-card entity-card store-seeded actual-search 다시 불러오기 후 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다` 시나리오 바로 뒤, 기존 runtime-backed `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(...)` 시나리오 앞에 삽입해 store-seeded 가족이 first-follow-up + second-follow-up 두 짝으로 인접 배치되도록 함
   - 디스크 record 에 `claim_coverage: []` + 빈 `claim_coverage_progress_summary` 를 명시적으로 시드
   - `renderSearchHistory` item 에는 `claim_coverage_summary` / `claim_coverage_progress_summary` 를 **전혀 seed 하지 않음** — client-side 에서도 detail `.meta` 가 생성되지 않는 경로를 그대로 exercise
   - 흐름:
     - `renderSearchHistory` → `다시 불러오기` 클릭 (show-only reload)
     - `sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id }, "follow_up")` first follow-up
     - `sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id }, "follow_up")` **second follow-up**
   - second follow-up 이후 기존 어서션:
     - `#response-origin-badge === "WEB"` + `web` class
     - `#response-answer-mode-badge` visible + `"설명 카드"`
     - `#response-origin-detail` 이 `설명형 다중 출처 합의` + `백과 기반` 포함
     - `#context-box` 가 `namu.wiki` + `ko.wikipedia.org` 포함 (source-path 연속성)
   - 신규 empty-meta no-leak 어서션:
     - `historyCard.locator(".meta") toHaveCount(0)` — second follow-up 이후에도 detail `.meta` 가 전혀 생성되지 않음
     - `historyCard not.toContainText("사실 검증")` — accidental `.meta` creation 으로 count line 이 leak 되는 경우 방어 double-guard
   - 기존 store-seeded first-follow-up 시나리오는 handoff 지시대로 **전혀 건드리지 않음** (라운드 45 에서 이미 잠금)
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
3. runtime-backed strong-plus-missing / natural reload / dual-probe / zero-strong / latest-update / noisy / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_store_seeded_actual_search_reload_second_follow_up_preserves_empty_meta_no_leak tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary` → 세 테스트 모두 `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "store-seeded actual-search.*두 번째 follow-up|store-seeded actual-search.*second-follow-up|store-seeded actual-search.*empty-meta" --reporter=line` → `2 passed (11.7s)` (first-follow-up CONTROL_SEQ 45 시나리오와 second-follow-up 신규 시나리오 두 개가 `-g` 정규식에 모두 매칭되어 실행; 둘 다 `ok`)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 store-seeded 서비스 회귀 **한 개를 신규 추가** 했고 기존 회귀의 외부 동작을 바꾸지 않음. handoff 도 focused 세 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 신규 시나리오 한 개만 추가함
- 기존 runtime-backed actual-search / dual-probe / natural reload / second follow-up / zero-strong / latest-update / noisy / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 신규 서비스 회귀의 정확 dict equality (`{"strong": 0, "weak": 0, "missing": 0}`) 는 `_summarize_claim_coverage([])` 가 `{strong:0, weak:0, missing:0}` 을 내는 현재 `storage/web_search_store.py:316-317` 구현에 의존함. 해당 기본값이 None 또는 추가 key 를 포함하도록 바뀌면 equality 가 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계
- 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 false-fail 됨. 같은 가정이 이전 latest-update / store-seeded first-follow-up empty-meta 라운드들에서도 사용 중이라 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 badge/summary 영역에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- store-seeded 경로에서 `renderSearchHistory` item 에 `claim_coverage_summary` 를 seed 하지 않는 것이 의도된 설계임. seed 하면 client-side 에서 `.meta` 가 생성될 수 있어 `toHaveCount(0)` 어서션이 false-fail 할 수 있음 — 이 의도는 주석으로 명시해 두었음
- first follow-up (CONTROL_SEQ 45) 과 second follow-up (본 라운드) 시나리오는 동일한 seed 규약과 동일한 `.meta` 어서션을 공유함. 두 시나리오는 체인 길이만 다르며, `-g` 정규식에서 자연스럽게 함께 매칭됨
- CONTROL_SEQ 32/42/44 (runtime-backed strong-plus-missing) 와 CONTROL_SEQ 45/46 (store-seeded empty-meta) 이 각기 다른 분기로 잠겨 두 가족이 browser 파일 내에서 인접 배치됨. 향후 두 가족이 혼재되지 않는지 여러 라운드의 failure-first 어서션이 함께 감시함
- 시나리오/회귀를 in-place 로 추가했으므로 이름은 명시적으로 `store-seeded` prefix 를 포함함. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
- handoff 는 "keep the existing first-follow-up test untouched unless a tiny local extension is cleaner" 라고 허용했지만 본 라운드는 first-follow-up 테스트를 전혀 건드리지 않고 신규 회귀로 분리하는 쪽을 선택함 — 이 편이 chain 길이 차이를 test 이름 수준에서 명시적으로 구분할 수 있고 CONTROL_SEQ 45 잠금 상태를 그대로 유지함
