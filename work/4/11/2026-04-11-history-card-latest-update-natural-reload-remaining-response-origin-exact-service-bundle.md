# history-card latest-update natural-reload remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-load-by-id-stored-record-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-load-by-id-stored-record-remaining-response-origin-verification.md`)는 latest-update history-card by-id (`load_web_search_record_id`) 경로의 persisted stored record + reload 응답 surface 두 층을 single-source, mixed-source, news-only 세 variant 모두 `provider == "web"`, `badge == "WEB"`, `label == "외부 웹 최신 확인"`, `kind == "assistant"`, `model is None`, `answer_mode == "latest_update"`, variant별 `verification_label` / `source_roles`까지 exact-field로 고정했습니다. 즉, by-id history-card 경로의 same-family contract는 현재 worktree 안에서 이미 end-to-end로 닫힌 상태입니다.

같은 family에서 남은 가장 가까운 current-risk는 baseline natural reload trio — `"방금 검색한 결과 다시 보여줘"` 자연어 reload — 였습니다. 세 테스트 모두 reload 응답의 `answer_mode` / `verification_label` / `source_roles`만 exact로 잡고, `provider` / `badge` / `label` / `kind` / `model`과 persisted stored record는 잡지 않은 상태였습니다. 이 경로가 baseline 쪽이고 by-id 경로와 동일한 latest-update literal 세트를 재사용하므로, 이 슬라이스는 이 세 테스트를 한 번에 묶어 reload 응답 surface와 persisted stored record 두 층 모두를 같은 exact-field 계약으로 한 바운드 안에서 닫습니다. 노이즈-커뮤니티 latest-update 계열과 follow-up / entity-card / dual-probe / zero-strong / actual-search 등 다른 family로는 번지지 않습니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 baseline natural reload service 테스트에서, 첫 `handle_chat` 호출 직후 `record_id`를 `first["session"]["web_search_history"][0]["record_id"]`로 확보하고, 두 번째 `handle_chat` reload 호출 직전에 `service.web_search_store.get_session_record(...)` 기반 stored record assertion 블록을 추가했습니다. 두 번째 호출 뒤의 `reload_origin` assertion은 latest-update exact-field 계약으로 강화했습니다. 기존 `actions_taken == ["load_web_search_record"]`, `web_search_record_path`, `source_paths`, zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` assertion 블록은 그대로 유지했습니다.

- `test_handle_chat_mixed_source_latest_update_reload_exact_fields`  
  → session `"reload-mixed-session"`, variant `verification_label == "공식+기사 교차 확인"`, `source_roles == ["보조 기사", "공식 기반"]`
- `test_handle_chat_single_source_latest_update_reload_exact_fields`  
  → session `"reload-single-session"`, variant `verification_label == "단일 출처 참고"`, `source_roles == ["보조 출처"]`
- `test_handle_chat_news_only_latest_update_reload_exact_fields`  
  → session `"reload-news-session"`, variant `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`

세 테스트 공통 stored + reload 공통 literal 블록:

```
self.assertEqual(stored_origin["provider"], "web")
self.assertEqual(stored_origin["badge"], "WEB")
self.assertEqual(stored_origin["label"], "외부 웹 최신 확인")
self.assertEqual(stored_origin["kind"], "assistant")
self.assertIsNone(stored_origin["model"])
self.assertEqual(stored_origin["answer_mode"], "latest_update")

# ... reload 후 ...

self.assertEqual(reload_origin["provider"], "web")
self.assertEqual(reload_origin["badge"], "WEB")
self.assertEqual(reload_origin["label"], "외부 웹 최신 확인")
self.assertEqual(reload_origin["kind"], "assistant")
self.assertIsNone(reload_origin["model"])
self.assertEqual(reload_origin["answer_mode"], "latest_update")
```

by-id latest-update 테스트, follow-up / second-follow-up latest-update 테스트, noisy-community latest-update family, entity-card / dual-probe / zero-strong / actual-search family, 브라우저/Playwright는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_mixed_source_latest_update_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_single_source_latest_update_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_news_only_latest_update_reload_exact_fields` → `Ran 3 tests in 0.049s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 persistence + reload surface service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted three-test bundle로 충분합니다.

## 남은 리스크

- noisy-community latest-update family (show-only / stored / natural reload / follow-up) 계약은 이 슬라이스 범위 밖입니다.
- 이 슬라이스는 baseline natural reload만 닫았고, follow-up / second-follow-up latest-update natural 경로의 추가 literal 필요 여부는 확인하지 않았습니다.
- entity-card family 외 다른 family (dual-probe / zero-strong / actual-search)의 baseline natural reload stored-record exact 계약은 아직 확인하지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
