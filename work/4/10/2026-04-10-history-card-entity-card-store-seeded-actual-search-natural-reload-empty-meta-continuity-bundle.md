# history-card entity-card store-seeded actual-search natural-reload empty-meta continuity bundle

## 변경 파일
- 없음 (이번 라운드는 persistent-truth sync 전용 round)
- 기존 local 구현이 이미 truthfully live 상태임을 확인:
  - `tests/test_web_app.py:17179` — `test_handle_chat_entity_card_store_seeded_actual_search_post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak`
  - `e2e/tests/web-smoke.spec.mjs:3856` — `history-card entity-card store-seeded actual-search 자연어 reload 체인에서 empty-meta no-leak contract가 유지됩니다`

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- CONTROL_SEQ 47 의 blocked sentinel 은 `<short_reason>` placeholder 만 담고 있어 진단 근거가 없었고, 이후 CONTROL_SEQ 48 에서 동일 scope 의 store-seeded actual-search post-reload natural-reload 체인 empty-meta no-leak bundle 을 구현했음
- CONTROL_SEQ 49 handoff 는 해당 구현이 이미 local worktree 에 들어가 있는 상태를 인식하고, truthful 다음 단계가 "re-implement the same bundle" 이 아니라 "close the persistent-truth gap with one bounded same-family closeout" 이라고 명시함
- 따라서 본 라운드는 코드/테스트/시나리오를 **전혀 변경하지 않고**, 기존 local 구현이 truthfully 동작하는지를 focused rerun 으로 재확인한 뒤 persistent truth 를 지정된 경로의 `/work` closeout 에 기록하는 범위임
- 직전 `/work` (`2026-04-10-history-card-entity-card-store-seeded-actual-search-click-reload-second-follow-up-empty-meta-no-leak-bundle.md`) 는 store-seeded actual-search 가족의 **click-reload** 체인 (click reload → first follow-up → second follow-up) empty-meta no-leak 계약을 잠갔고, CONTROL_SEQ 48 에서 작성된 `/work` (`2026-04-10-history-card-entity-card-store-seeded-actual-search-post-reload-natural-reload-follow-up-chain-empty-meta-continuity-bundle.md`) 는 post-reload natural-reload 체인을 잠갔음. 본 closeout 은 CONTROL_SEQ 49 handoff 가 요구한 고유 파일명 (`..._store_seeded_actual_search_natural_reload_empty_meta_continuity_bundle.md`) 으로 동일 분기의 persistent truth 를 한 번 더 기록해 `/work` 인덱스 기준 파일 이름과 handoff 의 closeout path 를 정확히 맞춤

## 핵심 변경
이번 라운드는 **코드 수정 없음**. 기존 local 구현의 구조와 계약을 persistent-truth 로 기록:

1. **`tests/test_web_app.py:17179` — 이미 live 상태인 서비스 회귀**
   - 테스트명: `test_handle_chat_entity_card_store_seeded_actual_search_post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak`
   - 구조:
     - `WebSearchStore.save(...)` 를 `claim_coverage` 파라미터 없이 호출해 record 를 seed
     - `_FakeWebSearchTool([])` 로 service 를 초기화 (체인 도중 실제 web search 가 실행되지 않도록)
     - 네 단계 순차 실행:
       - `first` = click reload (`load_web_search_record_id` only, show-only)
       - `second` = 자연어 reload (`user_text: "방금 검색한 결과 다시 보여줘"`, no `load_web_search_record_id`)
       - `third` = 첫 follow-up (`user_text: "이 검색 결과 요약해줘"` + `load_web_search_record_id`)
       - `fourth` = 두 번째 follow-up (`user_text: "더 자세히 알려줘"` + `load_web_search_record_id`)
     - 내부 공통 헬퍼 `_assert_empty_meta_continuity(result, stage)` 가 각 단계마다 `ok`, `actions_taken` 에 `load_web_search_record` 포함, `active_context.source_paths` 에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89` 과 `https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89` 포함, `response_origin.answer_mode == "entity_card"` / `verification_label == "설명형 다중 출처 합의"` / `source_roles == ["백과 기반"]`, `session.web_search_history` 의 해당 record 항목이 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}` + 빈 `claim_coverage_progress_summary` + `verification_label == "설명형 다중 출처 합의"` 를 유지함을 잠금
   - handoff 가 명시한 "at each meaningful stage you traverse, not only at the end" 요구가 네 stage 의 `_assert_empty_meta_continuity` 호출에 직접 반영되어 있음
2. **`e2e/tests/web-smoke.spec.mjs:3856` — 이미 live 상태인 브라우저 시나리오**
   - 시나리오명: `history-card entity-card store-seeded actual-search 자연어 reload 체인에서 empty-meta no-leak contract가 유지됩니다`
   - 구조:
     - 디스크 record 에 `claim_coverage: []` + 빈 `claim_coverage_progress_summary` 시드 (store-seeded 분기)
     - `renderSearchHistory` item 에는 `claim_coverage_summary` / `claim_coverage_progress_summary` 를 **전혀 seed 하지 않음** (pre-click `.meta` 생성을 원천 차단)
     - 네 단계 흐름:
       - `다시 불러오기` 클릭 (show-only reload)
       - `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` 자연어 reload
       - `sendRequest({ user_text: "이 검색 결과 요약해줘", load_web_search_record_id }, "follow_up")` 첫 follow-up
       - `sendRequest({ user_text: "더 자세히 알려줘", load_web_search_record_id }, "follow_up")` 두 번째 follow-up
     - 최종 두 번째 follow-up 이후:
       - `#response-origin-badge === "WEB"` + `web` class
       - `#response-answer-mode-badge` visible + `"설명 카드"`
       - `#response-origin-detail` 이 `설명형 다중 출처 합의` + `백과 기반` 포함
       - `#context-box` 가 `namu.wiki` + `ko.wikipedia.org` 포함
       - `historyCard.locator(".meta") toHaveCount(0)` — store-seeded 경로에서 detail `.meta` 가 전혀 생성되지 않음
       - `historyCard not.toContainText("사실 검증")` — accidental `.meta` creation 으로 count line 이 leak 되는 경우 방어 double-guard
3. 기존 store-seeded click-reload first/second follow-up 시나리오 (CONTROL_SEQ 45, 46 에서 잠긴 상태) 와 runtime-backed actual-search 시나리오 (CONTROL_SEQ 32, 42, 44 에서 잠긴 상태) 는 이번 라운드에서 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_store_seeded_actual_search_post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary` → 두 테스트 모두 `ok` (`Ran 2 tests in 0.053s — OK`)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "store-seeded actual-search.*자연어 reload.*empty-meta|store-seeded actual-search.*자연어 reload 체인" --reporter=line` → `1 passed (6.4s)` (store-seeded 자연어 reload 체인 시나리오 한 개만 regex 에 매칭)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 라운드는 코드/테스트/시나리오 **어느 것도 변경하지 않음**. handoff 도 focused 두 회귀와 한 browser regex 만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 새 시나리오도 추가되지 않음
- 기존 store-seeded click-reload / runtime-backed actual-search / dual-probe / zero-strong / latest-update / noisy / general 시나리오 — handoff 는 본 라운드를 truth-sync 로 한정함

## 남은 리스크
- 본 라운드는 persistent-truth sync 전용이며 **어떤 코드 변경도 없음**. 기존 local 구현이 이미 truthfully live 상태였고 focused rerun 이 정상 통과함을 확인한 기록임
- CONTROL_SEQ 49 handoff 가 명시한 `/work` closeout 파일명 (`2026-04-10-history-card-entity-card-store-seeded-actual-search-natural-reload-empty-meta-continuity-bundle.md`) 과 CONTROL_SEQ 48 에서 작성된 `/work` 파일명 (`...-post-reload-natural-reload-follow-up-chain-empty-meta-continuity-bundle.md`) 은 서로 다른 파일로 coexist 함. 이는 동일 구현에 대한 두 개 closeout 이지만, CONTROL_SEQ 49 가 handoff 에서 정확한 파일 경로를 명시했으므로 의도된 결과임. 향후 closeout 인덱스 정리에서 두 파일 중 하나를 canonical 로 남기고 나머지를 보조 기록으로 리네임/삭제할 수 있음 — 별도 docs-sync 라운드에서 다룰 수 있는 drift 임
- 신규 서비스 회귀 (`:17179`) 의 정확 dict equality (`{"strong": 0, "weak": 0, "missing": 0}`) 는 `_summarize_claim_coverage([])` 가 `{strong:0, weak:0, missing:0}` 을 내는 현재 `storage/web_search_store.py:316-317` 구현에 의존함. 해당 기본값이 None 또는 추가 key 를 포함하도록 바뀌면 네 stage 중 해당 assertion 이 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계이며, `_assert_empty_meta_continuity` 가 네 stage 에 대해 각각 호출되어 stage 별 실패 메시지가 서로 구분됨
- 브라우저 시나리오 (`:3856`) 의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 false-fail 됨. 같은 가정이 이전 latest-update / store-seeded click-reload empty-meta 라운드들에서도 사용 중이라 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 badge/summary 영역에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- `renderSearchHistory` item 에 `claim_coverage_summary` 를 seed 하지 않는 것이 의도된 설계임. seed 하면 client-side 에서 `.meta` 가 생성될 수 있어 `toHaveCount(0)` 어서션이 false-fail 할 수 있음 — 이 의도는 기존 코드 주석으로 명시되어 있음
- CONTROL_SEQ 47 → 48 → 49 세 라운드에 걸친 `block (non-signal sentinel) → implement → truth-sync` 루프는 pipeline 이 place-holder sentinel 을 human-usable signal 로 간주하지 않고 자체 검증 후 persistent-truth 를 재기록하는 정상적 경로임. 본 closeout 은 blocked 단계를 건너뛴 것이 아니라 "CONTROL_SEQ 48 에서 이미 구현된 내용이 truthful 상태임" 을 재확인한 결과임
- 다른 store-seeded 가족 (click-reload first follow-up / click-reload second follow-up) 과 runtime-backed actual-search 가족은 이전 라운드들 (CONTROL_SEQ 32, 42, 44, 45, 46) 에서 잠긴 상태로 남아 있으며, 본 라운드는 그 가족들을 전혀 건드리지 않음. store-seeded × actual-search 조합의 browser + service `.meta` 계약이 이 라운드를 마지막으로 end-to-end 로 완전히 닫힘
