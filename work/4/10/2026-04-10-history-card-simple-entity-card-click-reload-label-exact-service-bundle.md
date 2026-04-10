# history-card simple entity-card click-reload label exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

- 직전 `/work`는 simple click-reload service 계열에서 `provider == "web"` literal lock을 세 앵커(`tests/test_web_app.py:8570`, `tests/test_web_app.py:16546`, `tests/test_web_app.py:16604`)에 걸었습니다.
- 직후 `/verify`는 show-only reload와 follow-up 경로 모두에서 `response_origin["label"] == "외부 웹 설명 카드"`가 안정적으로 방출됨을 확인했고, 동일 literal이 이미 `e2e/tests/web-smoke.spec.mjs:1407`의 브라우저 seeded simple 레코드 계약에도 존재합니다.
- 따라서 남은 same-family exact-field gap 중 가장 작은 current-risk reduction은 `label` literal lock이며, `kind`/`model`로 넘어가거나 browser 번들로 확장하는 것보다 먼저 닫는 것이 맞습니다.

## 핵심 변경

- `test_handle_chat_load_web_search_record_id_entity_card_exact_fields` (`tests/test_web_app.py:8570`):
  - 기존 `provider` / `badge` / `answer_mode` / `verification_label` / `source_roles` literal 블록 바로 뒤에 `self.assertEqual(reload_origin["label"], "외부 웹 설명 카드")` 한 줄을 추가했습니다.
- `test_handle_chat_entity_card_reload_preserves_stored_response_origin` (`tests/test_web_app.py:16546`):
  - 동일 literal 블록 바로 뒤에 `self.assertEqual(reload_origin["label"], "외부 웹 설명 카드")` 한 줄을 추가했습니다.
- `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` (`tests/test_web_app.py:16604` 부근):
  - 동일 literal 블록 바로 뒤에 `self.assertEqual(reload_origin["label"], "외부 웹 설명 카드")` 한 줄을 추가했습니다.
- fixture, `kind` / `model` 단언, dual-probe / zero-strong 테스트, 브라우저 앵커, docs, pipeline 파일은 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → 3 tests OK.
- `git diff --check -- tests/test_web_app.py work/4/10` → whitespace issue 없음.
- 이 라운드는 서비스 단 literal 단언 한 줄 추가 범위라서 browser-visible 계약이 바뀌지 않았기 때문에 `make e2e-test` 전체 브라우저 스위트는 과하다고 판단하여 실행하지 않았습니다.

## 남은 리스크

- 이제 simple click-reload 서비스 계열에서 `label`도 literal로 잠겼기 때문에, runtime이 `label` 표현("외부 웹 설명 카드")을 바꾸면 세 서비스 테스트와 `e2e/tests/web-smoke.spec.mjs:1407` 브라우저 앵커를 동시에 갱신해야 합니다.
- 동일 가족의 `kind` / `model` literal lock 여부는 이 슬라이스 범위 밖이며, 다음 라운드에서 별도로 판단할 수 있습니다.
