# 2026-05-19 reviewed-memory transition fingerprint guard

## 변경 파일

- `app/handlers/reviewed_memory.py`
- `tests/test_web_app.py`
- `work/5/19/2026-05-19-reviewed-memory-transition-fingerprint-guard.md`

## 사용 skill

- `work-log-closeout`: handoff #1969 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1969`가 reviewed-memory lifecycle의 `stop_apply_aggregate_transition`, `reverse_aggregate_transition`, `check_aggregate_conflict_visibility` 경로에서 `canonical_transition_id`뿐 아니라 요청된 `aggregate_fingerprint`도 transition record identity와 함께 확인하라고 지시했습니다.
- 기존 `apply_aggregate_transition` / `confirm_aggregate_transition_result`는 이미 `aggregate_identity_ref.normalized_delta_fingerprint`를 요청 fingerprint와 대조했지만, 이후 lifecycle mutation 경로는 transition id만 맞으면 진행될 수 있었습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `ReviewedMemoryHandlerMixin._find_aggregate_transition_record`를 추가해 transition record 조회 기준을 `canonical_transition_id`와 `aggregate_fingerprint`의 결합 identity로 통일했습니다.
- `apply_aggregate_transition`, `confirm_aggregate_transition_result`, `stop_apply_aggregate_transition`, `reverse_aggregate_transition`, `check_aggregate_conflict_visibility`가 같은 helper를 사용하도록 정리했습니다.
- wrong `aggregate_fingerprint`가 active reviewed-memory effect를 stop하지 못하고 원본 active state를 보존하는지 검증하는 회귀 테스트를 추가했습니다.
- wrong `aggregate_fingerprint`가 stopped transition을 reverse하지 못하고 stopped/result_stage 상태를 보존하는지 검증했습니다.
- wrong `aggregate_fingerprint`가 reversed transition에 conflict-visibility record를 만들지 못하는지 검증했습니다.

## 검증

- `python3 -m py_compile app/handlers/reviewed_memory.py tests/test_web_app.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_actions_reject_mismatched_aggregate_fingerprint tests.test_web_app.WebAppServiceTest.test_check_aggregate_conflict_visibility_creates_separate_record_with_key_fields tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_returns_ok`
  - 통과: `Ran 5 tests ... OK`.
- `git diff --check -- app/handlers/reviewed_memory.py tests/test_web_app.py work/5/19/2026-05-19-reviewed-memory-transition-fingerprint-guard.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 reviewed-memory lifecycle handler와 focused server-side tests 범위만 검증했습니다.
- Playwright/E2E, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
