# history-card latest-update noisy-community natural-reload reload-only exact service bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-natural-reload-stored-record-remaining-response-origin-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-stored-record-remaining-response-origin-verification.md`)는 noisy-community latest-update natural-reload first / second follow-up 두 테스트에서 surface `response_origin`과 persisted stored `response_origin` 두 층을 end-to-end exact-field 계약으로 잠갔습니다. 즉, natural-reload follow-up chain은 이미 닫힌 상태입니다.

같은 user-visible history-card latest-update noisy-community family에서 남은 가장 가까운 gap은 follow-up 없이 `"방금 검색한 결과 다시 보여줘"`에서 끝나는 자연어 reload show-only branch였습니다. 기존 noisy family는 initial search, click-reload show-only, click-reload first/second follow-up, natural-reload first/second follow-up까지 잠겨 있었지만, 동일 reload user flow가 follow-up 없이 멈출 때의 service-level 계약은 서비스 테스트에 한 번도 표현되어 있지 않았습니다. 이 slice는 그 한 branch만 하나의 bounded 테스트로 닫아, 같은 slice 안에서 actions/path continuity, negative 제외, positive `source_paths`, zero-count claim-coverage summary, 그리고 surface + stored 두 층의 latest-update exact-field 계약을 함께 잠급니다. stored 쪽은 이미 다른 라운드에서 쓰고 있는 `service.web_search_store.get_session_record(...)` store-read 패턴을 그대로 재사용합니다 (`session["web_search_history"]` 요약 serializer 확장 없음).

## 핵심 변경

`tests/test_web_app.py`에 새 service 테스트 `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload`를 기존 `..._follow_up` 테스트 바로 위에 추가했습니다. fake 검색 소스와 noisy_snippet은 기존 noisy natural-reload follow-up 쪽 fixture와 동일한 shape (hankyung / mk / brunch + 공통 noisy_snippet)을 그대로 재사용했습니다.

- session id: `"latest-noisy-nat-reload-session"` (전용)
- 첫 호출: `"기준금리 속보 검색해봐"` + `web_search_permission: enabled` → `record_id` 확보
- 둘째 호출: `"방금 검색한 결과 다시 보여줘"` (follow-up 없음)

테스트가 잠그는 계약:

1. `actions_taken == ["load_web_search_record"]`
2. `reload_origin` exact-field 계약:
   - `provider == "web"`, `badge == "WEB"`, `label == "외부 웹 최신 확인"`
   - `kind == "assistant"`, `model is None`, `answer_mode == "latest_update"`
   - `verification_label == "기사 교차 확인"`, `source_roles == ["보조 기사"]`
3. negative 제외 계약: `self.assertNotIn("보조 커뮤니티", str(reload_origin["source_roles"]))`, `self.assertNotIn("brunch", second["response"]["text"])`
4. positive `source_paths` 계약: `hankyung`, `mk.co.kr` 포함 / `brunch` 미포함
5. `service.web_search_store.get_session_record(...)` 기반 stored `response_origin` exact-field 계약 (위와 동일 literal 세트)
6. history entry empty-meta branch: zero-count `claim_coverage_summary`, 빈 `claim_coverage_progress_summary`

noisy-community follow-up 테스트, non-noisy latest-update family, entity-card / dual-probe / zero-strong / actual-search family, session summary serializer, 브라우저/Playwright는 건드리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload` → `Ran 1 test in 0.024s OK`
- `git diff --check -- tests/test_web_app.py work/4/11` → whitespace 경고 없음
- 이 슬라이스는 service-only 계약 대조이고 browser-visible 계약을 건드리지 않으므로 `make e2e-test`는 과합니다. 신규 단일 테스트 실행으로 충분합니다.

## 남은 리스크

- noisy-community latest-update 쪽 initial 응답 단독에 대한 exact surface/stored 계약이 이 family에서 이미 유사하게 잡혀 있는지는 이번 라운드에서 재확인하지 않았습니다. 별도 audit 슬라이스에서 다룰 여지가 있습니다.
- entity-card family 외 다른 family (dual-probe / zero-strong / actual-search)의 natural-reload reload-only 경로 exact 계약은 이 라운드에서 확인하지 않았습니다.
- `session["web_search_history"]` 항목이 `response_origin` 객체를 노출하지 않는 구조 자체는 유지되었고, 추후 요약 serializer를 넓히게 되면 store-read 대신 history_entry에서 직접 검증하도록 정리할 여지가 있습니다.
- 저장소는 여전히 dirty 상태입니다 (`verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
