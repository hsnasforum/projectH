# history-card simple entity-card stored-origin fixture realignment exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

- 최신 `/verify`는 simple stored-origin 계열에서 남은 drift가 `tests/test_web_app.py:16546`, `tests/test_web_app.py:16642` 두 지점임을 확인했습니다. 두 테스트는 이름상 generic simple stored-origin 앵커지만, fixture는 dict 기반 dual-probe + `pages=` 모양으로 과잉 구성되어 있어서 simple single-source branch 의도와 맞지 않았습니다.
- Dual-probe exact service/browser coverage는 이미 `tests/test_web_app.py:9628`, `tests/test_web_app.py:10014`, `e2e/tests/web-smoke.spec.mjs:3096`에서 닫혀 있으므로, 이 두 서비스 테스트를 dual-probe 쪽으로 끌어올리는 것은 동일 가족 중복입니다. 대신 simple single-source fixture로 맞추고, 이미 닫힌 `tests/test_web_app.py:8570`의 shipped simple literal과 동일하게 `reload_origin` exact 필드를 literal로 고정하는 것이 최소 same-family current-risk reduction입니다.

## 핵심 변경

- `test_handle_chat_entity_card_reload_preserves_stored_response_origin`:
  - dict 기반 `_FakeWebSearchTool({...}, pages={...})` 네 probe + 두 공식 페이지 fixture를 제거하고, `tests/test_web_app.py:8588` reference와 동일한 list 기반 단일 `SimpleNamespace` 나무위키 result 한 건짜리 simple single-source fixture로 교체했습니다.
  - `first_origin` 기반 equality 블록을 제거하고 `reload_origin["badge"] == "WEB"`, `reload_origin["answer_mode"] == "entity_card"`, `reload_origin["verification_label"] == "설명형 단일 출처"`, `reload_origin["source_roles"] == ["백과 기반"]` literal 4종으로 교체했습니다.
  - runtime에서 `reload_origin.get("provider")` 계열이 이 simple entity-card reload 경로에서 이미 shipped reference 테스트(`tests/test_web_app.py:8627`)에서도 literal로 고정되어 있지 않아, unstable 가능성을 피하기 위해 provider literal 단언은 추가하지 않았습니다.
  - 위 교체로 unused 상태가 된 `first_origin` local을 제거했습니다.
- `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin`:
  - 동일한 방식으로 fixture를 list 기반 단일 나무위키 result 한 건짜리 simple single-source fixture로 교체했습니다.
  - `self.assertIsNotNone` + `self.assertIn(reload_origin.get("answer_mode", ""), ("entity_card", first_origin["answer_mode"]))` 느슨한 블록을 제거하고 첫 테스트와 동일한 literal 4종(`badge`, `answer_mode`, `verification_label`, `source_roles`)으로 교체했습니다.
  - provider literal 단언은 동일 이유로 추가하지 않았습니다.
  - 위 교체로 unused 상태가 된 `first_origin` local을 제거했습니다.
- 편집 범위는 `tests/test_web_app.py`에 국한했고, `test_handle_chat_load_web_search_record_id_entity_card_exact_fields`, 이미 닫힌 dual-probe / zero-strong / actual-search 계열, 브라우저 테스트, docs, pipeline 파일은 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → 2 tests OK.
- `git diff --check -- tests/test_web_app.py work/4/10` → whitespace issue 없음.
- 이 라운드는 simple single-source fixture 재정렬과 service-level literal lock 범위이므로, browser-visible 계약을 건드리지 않아 `make e2e-test` 전체 브라우저 스위트는 과하다고 판단하여 실행하지 않았습니다.

## 남은 리스크

- 이 두 서비스 테스트는 이제 simple single-source literal 계약으로 고정되었으므로, 추후 entity-card reload 경로에서 runtime이 `verification_label`이나 `source_roles` 표현을 조정하면 동일 가족의 `tests/test_web_app.py:8627` reference 테스트와 동시에 갱신해야 합니다.
- `reload_origin.get("provider")`에 대한 literal lock은 여전히 비어 있습니다. simple entity-card reload 경로에서 `provider="web"`이 안정적으로 방출되는 것이 확인되면 별도 후속 슬라이스에서 네 literal과 함께 한 번에 잠글 수 있습니다.
