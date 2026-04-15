# history-card latest-update load-by-id remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-stored-record-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-stored-record-remaining-response-origin-verification.md`)는 latest-update history-card reload-follow-up 경로의 persisted record `response_origin`을 세 follow-up service 테스트에서 `provider == "web"`, `badge == "WEB"`, `label == "외부 웹 최신 확인"`, `kind == "assistant"`, `model is None`, `answer_mode == "latest_update"`, variant별 `verification_label` / `source_roles`까지 exact-field로 고정했습니다. 즉, follow-up 쪽의 reload surface + persisted stored record 두 층은 이미 현재 worktree 안에서 닫힌 상태였습니다.

같은 family에서 남은 가장 가까운 current-risk는 basic `load_web_search_record_id` show-only history-card 경로였습니다. 이 쪽은 persisted record를 이미 한 라운드에서 잠근 동일 stored-record contract를 바탕으로 동작하지만, show-only 테스트 자체는 여전히 `answer_mode`, `verification_label`, `source_roles`만 exact-field로 잡고 `provider` / `badge` / `label` / `kind` / `model`은 잡지 않고 있었습니다. 노이즈-커뮤니티 latest-update reload 강화보다 이 쪽이 사용자 입장에서 더 직접적인 history-card reload 흐름이고, 같은 stored-record contract 위에 올라타 있으므로 이 라운드는 basic show-only 경로의 남은 literal들을 한 바운드 안에서 마저 잠급니다.

## 핵심 변경

1. 기존 두 show-only latest-update by-id 테스트에서 `reload_origin` assertion을 latest-update exact-field 계약으로 강화했습니다.
   - `test_handle_chat_load_web_search_record_id_single_source_latest_update_exact_fields` — session `"reload-by-id-single-session"`, variant 단일 출처 (`verification_label == "단일 출처 참고"`, `source_roles == ["보조 출처"]`)
   - `test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields` — session `"reload-by-id-mixed-session"`, variant 공식+기사 교차 (`verification_label == "공식+기사 교차 확인"`, `source_roles == ["보조 기사", "공식 기반"]`)
   - 두 테스트 모두 기존 `actions_taken == ["load_web_search_record"]` / `web_search_record_path` assertion은 그대로 유지했습니다.
2. 새 news-only 평행 테스트 `test_handle_chat_load_web_search_record_id_news_only_latest_update_exact_fields`를 바로 뒤에 추가했습니다. session `"reload-by-id-news-session"`, fake 검색 소스는 latest-update follow-up news-only 테스트와 동일한 non-noisy 두 기사 패턴(`hankyung.com/economy/2025`, `mk.co.kr/economy/2025`)을 사용하고, reload 결과에서 `actions_taken == ["load_web_search_record"]`, `web_search_record_path`, 그리고 latest-update exact-field 세트 + variant별 `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`을 잡습니다.

세 테스트 공통 latest-update reload_origin assertion 블록:

```
self.assertIsNotNone(reload_origin)
self.assertEqual(reload_origin["provider"], "web")
self.assertEqual(reload_origin["badge"], "WEB")
self.assertEqual(reload_origin["label"], "외부 웹 최신 확인")
self.assertEqual(reload_origin["kind"], "assistant")
self.assertIsNone(reload_origin["model"])
self.assertEqual(reload_origin["answer_mode"], "latest_update")
```

follow-up latest-update 테스트, stored-record latest-update 계약 (별도 라운드에서 이미 잠긴 세트), natural reload latest-update 테스트, noisy-community latest-update family, 브라우저/Playwright, entity-card / dual-probe / zero-strong / actual-search family는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_single_source_latest_update_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_news_only_latest_update_exact_fields` → `Ran 3 tests in 0.049s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 service-only reload surface 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted three-test bundle로 충분합니다.

## 남은 리스크

- 새로 추가한 news-only by-id 테스트에 대응하는 persisted stored-record exact assertion은 이 슬라이스에서 추가하지 않았습니다. 필요하다면 별도 슬라이스에서 `service.web_search_store.get_session_record(...)` 기반 contract로 잠글 수 있습니다.
- noisy-community latest-update family의 show-only / stored / follow-up 계약은 아직 확인하지 않았습니다.
- natural (non-history-card) latest-update reload show-only 경로는 이 슬라이스 범위 밖이므로 해당 경로의 추가 literal 필요 여부는 확인되지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
