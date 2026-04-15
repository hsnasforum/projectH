# history-card simple entity-card stored-record kind/model exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-simple-entity-card-click-reload-kind-model-exact-service-bundle.md`)는 reload 시점의 `reload_origin["kind"] == "assistant"` / `self.assertIsNone(reload_origin["model"])` 두 줄 assertion을 추가했지만, 같은 closeout의 사용 skill 항목과 남은 리스크 서술은 `superpowers:using-superpowers` 및 browser seeded fixture가 이미 `kind` / `model`을 노출하고 있는 것처럼 overclaim했습니다. 최신 `/verify` 기록과 `e2e/tests/web-smoke.spec.mjs:1404`의 simple seeded record는 그 두 필드를 실제로는 여전히 노출하지 않습니다.

이 라운드는 그 overclaim을 바로잡는 동시에, 같은 simple entity-card click-reload family에서 실제로 남은 current-risk를 제거합니다. shipped click-reload 경로는 persisted web-search record에 의존하므로, reload 결과뿐 아니라 `service.web_search_store.get_session_record(...)`로 읽은 저장 레코드 자체가 `response_origin["kind"] == "assistant"` / `response_origin["model"] is None` 계약을 만족하는지 직접 고정하는 편이 browser fixture sync보다 current-risk reduction에 직접적입니다. `app/static/app.js`는 `model`이 truthy일 때만 노출하고 `kind == "approval"`일 때만 별도 detail을 붙이므로, 현재 `assistant` + `None` 쌍에서는 browser-first 라운드가 대부분 테스트 데이터 동기화에 그쳐 persistence 계약을 실제로 보호하지 못합니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 service 테스트에서 첫 `handle_chat` 호출로 `record_id`가 확보된 직후, persisted record를 `service.web_search_store.get_session_record(<session_id>, record_id)`로 읽어 exact-field assertion 세트를 추가했습니다.

- `test_handle_chat_load_web_search_record_id_entity_card_exact_fields`  
  → session_id `"reload-by-id-entity-session"`
- `test_handle_chat_entity_card_reload_preserves_stored_response_origin`  
  → session_id `"entity-origin-reload-session"`
- `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin`  
  → session_id `"entity-followup-origin-session"`

각 테스트에 추가된 assertion 블록:

```
stored_record = service.web_search_store.get_session_record(
    "<session_id>", record_id
)
self.assertIsNotNone(stored_record)
stored_origin = stored_record["response_origin"]
self.assertEqual(stored_origin["kind"], "assistant")
self.assertIsNone(stored_origin["model"])
```

이미 landed되어 있던 reload_origin 쪽 `kind` / `model` assertion은 그대로 유지했습니다. 브라우저 테스트, seeded browser fixture, docs, pipeline 파일, dual-probe / zero-strong / actual-search / latest-update family는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.076s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- browser-visible 계약은 이번 슬라이스에서 건드리지 않았으므로 `make e2e-test`는 과합니다. persistence 계약의 service-only 대조이므로 targeted three-test bundle로 충분합니다.

## 남은 리스크

- `e2e/tests/web-smoke.spec.mjs:1404`의 simple seeded browser record는 여전히 `kind` / `model` 필드를 노출하지 않습니다. browser DOM 레벨의 `kind` / `model` surfacing은 이번 슬라이스 범위 밖이며, 필요하다면 별도 seeded-record sync 슬라이스에서 닫아야 합니다.
- 같은 `response_origin["kind"]` / `response_origin["model"]` exact-field 대조를 다른 response-origin family (dual-probe / zero-strong / actual-search / latest-update) persisted record에 대해서도 할 필요가 있는지는 이 라운드에서 확인하지 않았습니다.
- 직전 `/work`의 사용 skill 항목은 `superpowers:using-superpowers`를 사용했다고 적었지만, `/verify`는 그것이 available skill 표면에 없다는 점을 지적했습니다. 이 라운드는 closeout 항목을 `- 없음`으로 바로잡았고, 기존 `/work` 문서를 되돌리지는 않았습니다.
