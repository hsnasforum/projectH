# 2026-05-19 task hint source reload closed round replay guard

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/19/2026-05-19-task-hint-source-reload-closed-round-replay-guard.md`

## 사용 skill

- `work-log-closeout`: handoff #1984 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1984`가 source-aware watcher reload 뒤 active implement control이 stale closed verify round identity를 재사용하지 않는 companion replay/fix를 요구했습니다.
- handoff #1983은 active self-verify round precedence를 deterministic replay로 고정했지만, 반대 경계인 active implement control + stale closed verify round 조합은 아직 source-reload replay로 묶이지 않았습니다.
- 새 replay를 먼저 실행하자 Codex task hint `control_seq`가 stale verify round의 `1983`으로 남는 실패가 재현됐습니다.

## 핵심 변경

- `tests/test_pipeline_runtime_supervisor.py`에 `test_source_reload_implement_task_hint_ignores_closed_verify_round_after_watcher_restart`를 추가했습니다.
- 새 테스트는 implement/verify owner가 모두 `Codex`인 profile에서 live watcher owner pointer를 구성하고, source-aware watcher restart helper를 mock side effect로 실행합니다.
- stale closed verify round와 matching old receipt가 남아 있어도 active implement control #1984의 task hint가 `job_id=ctrl-1984`, `dispatch_id=seq-1984`, `control_seq=1984`를 쓰는지 확인합니다.
- `pipeline_runtime/supervisor.py`의 task-hint identity 선택에서 verify round identity 사용 조건을 live verify round state(`VERIFY_PENDING`, `VERIFYING`)로 좁혔습니다.
- active self-verify round는 verify identity를 유지하고, active implement control은 stale closed verify identity를 재사용하지 않도록 같은 family 양쪽 replay가 함께 통과합니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `18291bf442b031bd0bddb720674af19760a4fbd7fc6bb0849c4252ffa80f8ebc`와 일치했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_source_reload_implement_task_hint_ignores_closed_verify_round_after_watcher_restart`
  - 결과: FAIL. production 수정 전 `AssertionError: 1983 != 1984`로 stale closed verify round identity 재사용 문제가 재현됐습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_implement_lane_ignores_closed_verify_round_identity tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_self_verify_round_identity_takes_precedence tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_source_reload_self_verify_task_hint_identity_survives_watcher_restart tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_source_reload_implement_task_hint_ignores_closed_verify_round_after_watcher_restart`
  - 결과: PASS. 4개 테스트 통과.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py pipeline_runtime/supervisor.py work/5/19/2026-05-19-task-hint-source-reload-closed-round-replay-guard.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- 이번 라운드는 deterministic unit replay와 focused production fix입니다. live `pipeline_runtime.cli start`, `status --json`, `doctor --json`, tmux, controller startup, Playwright, `make e2e-test`, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- 작업트리에는 handoff 이전부터 reviewed-memory, runtime, docs, tests 계열의 넓은 dirty 변경이 남아 있습니다. 이번 handoff와 무관한 변경은 되돌리지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
