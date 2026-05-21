# 2026-05-19 reviewed-memory transition HTTP fingerprint guard

## 변경 파일

- `tests/test_web_app.py`
- `work/5/19/2026-05-19-reviewed-memory-transition-http-fingerprint-guard.md`
- 검증 대상 기존 dirty 파일
  - `app/handlers/reviewed_memory.py`
- `app/web.py`는 검증 대상이었지만 수정하지 않았습니다.

## 사용 skill

- `work-log-closeout`: handoff #1970 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1970`이 reviewed-memory transition wrong-fingerprint guard를 local HTTP handler 경계에서도 확인하라고 지시했습니다.
- 직전 service-layer guard는 `stop_apply_aggregate_transition`, `reverse_aggregate_transition`, `check_aggregate_conflict_visibility` 직접 호출에서 `aggregate_fingerprint`와 `canonical_transition_id` 결합 identity를 확인했습니다.
- 이번 라운드는 같은 mutation이 `/api/aggregate-transition-stop`, `/api/aggregate-transition-reverse`, `/api/aggregate-transition-conflict-check` endpoint를 통해 호출될 때도 wrong fingerprint 요청이 404로 실패하고 session state를 바꾸지 않는지 확인했습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `tests/test_web_app.py`에 `test_reviewed_memory_transition_http_actions_reject_mismatched_aggregate_fingerprint`를 추가했습니다.
- 새 테스트는 local HTTP server를 통해 wrong `aggregate_fingerprint` stop 요청이 active reviewed-memory transition/effect를 변경하지 않는지 확인합니다.
- 같은 테스트에서 wrong `aggregate_fingerprint` reverse 요청이 stopped transition을 변경하지 않는지 확인합니다.
- 같은 테스트에서 wrong `aggregate_fingerprint` conflict-check 요청이 reversed transition에 conflict-visibility record를 append하지 않는지 확인합니다.
- handler-level evidence가 기존 service guard 위에서 통과해 `app/web.py`와 `app/handlers/reviewed_memory.py` 추가 수정은 하지 않았습니다.

## 검증

- `python3 -m py_compile app/web.py app/handlers/reviewed_memory.py tests/test_web_app.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_actions_reject_mismatched_aggregate_fingerprint tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_actions_reject_mismatched_aggregate_fingerprint tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_returns_ok`
  - 통과: `Ran 5 tests ... OK`.
- `git diff --check -- app/web.py app/handlers/reviewed_memory.py tests/test_web_app.py work/5/19/2026-05-19-reviewed-memory-transition-http-fingerprint-guard.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 reviewed-memory transition HTTP handler와 focused server-side tests 범위만 검증했습니다.
- Playwright/E2E, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
