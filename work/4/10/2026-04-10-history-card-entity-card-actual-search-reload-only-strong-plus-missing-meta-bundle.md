# history-card entity-card actual-search reload-only strong-plus-missing meta bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 actual-search entity-card reload-only 세 서비스 회귀에 history-entry strong-plus-missing count-summary continuity 어서션을 in-place 추가 (기존 source-path / exact-field 어서션은 그대로 유지):
  - `test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths` (click-reload, source-paths)
  - `test_handle_chat_actual_entity_search_natural_reload_preserves_source_paths` (자연어 reload, source-paths)
  - `test_handle_chat_actual_entity_search_natural_reload_exact_fields` (자연어 reload, exact-fields)
  - 세 회귀 모두 `second` (show-only 또는 자연어 reload) 응답 단계에서 `session.web_search_history` 의 해당 record 항목이 `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}`, 빈 `claim_coverage_progress_summary`, `verification_label == "설명형 다중 출처 합의"` 를 유지하는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 기존 actual-search entity-card reload-only 세 브라우저 시나리오를 실제 shipped strong-plus-missing 분기로 truth-sync:
  - `history-card entity-card 다시 불러오기 후 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, ...` (click-reload)
  - `entity-card 붉은사막 검색 결과 자연어 reload에서 WEB badge, 설명 카드, noisy single-source claim(출시일/2025/blog.example.com) 미노출, ..., blog.example.com provenance 유지됩니다` (자연어 reload, noisy exclusion variant)
  - `entity-card 붉은사막 자연어 reload에서 source path(namu.wiki, ko.wikipedia.org, blog.example.com provenance)가 context box에 유지됩니다` (자연어 reload, source-path variant)
  - 세 시나리오 모두 디스크 record 의 `claim_coverage` 를 stale 단일 `{strong:1}` slot + `"교차 확인 1건."` progress 에서 3 strong + 2 missing slot + 빈 progress 로 전환, `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` 와 빈 progress 를 시드, reload 이후 history-card `.meta === "사실 검증 교차 확인 3 · 미확인 2"` + `설명 카드` / `최신 확인` / `일반 검색` 부정 어서션을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-dual-probe-reload-only-mixed-count-summary-meta-bundle.md`) 는 dual-probe reload-only mixed count-summary 가족을 `{strong:1, weak:4, missing:0}` 분기로 잠갔음. 본 라운드는 **actual-search (non-dual-probe)** reload-only 가족의 **strong-plus-missing** 분기 (`{strong:3, weak:0, missing:2}`) 를 별도로 잠그는 범위임
- `storage/web_search_store.py:316-317` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 의 렌더러 경로는 investigation entity_card 에서 answer-mode label 을 skip 하고 `formatClaimCoverageCountSummary({strong:3, missing:2})` → `"교차 확인 3 · 미확인 2"` 를 내므로 `.meta` 는 `사실 검증 교차 확인 3 · 미확인 2` 한 줄이어야 함. 이는 이전 CONTROL_SEQ 32 (actual-search follow-up chain) 에서 같은 분기로 이미 잠긴 값과 정확히 일치하며, 본 라운드는 reload-only 경로에 동일 계약을 명시적으로 잠그는 범위임
- 기존 서비스 회귀 세 개(`:8906`, `:9183`, `:9242`) 는 source-path / exact-field 만 잠갔고, 기존 브라우저 시나리오 세 개(`:2539`, `:5773` → 현재 `:5782`, `:5845` → 현재 `:5853`) 는 source path / badge / origin-detail 만 잠가 `.meta` 분기를 직접 exercise 하지 못했으며, 시드된 `claim_coverage` 는 stale 단일 `{strong:1}` slot 으로 runtime 분포와 드리프트 상태였음
- 이 슬라이스는 런타임 변경 없이 세 서비스 회귀와 세 browser 시나리오에 strong-plus-missing count-summary assertion block 을 in-place 추가하고, 스토어 시드를 runtime 과 정렬해 reload-only 경로의 `.meta` 계약을 잠그는 범위임. actual-search follow-up chain (CONTROL_SEQ 32 완료), dual-probe (CONTROL_SEQ 31 / CONTROL_SEQ 41 완료), zero-strong, latest-update, noisy latest-update, general, docs, pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` 세 서비스 회귀 in-place tighten**
   - 세 테스트 모두 `second = service.handle_chat({... load_web_search_record_id / "방금 검색한 결과 다시 보여줘"})` 이후 기존 source_paths / response_origin 어서션 뒤에 assertion block 을 삽입
   - 공통 assertion pattern (CONTROL_SEQ 32 actual-search follow-up + CONTROL_SEQ 41 dual-probe reload-only 라운드와 동일한 failure-first 정규화):
     - `reload_history = second["session"]["web_search_history"]`
     - `self.assertTrue(reload_history)`
     - click-reload 테스트는 `reload_entry = next((item for item in reload_history if item.get("record_id") == record_id), None)` + `assertIsNotNone`; 자연어 reload 테스트는 `reload_entry = reload_history[0]`
     - `self.assertEqual(reload_entry.get("claim_coverage_summary") or {}, {"strong": 3, "weak": 0, "missing": 2})`
     - `self.assertEqual(str(reload_entry.get("claim_coverage_progress_summary") or ""), "")`
     - `self.assertEqual(reload_entry["verification_label"], "설명형 다중 출처 합의")`
   - 기존 `actions_taken == ["load_web_search_record"]`, `response_origin` exact-fields, `active_context.source_paths` 어서션은 전부 그대로 유지
   - `_FakeWebSearchTool` / `AppSettings` / `WebAppService` fixture 는 재사용, 신규 helper/import/fixture 파일 없음
2. **`e2e/tests/web-smoke.spec.mjs` 세 브라우저 시나리오 in-place tighten**
   - 세 시나리오 모두 디스크 record 의 `claim_coverage` 를 stale `[{장르 strong}]` + `"교차 확인 1건."` progress 에서 5 slot 으로 확장:
     - strong: `장르`, `개발사`, `플랫폼` (3개)
     - missing: `엔진`, `난이도` (2개)
   - slot 이름은 noisy 가족 scenarios (5782) 의 `출시일` / `2025` / `brunch` 등 negative assertion 키워드와 충돌하지 않도록 의도적으로 선택 (`엔진`/`난이도`)
   - `claim_coverage_progress_summary` 를 stale `"교차 확인 1건."` → `""` 로 전환 (실제 runtime 과 일치)
   - `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` 와 빈 progress 를 시드해 pre-click 과 post-reload 양쪽에서 `.meta` 가 동일 문자열을 내도록 정렬
   - reload (`다시 불러오기` click 또는 `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })`) 이후 기존 origin/context-box 어서션 다음에 아래 블록 추가:
     ```
     const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
     await expect(historyCardMeta).toHaveCount(1);
     await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
     await expect(historyCardMeta).not.toContainText("설명 카드");
     await expect(historyCardMeta).not.toContainText("최신 확인");
     await expect(historyCardMeta).not.toContainText("일반 검색");
     ```
   - handoff 지시대로 `설명 카드` / `최신 확인` / `일반 검색` 부정 어서션은 `.meta` element 에만 한정 적용함 (history card 의 answer-mode-badge 뱃지 텍스트와 충돌하지 않음). count line 자체가 ` · ` 구분자를 합법적으로 포함하므로 `not.toContainText("·")` blanket rule 은 사용하지 않음
   - 기존 `WEB` badge, `설명 카드` answer-mode badge, origin detail verification-label & source-roles, `#context-box` source-path, noisy 시나리오의 `출시일`/`2025`/`brunch`/`blog.example.com` 부정 어서션, `blog.example.com` provenance 긍정 어서션은 전부 그대로 유지
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - actual-search follow-up / dual-probe / zero-strong / latest-update / noisy latest-update / general 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_exact_fields` → 세 테스트 모두 `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 actual-search source path|entity-card 붉은사막 검색 결과 자연어 reload에서 WEB badge|entity-card 붉은사막 자연어 reload에서 source path.*blog.example.com provenance" --reporter=line` → `3 passed (17.2s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 세 actual-search reload-only 회귀에 순수 추가 어서션만 붙였고 기존 로직 변경이 없음. handoff 도 focused 세 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 기존 세 시나리오만 in-place tighten 함
- 기존 actual-search follow-up / dual-probe / zero-strong / latest-update / noisy 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 세 서비스 회귀의 `{"strong": 3, "weak": 0, "missing": 2}` 정확 dict equality 는 실제 런타임 분포에 의존함. `_FakeWebSearchTool` 기본 응답 또는 `_build_entity_claim_records` / `_select_entity_fact_card_claims` 분류가 바뀌면 이 값이 drift 할 수 있고 세 회귀가 함께 실패해 원인을 빠르게 가리킴 — failure-first 설계이며, 이전 CONTROL_SEQ 32 (actual-search follow-up) 의 동일 분포와 상호 일관적
- 세 브라우저 시나리오의 `.meta` 정확 텍스트는 시드된 `claim_coverage` 의 3 strong + 2 missing 비율과 `formatClaimCoverageCountSummary` 포맷에 의존함. 포맷이 바뀌면 스모크가 먼저 깨짐
- noisy actual-search 시나리오(`:5782`, `:5853`) 에서 slot 이름은 `엔진`/`난이도` 로 의도적으로 선택해 기존 noisy 부정 assertion (`출시일`/`2025`/`brunch`/`blog.example.com`) 과 충돌하지 않도록 함. 향후 noisy 키워드 목록이 확장되면 slot 이름도 함께 재검토해야 함
- handoff 지시에 따라 `설명 카드` / `최신 확인` / `일반 검색` 부정 어서션은 `.meta` element 에만 한정함 (history card 의 `.answer-mode-badge` 에는 `설명 카드` 가 정상적으로 등장하므로 전체 카드 blanket 부정은 false negative 가 됨)
- CONTROL_SEQ 32 의 follow-up chain, CONTROL_SEQ 41 의 dual-probe reload-only, 본 라운드의 actual-search reload-only 가 각각 다른 mixed/strong-plus-missing 분포로 잠겨 서로 구분됨:
  - dual-probe: `{strong:1, weak:4, missing:0}` → `.meta = "사실 검증 교차 확인 1 · 단일 출처 4"`
  - actual-search: `{strong:3, weak:0, missing:2}` → `.meta = "사실 검증 교차 확인 3 · 미확인 2"`
  - 이 두 가족이 장래에 혼재되지 않는지 여러 라운드에 걸친 failure-first 설계로 감시됨
- 시나리오/회귀를 in-place tighten 했으므로 이름은 그대로 유지되었지만 실제로는 strong-plus-missing `.meta` 어서션까지 확장되었음. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
