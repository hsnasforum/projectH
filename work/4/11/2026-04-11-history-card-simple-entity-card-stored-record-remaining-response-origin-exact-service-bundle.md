# history-card simple entity-card stored-record remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-simple-entity-card-stored-record-kind-model-exact-service-bundle.md`)는 simple entity-card history-card 경로의 persisted record에 대해 `response_origin["kind"] == "assistant"` / `response_origin["model"] is None` 두 필드만 고정했고, 최신 `/verify`와 직접 runtime probe는 동일 stored record가 이미 `provider`, `badge`, `label`, `answer_mode`, `verification_label`, `source_roles`까지 안정적으로 직렬화된다는 것을 확인한 상태였습니다. 즉, simple stored record에서 남은 current-risk는 잠겨 있지 않은 나머지 response-origin 리터럴들이었습니다.

이 라운드는 같은 세 service 테스트에서 이미 읽고 있는 `stored_origin` 객체에 `provider == "web"`, `badge == "WEB"`, `label == "외부 웹 설명 카드"`, `answer_mode == "entity_card"`, `verification_label == "설명형 단일 출처"`, `source_roles == ["백과 기반"]` exact-field assertion을 한 번에 추가해 simple stored-record response-origin family를 한 바운드 안에서 닫습니다. provider-only / label-only / badge-only 마이크로 루프를 다시 여는 것보다, 이미 확인된 shape를 한 라운드에 bundle하는 편이 same-family current-risk reduction에 직접적입니다. browser seeded fixture sync는 shipped click-reload 경로가 persisted record에 먼저 의존하므로 이 stored-record 계약이 닫힌 뒤의 부차 슬라이스입니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 service 테스트 각각에서, 기존 `stored_record = service.web_search_store.get_session_record(...)` 조회 블록과 이미 있던 `stored_origin["kind"] == "assistant"` / `stored_origin["model"] is None` assertion은 그대로 두고, 같은 `stored_origin` 객체에 대해 remaining response-origin 리터럴을 exact-field로 추가했습니다.

- `test_handle_chat_load_web_search_record_id_entity_card_exact_fields`  
  → session_id `"reload-by-id-entity-session"`
- `test_handle_chat_entity_card_reload_preserves_stored_response_origin`  
  → session_id `"entity-origin-reload-session"`
- `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin`  
  → session_id `"entity-followup-origin-session"`

세 블록에 공통으로 추가된 assertion:

```
self.assertEqual(stored_origin["provider"], "web")
self.assertEqual(stored_origin["badge"], "WEB")
self.assertEqual(stored_origin["label"], "외부 웹 설명 카드")
self.assertEqual(stored_origin["answer_mode"], "entity_card")
self.assertEqual(
    stored_origin["verification_label"], "설명형 단일 출처"
)
self.assertEqual(stored_origin["source_roles"], ["백과 기반"])
```

이미 landed되어 있던 reload_origin assertion, `kind` / `model` stored assertion, 그리고 다른 모든 테스트는 건드리지 않았습니다. 브라우저 테스트, seeded browser fixture, docs, pipeline 파일, dual-probe / zero-strong / actual-search / latest-update family 역시 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.078s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- browser-visible 계약은 이 슬라이스에서 건드리지 않았으므로 `make e2e-test`는 과합니다. persistence 계약의 service-only 대조이므로 targeted three-test bundle로 충분합니다.

## 남은 리스크

- `e2e/tests/web-smoke.spec.mjs`의 simple seeded browser record는 여전히 stored record의 response-origin 리터럴들을 자체적으로 노출하지 않습니다. browser DOM / seeded fixture 레벨의 같은 계약 반영은 이 슬라이스 범위 밖이며, 필요하다면 별도 seeded-record sync 슬라이스에서 닫아야 합니다.
- 같은 remaining response-origin exact-field 대조를 다른 response-origin family (dual-probe / zero-strong / actual-search / latest-update) persisted record에 대해서도 적용해야 하는지는 이 라운드에서 확인하지 않았습니다.
- 저장소 상태가 여전히 dirty합니다 (`verify/4/10/2026-04-10-simple-entity-card-stored-origin-handoff-fixture-mismatch-verification.md` 및 다른 기존 pending 항목). 이 라운드는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
