# history-card entity-card store-seeded actual-search click-reload-follow-up empty-meta no-leak bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` 에 store-seeded empty-meta continuity 어서션을 in-place 추가 (기존 source-path / response-origin 어서션은 그대로 유지). `second` (click-reload → first follow-up) 단계에서 `session.web_search_history` 의 해당 record 항목이 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}`, 빈 `claim_coverage_progress_summary`, `verification_label == "설명형 다중 출처 합의"` 를 유지하는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 신규 브라우저 시나리오 `history-card entity-card store-seeded actual-search 다시 불러오기 후 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다` 를 기존 `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(...)` 시나리오 직전에 추가. store-seeded 분기 (`claim_coverage: []`, `claim_coverage_progress_summary: ""`) 를 디스크 record 에 직접 시드하고, `renderSearchHistory` item 에도 `claim_coverage_summary` 와 `claim_coverage_progress_summary` 를 **전혀 seed 하지 않음** 으로써 client-side 에서도 `.meta` 가 생성되지 않아야 함을 강제. click-reload → 첫 follow-up 이후 `WEB` badge / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` + `ko.wikipedia.org` 기존 어서션을 그대로 유지하고, `historyCard.locator(".meta") toHaveCount(0)` 과 `historyCard not.toContainText("사실 검증")` 두 줄을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- `CONTROL_SEQ: 43` 은 세 actual-search first-follow-up 서비스 회귀를 strong-plus-missing 가족으로 묶으려다 `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` 가 **store-seeded empty-meta** 경로임을 확인하고 `implement_blocked` 로 되돌아감. `CONTROL_SEQ: 44` 는 browser-side 만 먼저 truth-sync 하며 store-seeded 서비스 테스트는 건드리지 않도록 scope 를 좁혔고, 본 `CONTROL_SEQ: 45` 는 그 남은 store-seeded empty-meta 분기를 별도 bundle 로 잠그는 범위임
- `storage/web_search_store.py:316-317` 은 `WebSearchStore.save(...)` 가 `claim_coverage` 파라미터 없이 호출되면 저장 시점에 `claim_coverage` 필드를 세팅하지 않고, `list_session_record_summaries` 는 `_summarize_claim_coverage([])` 를 거쳐 `{strong:0, weak:0, missing:0}` 을 반환함
- `app/serializers.py:280-287` 은 그 zero-count dict 를 `claim_coverage_summary` 그대로 직렬화함
- `app/static/app.js:2954-2969` 의 history card 렌더러는 investigation entity_card 에 대해 answer-mode label 을 skip 하고, `formatClaimCoverageCountSummary({strong:0,weak:0,missing:0})` 가 빈 문자열을 내므로 `detailLines` 는 비게 되어 `.meta` detail node 자체가 생성되지 않아야 함
- 본 슬라이스는 런타임 변경 없이 service 테스트 한 개에 assertion block 을 in-place 추가하고, 신규 browser 시나리오 한 개를 추가해 "store-seeded → click-reload → first follow-up" 체인의 empty-meta no-leak 계약을 명시적으로 잠그는 범위임. 이 라운드로 actual-search 가족의 browser-side `.meta` 계약이 strong-plus-missing runtime 분기 (CONTROL_SEQ 32, 42, 44) 와 store-seeded empty-meta 분기 (본 라운드) 양쪽에서 end-to-end 로 닫힘
- runtime-backed strong-plus-missing / natural reload / second follow-up / dual-probe / zero-strong / latest-update / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` store-seeded 서비스 회귀 in-place tighten**
   - `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths` 의 `second = service.handle_chat({..., user_text, load_web_search_record_id})` follow-up 이후 기존 source_paths / response_origin 어서션 다음에 assertion block 추가:
     - `followup_history = second["session"]["web_search_history"]`
     - `self.assertTrue(followup_history)`
     - `followup_entry = next((item for item in followup_history if item.get("record_id") == record_id), None)` + `assertIsNotNone`
     - `self.assertEqual(followup_entry.get("claim_coverage_summary") or {}, {"strong": 0, "weak": 0, "missing": 0})`
     - `self.assertEqual(str(followup_entry.get("claim_coverage_progress_summary") or ""), "")`
     - `self.assertEqual(followup_entry["verification_label"], "설명형 다중 출처 합의")`
   - 기존 `actions_taken`, `source_paths`, `response_origin.answer_mode`, `verification_label`, `source_roles` 어서션은 전부 그대로 유지
   - `WebSearchStore` + `AppSettings` + `WebAppService` + `_FakeWebSearchTool([])` fixture 는 재사용, 신규 helper/import/fixture 파일 없음
   - 이 회귀는 CONTROL_SEQ 43 에서 실패했던 `{strong:3, weak:0, missing:2}` 기대값을 정확한 store-seeded 런타임 결과 `{0,0,0}` 로 잠가 false-failure 를 원천 차단함
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오 추가**
   - 신규 테스트 이름: `history-card entity-card store-seeded actual-search 다시 불러오기 후 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다`
   - 기존 runtime-backed actual-search first-follow-up 시나리오 (`history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(...)`) 바로 앞에 삽입해 같은 파일 내에서 두 분기 (runtime strong-plus-missing vs store-seeded empty-meta) 가 시각적으로 인접하도록 함
   - 디스크 record 에 `claim_coverage: []` 와 `claim_coverage_progress_summary: ""` 를 명시적으로 시드 (이미 empty 인 상태를 의도적으로 유지)
   - `renderSearchHistory` item 에는 `claim_coverage_summary` 와 `claim_coverage_progress_summary` 를 **전혀 seed 하지 않음** — 이는 client-side 에서도 `formatClaimCoverageCountSummary(undefined)` 가 빈 문자열을 내고 `(undefined || "").trim()` progress 가 비어 detail `.meta` 가 생성되지 않는 경로를 그대로 exercise
   - 흐름:
     - `renderSearchHistory` → `다시 불러오기` 클릭 (show-only reload)
     - `sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id })` 첫 follow-up
   - follow-up 이후 기존 어서션:
     - `#response-origin-badge === "WEB"` + `web` class
     - `#response-answer-mode-badge` visible + `"설명 카드"`
     - `#response-origin-detail` 이 `설명형 다중 출처 합의` + `백과 기반` 포함
     - `#context-box` 가 `namu.wiki` + `ko.wikipedia.org` 포함 (source-path 연속성)
   - 신규 empty-meta no-leak 어서션:
     - `historyCard.locator(".meta") toHaveCount(0)` — store-seeded 경로에서 detail `.meta` 가 전혀 생성되지 않음
     - `historyCard not.toContainText("사실 검증")` — accidental `.meta` creation 으로 count line 이 leak 되는 경우 방어 double-guard
   - handoff 지시에 따라 `최신 확인` / `기사 교차 확인` 같은 blanket answer-mode 부정 rule 은 이 시나리오에서 사용하지 않음 — history card 의 badge row 영역에는 `설명 카드` 가 정상 등장하므로 전체 카드 blanket 부정은 false negative 가 됨. `.meta toHaveCount(0)` 이 accidental `.meta` 생성 자체를 원천 차단
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
3. runtime-backed actual-search / natural reload / second follow-up / dual-probe / zero-strong / latest-update / general 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary` → 두 테스트 모두 `ok` (store-seeded empty-meta 어서션이 `{0,0,0}` 로 잠겼고, `list_session_record_summaries` 가 빈 `claim_coverage` 입력에 대해 zero-count dict 를 내는 기존 계약도 함께 통과)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "store-seeded actual-search.*follow-up|history-card entity-card.*actual-search.*empty-meta" --reporter=line` → `1 passed (6.4s)` (신규 시나리오만 매칭되며 기존 runtime-backed 시나리오는 `-g` 정규식 범위 밖)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 store-seeded follow-up 회귀 한 개에 순수 추가 어서션만 붙였고 기존 로직 변경이 없음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 신규 시나리오 한 개만 추가함
- 기존 runtime-backed actual-search / natural reload / second follow-up / dual-probe / zero-strong / latest-update / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 서비스 회귀의 정확 dict equality (`{"strong": 0, "weak": 0, "missing": 0}`) 는 `_summarize_claim_coverage([])` 가 `{strong:0, weak:0, missing:0}` 을 내는 현재 `storage/web_search_store.py:316-317` 구현에 의존함. 해당 기본값이 None 또는 추가 key 를 포함하도록 바뀌면 equality 가 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계
- 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 false-fail 됨. 같은 가정이 이전 latest-update empty-meta 라운드들에서 이미 사용되고 있어 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 badge/summary 영역에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- store-seeded 경로에서 `renderSearchHistory` item 에 `claim_coverage_summary` 를 seed 하지 않는 것이 의도된 설계임. seed 하면 client-side 에서 `.meta` 가 생성될 수 있어 `toHaveCount(0)` 어서션이 false-fail 할 수 있음 — 이 의도는 코드 주석으로 명시해 두었음
- runtime-backed strong-plus-missing 분기(CONTROL_SEQ 32, 42, 44 완료) 와 store-seeded empty-meta 분기 (본 라운드) 가 같은 browser 파일 내에서 시각적으로 인접하게 배치되어 두 분기의 차이가 future reader 에게 명확히 구분됨. 향후 두 가족이 혼재되지 않는지 여러 라운드의 failure-first 어서션이 함께 감시함
- `CONTROL_SEQ: 43` 의 `implement_blocked` → `CONTROL_SEQ: 44` 의 browser-only scope 재조정 → `CONTROL_SEQ: 45` 의 store-seeded 분기 bundle 흐름은 `block → correct → implement` 루프가 두 단계에 걸쳐 다른 family 를 구분해 닫은 결과임. 본 closeout 은 blocked 단계를 건너뛴 것이 아니라 수정된 scope 를 구현한 결과임
- 기존 runtime-backed first-follow-up 시나리오(CONTROL_SEQ 44 완료) 는 본 라운드에서 전혀 건드리지 않았음. 두 시나리오가 같은 actual-search 가족 안에서 서로 다른 seed 규약을 따른다는 경계는 scenario 이름에 `store-seeded` vs 없음 으로 명시되어 있으며, 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
