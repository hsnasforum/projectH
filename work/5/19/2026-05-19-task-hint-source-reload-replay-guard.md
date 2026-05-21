# 2026-05-19 task hint source reload replay guard

## 변경 파일

- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/19/2026-05-19-task-hint-source-reload-replay-guard.md`

## 사용 skill

- `work-log-closeout`: handoff #1983 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1983`이 live runtime reload evidence에 의존하지 않는 deterministic supervisor replay를 요구했습니다.
- 이전 `/work`는 `local_runtime_reload_env_held`를 남겼고, 최신 `/verify`는 dispatch surface가 `RUNNING/ok/continue`였지만 release/full-smoke readiness는 주장하지 않았습니다.
- handoff #1982의 required unittest 이름 하나가 현재 repo 테스트명과 불일치했으므로, old typo alias를 추가하지 않고 현재 테스트명과 새 replay로 guard를 보강했습니다.

## 핵심 변경

- `RuntimeSupervisorTest`에 `test_source_reload_self_verify_task_hint_identity_survives_watcher_restart`를 추가했습니다.
- 새 테스트는 implement/verify owner가 모두 `Codex`인 self-verify profile에서 live watcher owner pointer를 구성하고, source-aware watcher restart helper를 mock side effect로 실행합니다.
- `_write_status()`가 active implement control #1983과 active self-verify round를 함께 관찰한 뒤, Codex task hint가 `ctrl-1983` / `seq-1983`로 덮이지 않고 verify round의 `job_id` / `dispatch_id`를 유지하는지 확인합니다.
- 새 테스트는 runtime status가 `RUNNING`이고 `watcher_self_restart_started` / `watcher_self_restart_completed` event가 기록되는지도 확인합니다.
- 이번 replay는 test-only 변경으로 통과했으므로 `pipeline_runtime/supervisor.py` production code는 수정하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `d80283a1d62612d5a2f21c3a116d2563532f0cbd1117b0ac168f77b2af702767`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_implement_lane_ignores_closed_verify_round_identity tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_self_verify_round_identity_takes_precedence tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_source_change_restarts_watcher_without_operator_decision tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_source_reload_self_verify_task_hint_identity_survives_watcher_restart`
  - 결과: PASS. 5개 테스트 통과.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py pipeline_runtime/supervisor.py work/5/19/2026-05-19-task-hint-source-reload-replay-guard.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- 이번 라운드는 deterministic unit replay guard입니다. live `pipeline_runtime.cli start`, `status --json`, `doctor --json`, tmux, controller startup, Playwright, `make e2e-test`, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- 작업트리에는 handoff 이전부터 reviewed-memory, runtime, docs, tests 계열의 넓은 dirty 변경이 남아 있습니다. 이번 handoff와 무관한 변경은 되돌리지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
