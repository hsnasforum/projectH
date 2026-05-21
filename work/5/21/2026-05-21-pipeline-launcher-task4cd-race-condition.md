# 2026-05-21 Pipeline launcher Task 4-C/D race condition

## 변경 파일

- `pipeline_runtime/cli.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-pipeline-launcher-task4cd-race-condition.md`

## 사용 skill

- `security-gate`: supervisor start 직렬화와 watcher run_id 상속 검증은 runtime control과 로컬 상태 파일 경계에 닿으므로, 실패 시 조용히 안전 종료하고 기존 operator boundary를 넓히지 않는지 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실패 확인, 검증 결과, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `docs/superpowers/plans/2026-05-21-pipeline-launcher-bugfixes.md`의 Task 4-C(P5)와 Task 4-D(P7)만 실행했습니다.
- `verify/5/21/2026-05-21-pipeline-launcher-task3-perf-caching.md`에서 남은 미수정 이슈가 P5/P7 두 건으로 확인되어 있었습니다.
- 이번 변경으로 계획서의 18개 이슈 중 앞선 라운드에서 처리된 항목을 제외한 마지막 경쟁 조건 2건을 닫았습니다.

## 핵심 변경

- P5: `_spawn_supervisor()` 진입부에 `.pipeline/.supervisor-start.lock` 파일 기반 `fcntl.flock(..., LOCK_EX | LOCK_NB)` 잠금을 추가했습니다.
- P5: lock이 이미 잡혀 있으면 다른 start가 진행 중인 정상 상황으로 보고 0을 반환하며, preflight나 daemon spawn까지 내려가지 않게 했습니다.
- P5: 함수 종료 시 `finally`에서 `LOCK_UN`과 fd close를 수행하도록 했습니다. lock 파일 open 자체가 실패하면 기존 경로로 진행합니다.
- P7: `_inherited_run_id_from_live_watcher()`가 watcher pid와 fingerprint를 확인한 뒤, candidate run_id를 반환하기 직전에 live watcher pid를 다시 확인하게 했습니다.
- P5/P7 회귀 테스트를 추가했습니다. P5 테스트는 두 번째 실제 `flock(... LOCK_NB)` 호출이 `BlockingIOError`를 발생시키는 것을 직접 assert합니다.

## 검증

- 수정 전 실패 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_cli.SupervisorCliTest.test_spawn_supervisor_returns_success_when_start_lock_is_held tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_watcher_disappears_after_fingerprint`
  - 결과: 두 테스트 모두 실패했습니다. start lock이 잡힌 상태에서도 `_spawn_supervisor()`가 preflight까지 내려가 1을 반환했고, fingerprint 확인 뒤 watcher가 사라지는 케이스에서 stale run_id를 상속했습니다.
- 수정 후 focused 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_cli.SupervisorCliTest.test_spawn_supervisor_returns_success_when_start_lock_is_held tests.test_pipeline_runtime_cli.SupervisorCliTest.test_spawn_supervisor_blocks_when_start_preflight_fails tests.test_pipeline_runtime_cli.SupervisorCliTest.test_spawn_supervisor_keeps_live_daemon_when_runtime_source_is_not_newer tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_watcher_disappears_after_fingerprint tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_after_watcher_exporter_writes_pointer tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_mismatches_live_watcher`
  - `Ran 6 tests in 0.032s` / `OK`.
- 지정 컴파일 확인:
  - `python3 -m py_compile pipeline_runtime/cli.py pipeline_runtime/supervisor.py`
  - 통과했습니다.
- 지정 전체 테스트 확인:
  - `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor -v`
  - `Ran 226 tests in 1.187s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/cli.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_supervisor.py work/5/21`
  - closeout 작성 전후 모두 통과했습니다.

## 남은 리스크

- Playwright, E2E, live runtime start/stop 검증은 요청 범위 밖이라 실행하지 않았습니다.
- 이번 라운드는 Task 4-C/D만 포함했고, Task 1~3 및 Task 4-A/B 변경은 앞선 라운드의 dirty 상태로 유지했습니다.
- 작업 시작 시점부터 대상 파일 일부는 기존 dirty 상태였고, 이 기록은 P5/P7 변경만 설명합니다.
- commit, push, PR publish, merge, release는 수행하지 않았습니다.
