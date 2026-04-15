## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-stored-record-remaining-response-origin-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-stored-record-remaining-response-origin-exact-service-bundle.md`가 주장한 noisy-community click-reload stored `response_origin` exactness가 실제 코드와 targeted 검증 결과에 부합하는지 truthfully 다시 확인해야 했습니다.
- 확인이 끝난 뒤에는 같은 history-card latest-update family 안에서 가장 가까운 current-risk 한 개만 다음 Claude 구현 슬라이스로 남겨야 했습니다.

## 핵심 변경
- `tests/test_web_app.py`의 noisy-community click-reload 3개 경로에 stored-record exact assertion이 실제로 존재함을 확인했습니다.
- show-only reload 경로는 `service.web_search_store.get_session_record(...)`로 저장 레코드를 직접 읽고 `stored_origin["provider"]`, `badge`, `label`, `kind`, `model`, `answer_mode`, `verification_label`, `source_roles` exact literal을 잠그고 있습니다 (`tests/test_web_app.py:11833`, `tests/test_web_app.py:11847`).
- click-reload first follow-up 경로도 같은 stored exactness를 직접 잠그고 있습니다 (`tests/test_web_app.py:19793`, `tests/test_web_app.py:19807`).
- click-reload second follow-up 경로도 같은 stored exactness를 직접 잠그고 있습니다 (`tests/test_web_app.py:19889`, `tests/test_web_app.py:19903`).
- 이 접근이 필요한 이유도 현재 구현과 일치했습니다. `storage/web_search_store.py:274`의 `get_session_record(...)`는 전체 저장 레코드를 반환하지만, `storage/web_search_store.py:295`의 `list_session_record_summaries(...)`는 `answer_mode`·`verification_label`·`source_roles` 중심 summary만 노출하므로 full `response_origin` exactness는 session summary만으로 잠글 수 없습니다.
- 다음 handoff는 `history-card latest-update noisy-community natural-reload remaining response-origin exact service bundle`로 좁혔습니다. noisy-community click-reload path는 surface + stored가 닫혔고, 현재 가장 가까운 same-family risk는 natural-reload follow-up 2개 테스트가 아직 `provider`·`label`·`kind`·`model` exactness를 직접 잠그지 않는 점입니다 (`tests/test_web_app.py:19639`, `tests/test_web_app.py:19649`, `tests/test_web_app.py:19717`, `tests/test_web_app.py:19727`).

## 검증
- 코드 대조:
  - `nl -ba tests/test_web_app.py | sed -n '11810,11860p'`
  - `nl -ba tests/test_web_app.py | sed -n '19768,19818p'`
  - `nl -ba tests/test_web_app.py | sed -n '19846,19912p'`
  - `nl -ba tests/test_web_app.py | sed -n '19618,19740p'`
  - `nl -ba storage/web_search_store.py | sed -n '270,314p'`
- targeted 회귀:
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up`
  - 결과: `Ran 3 tests in 0.095s OK`
- 포맷 확인:
  - `git diff --check -- tests/test_web_app.py work/4/11`
  - 결과: 출력 없음
- 전체 `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드 범위가 service-test assertion truth check라 재실행하지 않았습니다.

## 남은 리스크
- noisy-community natural-reload follow-up / second-follow-up 경로는 아직 response surface에서 `provider`·`label`·`kind`·`model` exactness가 열려 있습니다.
- noisy-community natural-reload stored-record exactness는 이번 라운드 범위 밖이라 아직 직접 잠기지 않았습니다.
- 작업 트리는 여전히 dirty 상태이므로 다음 구현 라운드는 기존 변경을 되돌리지 않고 지정된 테스트 범위만 좁게 수정해야 합니다.
