# history-card latest-update noisy-community initial-response exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-verification.md`)는 noisy-community latest-update natural-reload 의 follow-up 없이 `"방금 검색한 결과 다시 보여줘"`에서 끝나는 reload-only branch까지 잠가, noisy family의 click-reload show-only, natural-reload show-only, click-reload first/second follow-up, natural-reload first/second follow-up 계약을 surface + stored 두 층에서 모두 닫았습니다.

같은 noisy-community latest-update family에서 남은 마지막 direct user-visible gap은 **초기 검색 응답 자체**였습니다. 기존 `test_handle_chat_latest_update_noisy_source_excluded_from_body_and_badge` 는 `first_origin["answer_mode"] == "latest_update"` 과 noisy-community 제외 (`보조 커뮤니티`, `brunch`), history badge 쪽 noisy 제외만 잡고, `provider` / `badge` / `label` / `kind` / `model` / `verification_label` / positive `source_roles` / persisted stored `response_origin` 은 전혀 잠그지 않고 있었습니다. 이 슬라이스는 같은 테스트를 truthfully 강화해, 초기 응답 surface와 persisted stored record 두 층을 다른 reload/follow-up 계열과 동일한 latest-update exact-field 계약으로 정렬하고, 같은 테스트 안에서 directly 접근 가능한 initial history entry의 `verification_label`, zero-count `claim_coverage_summary`, 빈 `claim_coverage_progress_summary` 만 함께 잠급니다. 두 번째 reload 블록과 다른 family, 브라우저 축으로는 번지지 않습니다.

## 핵심 변경

`tests/test_web_app.py`의 `test_handle_chat_latest_update_noisy_source_excluded_from_body_and_badge`에서 기존 `first` 호출 직후 블록을 다음과 같이 강화했습니다.

1. `record_id`를 `first["session"]["web_search_history"][0]["record_id"]`로 캡처.
2. `first_origin`에 latest-update exact-field assertion 세트 추가:
   - `provider == "web"`, `badge == "WEB"`, `label == "외부 웹 최신 확인"`
   - `kind == "assistant"`, `model is None`, `answer_mode == "latest_update"`
   - `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`
3. 기존 noisy 제외 assertion (`보조 커뮤니티`, `brunch`, history badge noisy-role 제외)은 그대로 유지.
4. `first_history` 쪽에 같은 테스트에서 이미 접근 가능한 directly available 필드 계약 추가:
   - `verification_label == "기사 교차 확인"`
   - zero-count `claim_coverage_summary`, 빈 `claim_coverage_progress_summary`
5. `service.web_search_store.get_session_record("latest-update-noisy-session", record_id)` 으로 persisted record를 읽고, 같은 latest-update exact-field literal 세트를 `stored_origin` 에 대해 잠금.

기존 자연어 reload 블록 (`"방금 검색한 결과 다시 보여줘"` 기반 `reload_origin` noisy 제외) 은 건드리지 않았습니다. noisy-community 이외 family, entity-card / dual-probe / zero-strong / actual-search, session summary serializer, 브라우저/Playwright도 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_from_body_and_badge` → `Ran 1 test in 0.037s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 service-only 계약 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. 단일 테스트 실행으로 충분합니다.

## 남은 리스크

- 같은 `test_handle_chat_latest_update_noisy_source_excluded_from_body_and_badge` 내부의 두 번째 `reload_origin` 블록은 이 슬라이스 범위 밖이므로 여전히 `answer_mode` 외 exact 계약을 잡지 않고 negative 제외만 유지합니다. 필요시 별도 라운드에서 정리할 여지가 있습니다 (다만 reload-only 브랜치는 이미 동일 family 다른 테스트에서 exact 계약이 잡혀 있습니다).
- entity-card family 외 다른 family (dual-probe / zero-strong / actual-search)의 initial-response exact 계약은 이 라운드에서 확인하지 않았습니다.
- `session["web_search_history"]` 항목이 `response_origin` 객체를 노출하지 않는 구조 자체는 유지되었고, 추후 요약 serializer 확장 시 store-read 대신 history_entry에서 직접 검증하도록 정리할 여지가 있습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, 및 untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
