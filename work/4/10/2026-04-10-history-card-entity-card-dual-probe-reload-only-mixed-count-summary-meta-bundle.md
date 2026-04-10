# history-card entity-card dual-probe reload-only mixed count-summary meta bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 dual-probe reload-only 네 서비스 회귀에 history-entry mixed count-summary continuity 어서션을 in-place 추가 (기존 source-path / exact-field 어서션은 그대로 유지):
  - `test_handle_chat_actual_entity_search_dual_probe_reload_preserves_active_context_source_paths` (click-reload)
  - `test_handle_chat_actual_entity_search_dual_probe_natural_reload_preserves_source_paths` (자연어 reload, source-paths 전용)
  - `test_handle_chat_dual_probe_entity_search_natural_reload_exact_fields` (자연어 reload, exact-fields)
  - `test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields` (click-reload, exact-fields)
  - 네 회귀 모두 `second` (show-only 또는 자연어 reload) 응답 단계에서 `session.web_search_history` 의 해당 record 항목이 `claim_coverage_summary == {"strong": 1, "weak": 4, "missing": 0}`, 빈 `claim_coverage_progress_summary`, `verification_label == "설명형 다중 출처 합의"` 를 유지하는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 기존 dual-probe reload-only 세 브라우저 시나리오를 실제 shipped mixed count-summary 분기로 truth-sync:
  - `history-card entity-card 다시 불러오기 후 dual-probe source path(pearlabyss.com/200, pearlabyss.com/300) + ...` (click-reload)
  - `entity-card dual-probe 자연어 reload에서 source path(pearlabyss.com/200, pearlabyss.com/300)가 context box에 유지됩니다` (자연어 reload, source-path)
  - `entity-card dual-probe 자연어 reload에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 유지됩니다` (자연어 reload, exact-fields)
  - 세 시나리오 모두 디스크 record 의 `claim_coverage` 를 1 strong + 4 weak slot 으로 전환 (stale `[]` 에서 확장), `renderSearchHistory` item 에 `claim_coverage_summary: {strong:1, weak:4, missing:0}` + 빈 progress 를 시드, reload 이후 history-card `.meta === "사실 검증 교차 확인 1 · 단일 출처 4"` + `설명 카드` / `최신 확인` / `일반 검색` 부정 어서션을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- `CONTROL_SEQ: 40` 은 dual-probe entity-card reload-only 경로가 empty-meta 라고 가정해 `{"strong":0, "weak":0, "missing":0}` 어서션을 요구했지만, 실제 runtime probe 에서 `{"strong":1, "weak":4, "missing":0}` 을 관찰하면서 `implement_blocked` 로 반환됨. CONTROL_SEQ 40 의 raw probe 결과는 이전 CONTROL_SEQ 31 의 follow-up chain 값과 정확히 일치했고, reload-only 경로도 동일한 mixed count-summary branch 임이 확인됨
- `CONTROL_SEQ: 41` 은 이 실제 shipped 값 (`strong=1, weak=4, missing=0`, 빈 progress, `설명형 다중 출처 합의` verification label) 을 기준으로 scope 를 재작성함. 기존 dual-probe reload-only 서비스/브라우저 coverage 는 source-path / exact-field / badge 만 잠갔고 실제 `.meta` 분기는 exercise 하지 못함
- `storage/web_search_store.py:316-317` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 의 렌더러 경로는 investigation entity_card 에서 answer-mode label 을 skip 하고 `formatClaimCoverageCountSummary({strong:1, weak:4})` → `"교차 확인 1 · 단일 출처 4"` 를 내므로 `.meta` 는 `사실 검증 교차 확인 1 · 단일 출처 4` 한 줄이어야 함. 이는 CONTROL_SEQ 31 의 follow-up chain 에서 이미 같은 형태로 잠긴 분기와 정확히 일치하며, 본 라운드는 reload-only 경로에 동일 계약을 명시적으로 잠그는 범위임
- dual-probe follow-up 가족(CONTROL_SEQ 31 완료), actual-search strong-plus-missing(CONTROL_SEQ 32 완료), zero-strong, noisy, general, docs, pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` 네 서비스 회귀 in-place tighten**
   - 네 테스트 모두 `second = service.handle_chat({... load_web_search_record_id / "방금 검색한 결과 다시 보여줘"})` 이후 기존 source_paths / response_origin 어서션 뒤에 assertion block 을 삽입
   - 공통 assertion pattern:
     - `reload_history = second["session"]["web_search_history"]`
     - `self.assertTrue(reload_history)`
     - click-reload 테스트는 `reload_entry = next((item for item in reload_history if item.get("record_id") == record_id), None)` 후 `assertIsNotNone`; 자연어 reload 테스트는 `reload_entry = reload_history[0]` (record_id 미추출)
     - `self.assertEqual(reload_entry.get("claim_coverage_summary") or {}, {"strong": 1, "weak": 4, "missing": 0})`
     - `self.assertEqual(str(reload_entry.get("claim_coverage_progress_summary") or ""), "")`
     - `self.assertEqual(reload_entry["verification_label"], "설명형 다중 출처 합의")`
   - 기존 `actions_taken == ["load_web_search_record"]`, `response_origin` exact-fields, `active_context.source_paths` 어서션은 전부 그대로 유지
   - `_FakeWebSearchTool` / `AppSettings` / `WebAppService` fixture 는 재사용, 신규 helper/import/fixture 파일 없음
   - 이 assertion 은 CONTROL_SEQ 40 probe 에서 관찰된 `StrEnum` 기반 dict 과도 `assertEqual` 이 `strong/weak/missing` key 값 동등성을 비교하기 때문에 호환됨 (StrEnum 은 `str` 서브클래스로 hash/eq 가 문자열과 동일)
2. **`e2e/tests/web-smoke.spec.mjs` 세 브라우저 시나리오 in-place tighten**
   - 세 시나리오 모두 디스크 record 의 `claim_coverage` 를 stale `[]` 에서 5 slot (`개발사=strong`, `장르/플랫폼/서비스/출시일=weak`) 으로 확장해 서버 `_summarize_claim_coverage` 가 재직렬화할 때 `{strong:1, weak:4, missing:0}` 을 내도록 정렬 (CONTROL_SEQ 31 의 mixed count-summary follow-up 라운드에서 사용한 동일한 5-slot 모양을 재사용)
   - `renderSearchHistory` item 에 `claim_coverage_summary: { strong: 1, weak: 4, missing: 0 }` 와 빈 `claim_coverage_progress_summary` 를 시드해 pre-click 과 post-reload 양쪽에서 `.meta` 가 동일 문자열을 내도록 정렬
   - reload (`다시 불러오기` click 또는 `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })`) 이후 기존 origin/context-box 어서션 다음에 아래 블록 추가:
     ```
     const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
     await expect(historyCardMeta).toHaveCount(1);
     await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 1 · 단일 출처 4");
     await expect(historyCardMeta).not.toContainText("설명 카드");
     await expect(historyCardMeta).not.toContainText("최신 확인");
     await expect(historyCardMeta).not.toContainText("일반 검색");
     ```
   - handoff 지시대로 empty-meta / no-`.meta` 어서션은 사용하지 않고, 실제 mixed count-summary 분기의 exact text 를 잠금. count line 자체가 ` · ` 구분자를 합법적으로 포함하므로 `not.toContainText("·")` blanket rule 은 사용하지 않음
   - handoff 지시대로 `설명 카드` / `최신 확인` / `일반 검색` 에 대한 부정 어서션은 `.meta` 에만 한정함 (history card 의 `.answer-mode-badge` 나 다른 뱃지 영역에는 정상적으로 해당 문자열이 등장하므로 전체 카드 blanket 부정은 false negative)
   - 기존 `WEB` badge, `설명 카드` answer-mode badge, origin detail verification-label & source-roles, `#context-box` source-path 어서션은 전부 그대로 유지
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - dual-probe follow-up 시나리오(CONTROL_SEQ 31 완료), actual-search / zero-strong / noisy / general / latest-update 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_dual_probe_reload_preserves_active_context_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_dual_probe_natural_reload_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_search_natural_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields` → 네 테스트 모두 `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe source path|entity-card dual-probe 자연어 reload에서 source path|entity-card dual-probe 자연어 reload에서 WEB badge" --reporter=line` → `3 passed (16.7s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 네 dual-probe reload-only 회귀에 순수 추가 어서션만 붙였고 기존 로직 변경이 없음. handoff 도 focused 네 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 기존 세 시나리오만 in-place tighten 함
- 기존 dual-probe follow-up / actual-search / zero-strong / noisy / latest-update 계열 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 네 서비스 회귀의 `{"strong": 1, "weak": 4, "missing": 0}` 정확 dict equality 는 실제 런타임 분포에 의존함. `_FakeWebSearchTool` 의 기본 응답 혹은 dual-probe `_build_entity_claim_records` / `_select_entity_fact_card_claims` 가 바뀌면 이 값이 drift 할 수 있고 네 회귀가 함께 실패해 원인을 빠르게 가리킴 — failure-first 설계이며, 이전 CONTROL_SEQ 31 라운드의 동일 분포와 상호 일관적
- 세 브라우저 시나리오의 `.meta` 정확 텍스트는 디스크 record 에 시드한 `claim_coverage` 의 1 strong + 4 weak 비율과 `formatClaimCoverageCountSummary` 의 `"교차 확인 N · 단일 출처 N"` 포맷에 의존함. 포맷이 바뀌면 스모크가 먼저 깨지며, 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- handoff 지시에 따라 empty-meta / no-`.meta` 어서션은 사용하지 않고, 대신 `toHaveCount(1)` + `toHaveText` exact 로 mixed count-summary 분기를 잠금. CONTROL_SEQ 40 에서 empty-meta 로 오인되었던 분기 구분이 이 라운드로 정확히 재정렬됨
- `설명 카드` / `최신 확인` / `일반 검색` 에 대한 blanket `not.toContainText` 는 `.meta` element 에만 한정 적용되므로 history card 전체의 badge row 에 있는 answer-mode 텍스트와는 충돌하지 않음 (false positive 없음)
- CONTROL_SEQ 31 의 follow-up chain 과 본 라운드의 reload-only 경로가 동일한 mixed count-summary 분기를 공유한다는 사실이 두 라운드에 걸쳐 재확인되었음. 향후 두 가족이 다른 분포로 갈라지면 양쪽 회귀/시나리오가 함께 drift 를 감지함
- 시나리오/회귀를 in-place tighten 했으므로 이름은 그대로 유지되었지만 실제로는 mixed count-summary `.meta` 어서션까지 확장되었음. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
- CONTROL_SEQ 40 의 `implement_blocked` 사이클을 통해 handoff 의 empty-meta 전제가 정정되고 본 라운드 (CONTROL_SEQ 41) 에서 실제 shipped contract 가 잠겼음. 이 `block → correct → implement` 루프는 truthful pipeline 의 정상적 동작 이며, 본 closeout 은 blocked 단계를 건너뛴 것이 아니라 수정된 scope 를 구현한 결과임
