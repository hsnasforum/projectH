# history-card latest-update load-by-id stored-record remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-load-by-id-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-load-by-id-remaining-response-origin-verification.md`)는 latest-update history-card by-id show-only 경로의 reload 응답 surface 쪽 literal 세트를 세 테스트 — single-source, mixed-source, 신규 news-only — 에서 `provider == "web"`, `badge == "WEB"`, `label == "외부 웹 최신 확인"`, `kind == "assistant"`, `model is None`, `answer_mode == "latest_update"`, variant별 `verification_label` / `source_roles`까지 exact-field로 고정했습니다. 즉, by-id 경로의 reload 결과 surface exactness는 이미 현재 worktree 안에서 닫힌 상태입니다.

같은 family에서 남은 가장 가까운 current-risk는 그 동일 세 by-id 테스트의 persisted record 자체였습니다. show-only reload는 `core/agent_loop.py`에서 `stored_origin`이 존재할 때 그 값을 직접 재사용하기 때문에, reload 결과는 고정되어 있어도 저장 레코드가 예상 literal로 직렬화되고 있음을 같은 세 테스트 안에서 직접 확인하지 않으면 상위 계약이 열린 채 남습니다. 이 슬라이스는 세 by-id 테스트 각각에서 첫 호출로 `record_id`가 확보된 직후 `service.web_search_store.get_session_record(...)`로 persisted record를 읽어 동일 latest-update literal 세트를 exact-field로 잡습니다. reload 결과 쪽 assertion은 이미 잠겨 있어 그대로 유지하고, noisy-community / follow-up / natural reload / entity-card / browser 경로는 건드리지 않습니다.

## 핵심 변경

`tests/test_web_app.py`의 다음 세 service 테스트에서, 첫 `handle_chat` 호출 직후 `record_id`를 얻는 라인과 두 번째 `handle_chat` 호출 사이에 persisted record 조회와 stored response-origin exact assertion 블록을 추가했습니다.

- `test_handle_chat_load_web_search_record_id_single_source_latest_update_exact_fields`  
  → session `"reload-by-id-single-session"`, `verification_label == "단일 출처 참고"`, `source_roles == ["보조 출처"]`
- `test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields`  
  → session `"reload-by-id-mixed-session"`, `verification_label == "공식+기사 교차 확인"`, `source_roles == ["보조 기사", "공식 기반"]`
- `test_handle_chat_load_web_search_record_id_news_only_latest_update_exact_fields`  
  → session `"reload-by-id-news-session"`, `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`

세 테스트 공통 assertion 블록:

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

variant별 두 줄만 `verification_label` / `source_roles`에서 달라집니다. 기존 `actions_taken == ["load_web_search_record"]`, `web_search_record_path`, reload_origin exact-field assertion 블록은 전부 그대로 유지했습니다. 노이즈-커뮤니티 latest-update family, follow-up latest-update 테스트, natural reload latest-update 테스트, entity-card / dual-probe / zero-strong / actual-search family, 브라우저/Playwright는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_single_source_latest_update_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_news_only_latest_update_exact_fields` → `Ran 3 tests in 0.048s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 persistence-계약 service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted three-test bundle로 충분합니다.

## 남은 리스크

- noisy-community latest-update family의 by-id show-only, stored record, follow-up 계약은 이 슬라이스 범위 밖입니다.
- natural (non-history-card) latest-update reload show-only 경로의 추가 literal 필요 여부는 이 라운드에서 확인하지 않았습니다.
- entity-card family 외 다른 family (dual-probe / zero-strong / actual-search)의 by-id stored-record exact 계약은 아직 확인하지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
