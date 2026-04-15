# history-card latest-update follow-up remaining response-origin exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-simple-entity-card-stored-record-remaining-response-origin-exact-service-bundle.md`)와 그에 대응하는 `/verify` (`verify/4/11/2026-04-11-simple-entity-card-stored-record-remaining-response-origin-verification.md`)는 simple entity-card history-card 경로의 persisted record 응답 출처 계약을 더 이상 `kind` / `model`에만 묶어 두지 않고, 같은 세 service 테스트에서 `provider == "web"`, `badge == "WEB"`, `label == "외부 웹 설명 카드"`, `answer_mode == "entity_card"`, `verification_label == "설명형 단일 출처"`, `source_roles == ["백과 기반"]`까지 exact-field로 고정했습니다. 즉, simple entity-card stored-record response-origin family는 현재 worktree 안에서 이미 닫힌 상태입니다.

같은 축에서 남은 가장 가까운 current-risk는 latest-update history-card의 reload-follow-up 경로였습니다. 세 latest-update follow-up service 테스트는 reload 시점의 `reload_origin`을 `verification_label` + `source_roles`만 exact-field로 잡고, 나머지 `answer_mode`는 `assertIn(reload_origin.get("answer_mode", ""), ("latest_update", first_origin["answer_mode"]))`라는 두-후보 허용 형태로, `provider` / `badge` / `label` / `kind` / `model`은 아예 잡지 않았습니다. 이것은 show-only natural reload trio가 이미 exact-field `answer_mode == "latest_update"`까지 잡고 있는 쪽보다 더 느슨했고, 사용자 입장에서는 history-card reload 뒤 추가 질문까지 이어지는 경로이므로 현재 risk가 더 직접적이었습니다.

이 라운드는 동일 세 service 테스트의 `reload_origin` assertion 블록을 latest-update 전체 literal 세트 exact-field 계약으로 교체해 follow-up 경로 쪽 남은 current-risk를 한 바운드 안에서 닫습니다. `first_origin` 로컬은 다른 테스트 전역에서 쓰이는 일반 패턴이므로 제거하지 않고 그대로 두어 같은 세 테스트 바깥으로 범위가 번지지 않게 했습니다.

## 핵심 변경

`tests/test_web_app.py`의 아래 세 service 테스트에서, reload-follow-up 직후 `reload_origin` 주변의 느슨한 assertion 블록을 latest-update exact-field 계약으로 교체했습니다.

- `test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin`  
  → mixed-source variant
- `test_handle_chat_latest_update_single_source_reload_follow_up_preserves_stored_response_origin`  
  → single-source variant
- `test_handle_chat_latest_update_news_only_reload_follow_up_preserves_stored_response_origin`  
  → news-only variant

세 테스트 공통 assertion (variant별 마지막 두 줄만 다릅니다):

```
self.assertIsNotNone(reload_origin)
self.assertEqual(reload_origin["provider"], "web")
self.assertEqual(reload_origin["badge"], "WEB")
self.assertEqual(reload_origin["label"], "외부 웹 최신 확인")
self.assertEqual(reload_origin["kind"], "assistant")
self.assertIsNone(reload_origin["model"])
self.assertEqual(reload_origin["answer_mode"], "latest_update")
```

variant별 유지 라인:
- mixed-source: `verification_label == "공식+기사 교차 확인"`, `source_roles == ["보조 기사", "공식 기반"]`
- single-source: `verification_label == "단일 출처 참고"`, `source_roles == ["보조 출처"]`
- news-only: `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`

세 테스트의 기존 zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` assertion과 history_entry 조회 블록은 그대로 유지했습니다. stored-record latest-update 계약, natural reload show-only 테스트, 브라우저/Playwright, entity-card / dual-probe / zero-strong / actual-search family는 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.058s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 persistence-계약 service-only 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. targeted three-test bundle로 충분합니다.

## 남은 리스크

- stored-record latest-update exact-field 계약 (`service.web_search_store.get_session_record(...)` 측면)은 이 라운드에서 건드리지 않았습니다. simple entity-card쪽과 달리 latest-update follow-up trio는 여전히 reload_origin만 고정합니다.
- natural (non-history-card) latest-update reload show-only 계열은 이미 exact-field `answer_mode`를 가지고 있지만, 새로 추가한 provider/badge/label/kind/model literal들이 거기에도 필요한지는 이 라운드에서 확인하지 않았습니다.
- `first_origin` 로컬은 세 테스트 안에서 이제 사용되지 않지만, 파일 전역에서 동일한 패턴이 여러 테스트에 있기 때문에 범위 확장을 피하기 위해 제거하지 않았습니다. 별도 청소 슬라이스에서 다룰 여지가 있습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 이전 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
