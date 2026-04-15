# history-card simple entity-card click-reload kind/model exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- superpowers:using-superpowers

## 변경 이유

이전 `/work`와 `/verify`가 simple entity-card click-reload 경로에서 `label == "외부 웹 설명 카드"` 까지의 exact-field service 대조를 truthfully 닫았지만, 같은 세 service 테스트에는 여전히 `reload_origin["kind"]`와 `reload_origin["model"]`에 대한 직접 assertion이 존재하지 않았습니다. simple seeded browser fixture는 이미 `kind: "assistant"`와 `model: None`을 emit하고 있고 `app/static/app.js`는 그 두 필드를 origin-detail에서 그대로 사용하므로, 이 두 필드를 같은 three-test service bundle 안에서 한 번에 닫아 두 번의 추가 micro-slice를 피합니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 service 테스트에 기존 `provider` / `label` exact-field block 바로 뒤에 두 줄 assertion을 추가했습니다.

- `test_handle_chat_load_web_search_record_id_entity_card_exact_fields`
- `test_handle_chat_entity_card_reload_preserves_stored_response_origin`
- `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin`

각 테스트에 다음 두 assertion을 추가했습니다.

- `self.assertEqual(reload_origin["kind"], "assistant")`
- `self.assertIsNone(reload_origin["model"])`

fixture, browser anchor, 다른 response-origin family (dual-probe / zero-strong / actual-search / latest-update)는 수정하지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.070s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- browser-visible 계약이 바뀌지 않는 service-only assertion bundle이므로 `make e2e-test`는 이번 라운드에서 과합니다.

## 남은 리스크

- service-level assertion만 강화했고 browser fixture / Playwright anchor는 건드리지 않았으므로, 만약 이후 simple entity-card click-reload 경로에서 browser DOM 레벨의 `kind` / `model` surfacing 계약을 추가로 고정해야 한다면 별도 브라우저-계약 슬라이스가 필요합니다.
- 다른 response-origin family (dual-probe / zero-strong / actual-search / latest-update)의 동일한 `kind` / `model` exact-field 대조 여부는 이 라운드의 범위 밖이며 확인하지 않았습니다.
