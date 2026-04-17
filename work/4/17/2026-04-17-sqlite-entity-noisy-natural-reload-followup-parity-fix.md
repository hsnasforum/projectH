# 2026-04-17 sqlite-entity-noisy-natural-reload-followup-parity-fix

## 변경 파일

- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill

- work-log-closeout

## 변경 이유

seq 247에서 `sqlite-browser-history-card-natural-reload-chain-parity` 24개 bundle을 돌렸을 때 22건은 sqlite에서 그대로 통과했지만 붉은사막 noisy single-source 자연어 reload follow-up / 두 번째 follow-up 2건(web-smoke.spec.mjs:10712, 10784)만 sqlite에서 `[모의 문서 응답]` document-mode mock text를 돌려주며 실패했고 JSON-default에서는 그대로 통과했습니다. 사용자 지시에 따라 seq 247은 해당 parity 결함을 `implement_blocked / sqlite_parity_drift` sentinel로 넘기고 정지했습니다. seq 248은 이 blocker 하나만 좁게 잡아서, seq 247이 금지했던 product-level 조사(natural-reload record load path, `_reuse_web_search_record`, `_respond_with_active_context` 관계)를 허용하고 실제 drift를 source에서 고치도록 지정했습니다. 따라서 이번 라운드는 sqlite-only 복원 fix + 좁은 sqlite-backed service regression 2건 추가 + 2개 exact sqlite Playwright scenario 재실행만 수행했고, 24개 bundle / 79→103 docs 확장 / 다른 family / 다른 backend는 모두 scope 밖으로 유지했습니다.

조사 결과 실제 drift의 뿌리는 storage backend가 아니라 `_reuse_web_search_record` 자체에 있었습니다. `load_web_search_record_id`가 실려 있고 `user_text`가 "다시 보여 / 불러와" 계열이 아닌 follow-up 질문(`이 검색 결과 요약해줘`, `더 자세히 알려줘`)일 때 `show_only` 분기가 False가 되어 `_respond_with_active_context` 로 떨어지는데, 이 경로가 웹 검색 entity-card의 저장된 summary(`웹 검색 요약: …\n\n확인된 사실 [교차 확인]: …`)를 드롭하고 mock `answer_with_context`가 생성한 `[모의 문서 응답] …` document-mode 텍스트만 돌려줬습니다. JSON-default browser test가 "통과"한 이유는 feature가 맞아서가 아니라 `sendRequest`의 `state.isBusy` early-return 때문에 step 2 / step 3 요청이 실제로는 서버에 전혀 발사되지 않았고 (server-side debug log로 확인: JSON은 step 1 한 번만 찍히고, sqlite는 step 1→2→3 모두 찍힙니다) step 1이 세팅해 놓은 show-only reload 텍스트가 DOM에 남아 있어서였습니다. sqlite backend는 step 1이 빨리 끝나 state.isBusy가 풀리면서 step 2·3이 실제 요청을 쏘고 `[모의 문서 응답]` 으로 덮어쓰기 때문에 "확인된 사실 [교차 확인]:" positive assertion이 깨졌습니다. JSON은 timing race로 우연히 통과하던 셈이고, shipped contract인 "web-search entity-card / latest-update 가 natural-reload follow-up 체인에서 유지된다"를 실제로 만족하려면 product side를 고치는 편이 맞습니다.

## 핵심 변경

1. **`core/agent_loop.py::_reuse_web_search_record` 팔로업 경로 복원** (seq 247 blocker 직접 수정):
   - show_only가 아닌 follow-up 분기(`_respond_with_active_context` 이후)에서, `active_context.kind == "web_search"`이고 `stored_answer_mode ∈ {entity_card, latest_update}`이며 `summary_text`가 비어 있지 않을 때 stored normalized summary를 응답 텍스트 맨 앞에 prepend 합니다. 이미 포함되어 있으면 중복하지 않습니다. stored summary는 이미 noisy single-source claim(`출시일`/`2025`/`blog.example.com`)을 배제한 cross-verified 요약이라 noisy exclusion + provenance 대조 계약도 그대로 유지됩니다. storage shape, serializer semantics, answer-mode composition, claim-coverage serialization, source-role policy는 손대지 않았고 show-only 분기는 그대로 둬서 `show_only=True` 경로(click reload, 자연어 reload step 본체)는 영향 없습니다.

2. **`tests/test_web_app.py` sqlite-backed service regression 2건 추가**:
   - `test_handle_chat_sqlite_backend_entity_card_noisy_single_source_natural_reload_follow_up_keeps_stored_summary`: `AppSettings(storage_backend="sqlite", sqlite_db_path=…)` 로 sqlite backend 열어 noisy entity-card record를 `WebSearchStore.save` 로 미리 넣고 click reload → natural-reload(`방금 검색한 결과 다시 보여줘`) → follow-up(`이 검색 결과 요약해줘` + `load_web_search_record_id`) 순으로 태워서 `response_origin.badge == "WEB"`, `answer_mode == "entity_card"`, `verification_label == "설명형 다중 출처 합의"`, `source_roles == ["백과 기반"]`, `response.text ⊇ "확인된 사실 [교차 확인]:"`, `response.text ⊅ "출시일"/"2025"/"blog.example.com"`, `active_context.source_paths ⊇ namu.wiki / ko.wikipedia.org / blog.example.com` 을 모두 잠급니다.
   - `test_handle_chat_sqlite_backend_entity_card_noisy_single_source_natural_reload_second_follow_up_keeps_stored_summary`: 위 흐름에 `더 자세히 알려줘` follow-up 한 턴을 더 얹어 Playwright second-follow-up 시나리오(`web-smoke.spec.mjs:10784`)에 대응합니다. 두 테스트 모두 `storage_backend="sqlite"` 경로이기 때문에 향후 동일 drift가 다시 생기면 sqlite 쪽에서 즉시 감지됩니다.

3. **Scope 준수**: `storage/sqlite_store.py`, `storage/session_store.py`, `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, controller/runtime 파일은 이번 라운드에 건드리지 않았습니다. 24-scenario bundle / 79→103 docs 확장도 handoff scope 밖이므로 열지 않았습니다.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_sqlite_backend_entity_card_noisy_single_source_natural_reload_follow_up_keeps_stored_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_sqlite_backend_entity_card_noisy_single_source_natural_reload_second_follow_up_keeps_stored_summary  # 2/2 ok (0.229s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (4.1s)
git diff --check -- core/agent_loop.py tests/test_web_app.py  # clean
```

회귀 확인용 보조 실행(동일 family 기존 JSON-default service regression 6건, reload family 83건, noisy family 60건, test_smoke reload 5건):

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_follow_up_preserves_claim_coverage_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_second_follow_up_preserves_claim_coverage_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up  # 6/6 ok
python3 -m unittest -v tests.test_web_app -k "reload"  # 83/83 ok (11.807s)
python3 -m unittest -v tests.test_web_app -k "noisy"   # 60/60 ok (1.854s)
python3 -m unittest -v tests.test_smoke -k "reload"    # 5/5 ok
```

- 전체 `make e2e-test`, JSON-default Playwright 전체 suite, 나머지 22개 natural-reload chain sqlite scenario, sqlite browser full suite, `python3 -m unittest -v tests.test_web_app` 전 영역은 이번 scope가 좁게 정의된 parity 결함 2건에 한정돼 있어 실행하지 않았습니다. 이번 slice의 product diff는 `_reuse_web_search_record` 팔로업 분기에 stored summary prepend 조건 하나 추가에 그치며, 관련 family의 JSON-default + noisy 기존 회귀가 모두 유지되는 것을 확인했기 때문에 broad suite는 이번 범위 대비 과한 검증이었습니다.

## 남은 리스크

- 이번 fix는 현재 shipped contract(natural-reload / click-reload follow-up 시 저장된 cross-verified summary 유지)를 product code로도 실제 만족시키는 방향이지만, JSON-default browser test의 "timing race"로 우연히 통과하던 behavior도 바뀌지 않은 채 남아 있습니다(step 2·3가 state.isBusy로 early-return되는 것). 본격적인 browser-level race 정리는 이번 slice 밖이고, handoff가 scope 한정을 명시했기 때문에 변경하지 않았습니다. 다음 brower-contract 라운드에서 `sendRequest` early-return semantics + test 시나리오 단순화를 함께 손보는 편이 맞습니다.
- 22개 natural-reload chain sqlite scenario는 이번 라운드에 재실행하지 않았습니다. 이 fix는 `_reuse_web_search_record` follow-up 경로만 prepend 하나를 추가한 것이라 다른 22개는 영향받지 않을 가능성이 높지만, 다음 라운드에서 docs-sync 또는 bundle 재실행을 진행할 때는 24개 전체를 한번 더 확인하는 편이 안전합니다.
- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책은 이전 라운드와 동일합니다. sqlite/JSON Playwright config 동시 실행은 여전히 같은 `data/web-search/` 경로를 공유하므로 순차 실행 한정으로 안전합니다.
- 이번 scope에 따라 `README.md` / `docs/ACCEPTANCE_CRITERIA.md` / `docs/MILESTONES.md` / `docs/TASK_BACKLOG.md` sqlite browser gate inventory는 건드리지 않았고, seq 247에서 이미 uncommitted 상태로 올라와 있던 70~79번 자연어 reload reload-only 행도 그대로 유지했습니다. 79→103 docs 확장은 24-scenario bundle이 한 라운드 안에 truthfully 닫혔을 때 별도 라운드에서 반영하는 편이 맞습니다.
