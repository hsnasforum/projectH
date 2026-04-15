## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-stored-record-remaining-response-origin-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-stored-record-remaining-response-origin-exact-service-bundle.md`가 주장한 noisy-community natural-reload follow-up chain의 persisted stored `response_origin` exactness가 실제 코드와 targeted 검증 결과에 부합하는지 truthfully 다시 확인해야 했습니다.
- 확인이 끝난 뒤에는 같은 history-card latest-update noisy-community family 안에서 남은 current-risk를 한 번에 닫는 다음 한 슬라이스만 남겨야 했습니다.

## 핵심 변경
- `tests/test_web_app.py`의 noisy-community natural-reload follow-up 2개 경로에 stored-record exact assertion이 실제로 존재함을 확인했습니다.
- first follow-up 경로는 `service.web_search_store.get_session_record("latest-noisy-nat-fu-session", record_id)`로 저장 레코드를 직접 읽고 `stored_origin["provider"]`, `badge`, `label`, `kind`, `model`, `answer_mode`, `verification_label`, `source_roles` exact literal을 잠그고 있습니다 (`tests/test_web_app.py:19639`, `tests/test_web_app.py:19653`).
- second follow-up 경로도 같은 stored exactness를 직접 잠그고 있습니다 (`tests/test_web_app.py:19736`, `tests/test_web_app.py:19750`).
- 이 접근이 필요한 이유도 현재 구현과 일치했습니다. `storage/web_search_store.py:274`의 `get_session_record(...)`는 전체 저장 레코드를 반환하지만, `storage/web_search_store.py:295`의 `list_session_record_summaries(...)`는 `answer_mode`·`verification_label`·`source_roles` 중심 summary만 노출하므로 full stored `response_origin` exactness는 session summary만으로 잠글 수 없습니다.
- 최신 `/work`까지 반영하면 noisy-community latest-update family에서 click-reload show-only/first/second follow-up과 natural-reload first/second follow-up의 surface + stored exactness는 모두 닫혔습니다. 반대로 `"방금 검색한 결과 다시 보여줘"`로 끝나는 noisy natural-reload show-only 경로는 현재 direct exact-field test가 없어 same-family user-visible gap으로 남아 있습니다. 그래서 다음 handoff는 `history-card latest-update noisy-community natural-reload reload-only exact service bundle`로 좁혔습니다.

## 검증
- 코드 대조:
  - `rg -n "latest_update_noisy_source_excluded_after_natural_reload|latest-noisy-nat|get_session_record\\(" tests/test_web_app.py`
  - `nl -ba tests/test_web_app.py | sed -n '19540,19760p'`
  - `rg -n "noisy_source_excluded_after|latest_update_noisy|noisy-community" tests/test_web_app.py`
  - `nl -ba tests/test_web_app.py | sed -n '8128,8475p'`
  - `nl -ba storage/web_search_store.py | sed -n '274,314p'`
- targeted 회귀:
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up`
  - 결과: `Ran 2 tests in 0.074s OK`
- 포맷 확인:
  - `git diff --check -- tests/test_web_app.py work/4/11`
  - 결과: 출력 없음
- 전체 `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드 범위가 service-test stored assertion truth check라 재실행하지 않았습니다.

## 남은 리스크
- noisy-community latest-update family에는 `"방금 검색한 결과 다시 보여줘"`로만 끝나는 natural-reload show-only 경로의 surface + stored exact-field 검증이 아직 없습니다.
- 그 reload-only 경로를 닫기 전까지는 noisy-community natural-reload의 직접 user-visible branch 하나가 exact-field coverage 밖에 남습니다.
- 작업 트리는 여전히 dirty 상태이므로 다음 구현 라운드는 기존 pending `/verify`, `/work`, 그리고 untracked `docs/projectH_pipeline_runtime_docs/`를 되돌리거나 정리하지 않고 지정된 테스트 범위만 좁게 수정해야 합니다.
