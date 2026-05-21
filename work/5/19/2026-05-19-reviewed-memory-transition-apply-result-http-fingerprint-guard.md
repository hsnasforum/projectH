# 2026-05-19 reviewed-memory transition apply/result HTTP fingerprint guard

## 변경 파일

- `tests/test_web_app.py`
- `work/5/19/2026-05-19-reviewed-memory-transition-apply-result-http-fingerprint-guard.md`
- 기존 dirty context로 함께 검증한 파일
  - `app/web.py`
  - `app/handlers/reviewed_memory.py`
  - `.pipeline/implement_handoff.md`

## 사용 skill

- `onboard-lite`: 활성 handoff #1976, 현재 dirty context, 직접 관련 테스트/핸들러 경계를 빠르게 확인하기 위해 사용했습니다.
- `finalize-lite`: 구현 라운드 종료 전 검증 정직성, doc-sync 필요 여부, `/work` closeout 준비 상태를 확인하기 위해 사용했습니다.
- `work-log-closeout`: handoff #1976 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리하기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1976`이 reviewed-memory apply/result transition mutation도 mismatched `aggregate_fingerprint`를 HTTP 경계에서 거부하고 저장 상태를 변경하지 않는지 회귀 테스트로 고정하라고 지시했습니다.
- 기존 HTTP wrong-fingerprint regression은 stop, reverse, conflict-check mutation action을 중심으로 되어 있었고, `/api/aggregate-transition-apply` 및 `/api/aggregate-transition-result`에 대한 같은 수준의 HTTP 회귀 테스트가 비어 있었습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `tests/test_web_app.py`에 `test_reviewed_memory_transition_http_apply_result_reject_mismatched_aggregate_fingerprint`를 추가했습니다.
- emitted transition record를 직접 seed한 뒤 wrong fingerprint로 `/api/aggregate-transition-apply`를 호출해 `404`, `ok: false`, `error` 응답과 함께 `record_stage = emitted_record_only_not_applied`가 유지되는지 검증했습니다.
- correct fingerprint로 `/api/aggregate-transition-apply`를 통과시켜 `record_stage = applied_pending_result`까지 진행시킨 뒤, wrong fingerprint로 `/api/aggregate-transition-result`를 호출해 `404`, `ok: false`, `error` 응답과 상태 불변을 검증했습니다.
- wrong-fingerprint apply/result 요청이 `applied_at`, `result_at`, `apply_result`, active effect를 부적절하게 추가하지 않는지 확인했습니다.
- focused regression이 통과했기 때문에 `app/web.py`, `app/handlers/reviewed_memory.py`, UI, Playwright, serializer, docs는 변경하지 않았습니다.

## 검증

- `python3 -m py_compile app/web.py app/handlers/reviewed_memory.py tests/test_web_app.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_apply_result_reject_mismatched_aggregate_fingerprint tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_actions_reject_mismatched_aggregate_fingerprint`
  - 통과: `Ran 2 tests`, `OK`.
- `rg -n "test_reviewed_memory_transition_http_apply_result_reject_mismatched_aggregate_fingerprint|aggregate-transition-apply|aggregate-transition-result|wrong_fingerprint|mismatched_aggregate_fingerprint" tests/test_web_app.py app/web.py app/handlers/reviewed_memory.py`
  - 통과: 신규 test, 기존 apply/result route dispatch, wrong-fingerprint regression marker를 확인했습니다.
- `git diff --check -- app/web.py app/handlers/reviewed_memory.py tests/test_web_app.py work/5/19/2026-05-19-reviewed-memory-transition-apply-result-http-fingerprint-guard.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 focused HTTP regression 추가 범위입니다.
- 전체 unittest, 전체 Playwright suite, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
