# history-card latest-update noisy-community natural-reload stored-record remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-natural-reload-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-remaining-response-origin-verification.md`)는 noisy-community latest-update natural-reload first / second follow-up 두 테스트의 surface `response_origin`을 click-reload 쪽과 동일한 latest-update exact-field 계약으로 정렬했습니다. 즉, noisy-community natural-reload 경로의 response-surface exactness는 이미 닫힌 상태입니다.

같은 noisy-community natural-reload family에서 남은 가장 가까운 current-risk는 같은 두 테스트의 persisted stored `response_origin` 계약이었습니다. `session["web_search_history"]` 항목 구조가 `response_origin` 객체를 통째로 노출하지 않는다는 점은 직전 store-read 라운드들에서 이미 확인되었고, session summary serializer를 넓히는 것은 이 슬라이스 범위 밖입니다. 그래서 이 슬라이스는 앞선 click-reload 쪽 store-read 패턴을 그대로 재사용해 두 natural-reload 테스트에 persisted stored `response_origin` exact-field 계약을 한 번에 추가합니다. click-reload 계열이나 다른 history-card family, serializer 변경으로 넘어가지 않고 same-family current-risk 하나만 닫습니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 두 service 테스트에서, follow-up `handle_chat` 호출 직후(surface `origin` 추출 전) `service.web_search_store.get_session_record(<session_id>, record_id)`로 persisted record를 읽어 stored `response_origin` exact assertion 블록을 추가했습니다. 기존 surface `origin` contract, negative 제외 계약(`보조 커뮤니티`, `brunch`), positive retained `source_paths`, `latest_entry["verification_label"]` 확인 및 zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` 블록은 전부 그대로 유지했습니다.

- `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up`  
  → session `"latest-noisy-nat-fu-session"`, first follow-up `third` 호출 뒤
- `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up`  
  → session `"latest-noisy-nat-2fu-session"`, second follow-up `fourth` 호출 뒤

두 테스트 공통 stored assertion 블록:

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

noisy-community click-reload 테스트, non-noisy latest-update family, entity-card / dual-probe / zero-strong / actual-search family, session summary serializer, 브라우저/Playwright는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up` → `Ran 2 tests in 0.074s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 persistence service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted two-test bundle로 충분합니다.

## 남은 리스크

- noisy-community latest-update family에서 같은 축으로 남은 (baseline natural-reload, 즉 follow-up 없이 `"방금 검색한 결과 다시 보여줘"`로만 끝나는) 경로의 stored / surface exact 계약 필요 여부는 이 라운드에서 확인하지 않았습니다.
- entity-card family 외 다른 family (dual-probe / zero-strong / actual-search)의 noisy natural-reload persistence 계약은 이 라운드에서 확인하지 않았습니다.
- `session["web_search_history"]` 항목이 `response_origin` 객체를 노출하지 않는 구조 자체는 유지되었고, 추후 요약 serializer를 넓히게 되면 store-read 대신 history_entry에서 직접 검증하도록 정리할 여지가 있습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
