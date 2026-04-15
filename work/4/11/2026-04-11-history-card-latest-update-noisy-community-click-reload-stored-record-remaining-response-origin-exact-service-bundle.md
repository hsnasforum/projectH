# history-card latest-update noisy-community click-reload stored-record remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-click-reload-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-remaining-response-origin-verification.md`)는 noisy-community click-reload 세 테스트 (show-only reload / first follow-up / second follow-up)의 surface `origin`을 non-noisy click-reload 경로와 동일한 latest-update exact-field 계약으로 정렬했습니다. 즉, noisy-community click-reload 경로의 response-surface 쪽 exactness는 이미 닫힌 상태입니다.

같은 history-card click-reload 흐름에서 남은 가장 가까운 current-risk는 같은 세 테스트의 persisted stored `response_origin` 계약이었습니다. `session["web_search_history"]` 항목 구조가 `response_origin` 객체를 통째로 노출하지 않는다는 점은 앞선 라운드에서 runtime probe로 이미 확인되었고, session summary serializer를 넓히는 것은 이 슬라이스 범위 밖입니다. 그래서 이 슬라이스는 non-noisy쪽에서 이미 쓰고 있는 `service.web_search_store.get_session_record(...)` store-read 패턴을 그대로 재사용해, 세 noisy 테스트에 persisted stored `response_origin` exact-field 계약을 한 번에 추가합니다. natural-reload noisy 계열이나 다른 family로 넘어가는 대신 같은 click-reload 흐름의 persistence 틈만 닫는 것이 same-family current-risk reduction에 더 직접적입니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 service 테스트에서, 기존 surface assertion 블록과 `history_entry` 계열 zero-count 블록은 그대로 두고, 같은 세션의 persisted record를 `service.web_search_store.get_session_record(...)`로 읽어 `stored_origin`에 latest-update exact-field + noisy-community-positive literal 세트를 함께 잠그는 블록을 추가했습니다.

- `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload`  
  → session `"latest-update-noisy-reload-by-id-session"`, show-only `second` 호출 직후의 노이즈 제외 assertion 뒤에 store-read 블록 삽입
- `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up`  
  → session `"latest-noisy-click-fu-session"`, first follow-up `third` 호출 직후의 `origin` 추출 전에 store-read 블록 삽입
- `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up`  
  → session `"latest-noisy-click-2fu-session"`, second follow-up `fourth` 호출 직후의 `origin` 추출 전에 store-read 블록 삽입

세 테스트 공통 stored assertion 블록:

```
stored_record = service.web_search_store.get_session_record(
    "<session_id>", record_id
)
self.assertIsNotNone(stored_record)
stored_origin = stored_record["response_origin"]
self.assertEqual(stored_origin["provider"], "web")
self.assertEqual(stored_origin["badge"], "WEB")
self.assertEqual(stored_origin["label"], "외부 웹 최신 확인")
self.assertEqual(stored_origin["kind"], "assistant")
self.assertIsNone(stored_origin["model"])
self.assertEqual(stored_origin["answer_mode"], "latest_update")
self.assertEqual(
    stored_origin["verification_label"], "기사 교차 확인"
)
self.assertEqual(stored_origin["source_roles"], ["보조 기사"])
```

surface `origin` 계약, negative 제외 계약(`보조 커뮤니티`, `brunch`), positive retained `source_paths`, zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` 블록은 전부 그대로 유지했습니다. non-noisy latest-update family, noisy-community natural-reload 테스트, entity-card / dual-probe / zero-strong / actual-search family, session summary serializer, 브라우저/Playwright는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up` → `Ran 3 tests in 0.086s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 persistence service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted three-test bundle로 충분합니다.

## 남은 리스크

- noisy-community latest-update natural-reload 쪽 (`test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up` 등)의 surface + stored exact 계약은 이 슬라이스 범위 밖입니다.
- `session["web_search_history"]` 항목이 `response_origin` 객체를 노출하지 않는 구조 자체는 유지되었고, 추후 요약 serializer를 넓히게 되면 store-read 대신 history_entry에서 직접 검증하도록 정리할 여지가 있습니다.
- entity-card family 외 다른 family (dual-probe / zero-strong / actual-search)의 noisy click-reload persistence 계약은 이 라운드에서 확인하지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
