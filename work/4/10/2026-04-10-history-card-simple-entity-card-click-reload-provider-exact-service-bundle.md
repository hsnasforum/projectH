# history-card simple entity-card click-reload provider exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

- 직전 `/work`는 `tests/test_web_app.py:16546`, `tests/test_web_app.py:16604` 두 simple stored-origin reload 테스트를 dual-probe fixture에서 단일 나무위키 fixture로 realign하고, `badge`, `answer_mode`, `verification_label`, `source_roles` literal을 고정했습니다. 다만 `provider` 필드는 runtime 안정성 불확실을 이유로 literal lock을 보류했습니다.
- 직후 `/verify`는 show-only reload 경로와 follow-up 경로 모두에서 `response_origin["provider"] == "web"`이 안정적으로 방출됨을 확인했습니다. 이로써 simple click-reload 서비스 계열의 남은 same-family contract gap은 `provider` literal lock 뿐입니다.
- 이 슬라이스는 이미 닫힌 dual-probe / zero-strong / actual-search / latest-update 가족을 건드리지 않고, 같은 service-level 가족 안에서 가장 작은 current-risk reduction을 닫는 정확 범위입니다.

## 핵심 변경

- `test_handle_chat_load_web_search_record_id_entity_card_exact_fields` (`tests/test_web_app.py:8570`):
  - 기존 `badge` / `answer_mode` / `verification_label` / `source_roles` literal 블록 바로 뒤에 `self.assertEqual(reload_origin["provider"], "web")` 한 줄을 추가했습니다.
- `test_handle_chat_entity_card_reload_preserves_stored_response_origin` (`tests/test_web_app.py:16546`):
  - 동일 literal 블록 바로 뒤에 `self.assertEqual(reload_origin["provider"], "web")` 한 줄을 추가했습니다.
- `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` (`tests/test_web_app.py:16604` 부근):
  - 동일 literal 블록 바로 뒤에 `self.assertEqual(reload_origin["provider"], "web")` 한 줄을 추가했습니다.
- fixture, `label`, `kind`, `model` 단언, dual-probe / zero-strong 테스트, browser anchor, docs, pipeline 파일은 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → 3 tests OK.
- `git diff --check -- tests/test_web_app.py work/4/10` → whitespace issue 없음.
- 이 라운드는 서비스 단의 literal 단언 한 줄 추가 범위라서 browser-visible 계약이 바뀌지 않았기 때문에 `make e2e-test` 전체 브라우저 스위트는 과하다고 판단하여 실행하지 않았습니다.

## 남은 리스크

- 이제 simple click-reload 서비스 계열에서 `provider` 필드도 literal로 잠겼기 때문에, runtime이 `provider` 표현을 바꾸면 세 테스트를 한 번에 갱신해야 합니다.
- 브라우저 가시 계약 쪽에서 동일한 `provider` literal lock이 필요한지 여부는 이 슬라이스 범위 밖이며, 다음 라운드에서 별도로 판단할 수 있습니다.
