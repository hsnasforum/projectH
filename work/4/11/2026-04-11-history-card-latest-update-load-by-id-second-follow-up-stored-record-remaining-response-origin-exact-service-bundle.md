# history-card latest-update load-by-id second-follow-up stored-record remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-load-by-id-follow-up-chain-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-load-by-id-follow-up-chain-remaining-response-origin-verification.md`)는 click reload (`load_web_search_record_id`) latest-update follow-up chain 여섯 테스트의 follow-up 응답 `origin`을 `provider`, `badge`, `label`, `kind`, `model`, `answer_mode`, variant별 `verification_label` / `source_roles`까지 exact-field로 고정했습니다. 즉, click-reload follow-up chain의 surface exactness는 이미 닫힌 상태입니다.

first follow-up 쪽 persisted stored 계약은 앞선 라운드에서 이미 잠겨 있지만, 세 second-follow-up 테스트 (`..._reload_second_follow_up_...`)는 여전히 `history_entry`의 `claim_coverage_summary` / `claim_coverage_progress_summary` zero-count만 고정하고, 실제 persisted `response_origin`은 한 층도 잡지 않고 있었습니다. 런타임 probe 결과 `session["web_search_history"]` 항목에는 `answer_mode` / `verification_label` / `source_roles`는 있지만 `response_origin` 객체 자체는 들어가지 않기 때문에, handoff가 허용한 "unless the current structure forces it" 예외 조건이 실제로 발동되어, persisted contract를 잠그려면 이미 파일 전역에서 쓰이고 있는 `service.web_search_store.get_session_record(...)`로 store를 직접 읽는 방식이 불가피합니다. 노이즈-커뮤니티 latest-update 계열을 건드리는 것보다 non-noisy click-reload chain의 persistence 틈을 같은 세 테스트 안에서 한 번에 닫는 것이 더 좁고 직접적인 current-risk reduction이라, 이 슬라이스는 세 second-follow-up 테스트에 store-read 기반 stored `response_origin` exact assertion만 추가합니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 service 테스트에서, 네 번째 `handle_chat` 호출 직후 surface `origin` 블록을 읽기 전에 `service.web_search_store.get_session_record(<session_id>, record_id)` 조회와 stored `response_origin` exact assertion 블록을 추가했습니다. 기존 `origin` assertion, `source_paths` 검증, `history_entry` 조회, zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` assertion 블록은 그대로 유지했습니다.

- `test_handle_chat_latest_update_mixed_source_reload_second_follow_up_preserves_response_origin_and_source_paths`  
  → session `"latest-mixed-2fu-session"`, variant `verification_label == "공식+기사 교차 확인"`, `source_roles == ["보조 기사", "공식 기반"]`
- `test_handle_chat_latest_update_single_source_reload_second_follow_up_preserves_response_origin_and_source_paths`  
  → session `"latest-single-2fu-session"`, variant `verification_label == "단일 출처 참고"`, `source_roles == ["보조 출처"]`
- `test_handle_chat_latest_update_news_only_reload_second_follow_up_preserves_response_origin_and_source_paths`  
  → session `"latest-news-2fu-session"`, variant `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`

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
```

first follow-up stored 테스트, natural-reload latest-update family, show-only by-id latest-update 테스트, noisy-community latest-update family, entity-card / dual-probe / zero-strong / actual-search family, 브라우저/Playwright는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_second_follow_up_preserves_response_origin_and_source_paths` → `Ran 3 tests in 0.111s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 persistence service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted three-test bundle로 충분합니다.

## 남은 리스크

- noisy-community latest-update family (baseline / click-reload / follow-up / second follow-up / stored record / by-id 등) 계약은 이 슬라이스 범위 밖입니다.
- 같은 axis에서 entity-card 외 다른 family (dual-probe / zero-strong / actual-search)의 click-reload second-follow-up stored `response_origin` exact 계약은 이 라운드에서 확인하지 않았습니다.
- 이 라운드는 store-read 기반 stored assertion을 추가했지만, persisted-record serialization이 미래에 바뀌어 `session["web_search_history"]` 항목에도 `response_origin`을 포함하게 되면 같은 내용을 `history_entry`에서 직접 검증하는 방식으로 정리할 여지가 있습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
