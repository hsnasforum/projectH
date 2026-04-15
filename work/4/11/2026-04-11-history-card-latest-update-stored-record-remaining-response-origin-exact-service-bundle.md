# history-card latest-update stored-record remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-follow-up-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-follow-up-remaining-response-origin-verification.md`)는 latest-update history-card reload-follow-up 경로의 reload 응답 surface를 `provider == "web"`, `badge == "WEB"`, `label == "외부 웹 최신 확인"`, `kind == "assistant"`, `model is None`, `answer_mode == "latest_update"`, variant별 `verification_label` / `source_roles`까지 exact-field로 고정했습니다. 즉, 세 latest-update follow-up service 테스트의 reload 응답 contract는 이미 현재 worktree 안에서 닫힌 상태였습니다.

같은 family에서 남은 가장 가까운 current-risk는 reload surface가 의존하는 상위 계약인 persisted record 그 자체였습니다. `core/agent_loop.py`의 `response_origin` 저장 경로와 `storage/web_search_store.py`의 직렬화, 그리고 show-only reload에서 `stored_origin`을 직접 재사용하는 흐름은 전부 persisted record가 먼저 올바르게 저장되어 있다는 전제 위에 서 있기 때문에, stored record를 직접 고정하는 편이 또 다른 응답-surface-only 마이크로 타이트닝보다 same-family risk reduction에 더 직접적입니다. 이 슬라이스는 동일 세 service 테스트에서 첫 호출로 `record_id`가 확보된 직후 `service.web_search_store.get_session_record(...)`로 저장 레코드를 읽어 같은 latest-update literal 세트를 exact-field로 잡습니다. reload 이후의 assertion 블록과 zero-count claim_coverage 블록은 그대로 둡니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 service 테스트에서, 첫 `handle_chat` 호출로 `record_id`가 확보된 직후에 persisted record 조회와 stored response-origin exact assertion 블록을 추가했습니다.

- `test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin`  
  → mixed-source variant, session `"latest-followup-origin-session"`
- `test_handle_chat_latest_update_single_source_reload_follow_up_preserves_stored_response_origin`  
  → single-source variant, session `"latest-single-followup-origin-session"`
- `test_handle_chat_latest_update_news_only_reload_follow_up_preserves_stored_response_origin`  
  → news-only variant, session `"latest-news-followup-origin-session"`

세 테스트 공통 assertion:

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

variant별 추가 두 줄:
- mixed-source: `verification_label == "공식+기사 교차 확인"`, `source_roles == ["보조 기사", "공식 기반"]`
- single-source: `verification_label == "단일 출처 참고"`, `source_roles == ["보조 출처"]`
- news-only: `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`

기존 reload-origin exact assertion 블록, `history_entry` 조회, zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` assertion은 그대로 유지했습니다. show-only latest-update 테스트, natural reload latest-update 테스트, noisy-community latest-update family, 브라우저/Playwright, entity-card / dual-probe / zero-strong / actual-search family는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.068s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 persistence-계약 service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted three-test bundle로 충분합니다.

## 남은 리스크

- `load_web_search_record_id` show-only latest-update reload 경로의 stored-record 계약, natural (non-history-card) latest-update reload 계약, noisy-community latest-update family의 stored/reload 계약은 이 슬라이스 바깥으로 남겨 두었습니다.
- 이 라운드는 latest-update family에서 stored + reload-follow-up 두 층을 잠그지만, entity-card 외 다른 family (dual-probe / zero-strong / actual-search)의 stored-record response-origin exact 계약은 아직 확인하지 않았습니다.
- `first_origin` 로컬은 세 테스트 안에서 여전히 사용되지 않지만, 파일 전역 패턴 보존을 위해 이번 슬라이스에서도 그대로 두었습니다. 별도 청소 슬라이스에서 다룰 여지가 있습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 이전 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
