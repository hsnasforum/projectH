# 2026-05-21 Pipeline runs dir auto cleanup

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-pipeline-runs-dir-auto-cleanup.md`

## 사용 skill

- `security-gate`: `.pipeline/runs/`의 로컬 런 기록 디렉터리를 자동 삭제하는 변경이라, current run 보존과 실패 시 fail-soft 동작을 우선 확인했습니다.
- `work-log-closeout`: 변경 파일, 검증 결과, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/runs/` 아래 오래된 런 디렉터리가 정리 로직 없이 계속 누적되어 런타임 상태 파일과 로그가 불필요하게 커지고 있었습니다.
- 자동 정리는 런타임 기동 시점에만 수행하고, 현재 런과 최신 런을 보존해 운영 중인 evidence/status 표면을 삭제하지 않도록 제한했습니다.

## 핵심 변경

- `RuntimeSupervisor._cleanup_old_runs()`를 추가했습니다.
  - `PIPELINE_RUNTIME_DISABLE_RUNS_CLEANUP`이 `1`, `true`, `yes`, `y`, `on`이면 정리를 건너뜁니다.
  - `PIPELINE_RUNTIME_KEEP_RECENT_RUNS`로 최신 보존 개수를 조정하며, 미설정/비정상/0 이하 값은 기본값 `10`으로 되돌립니다.
  - `self.run_id`, `current_run.json`의 `run_id`, timestamp prefix 기준 최신 N개 런 디렉터리를 보존합니다.
  - 삭제 성공분이 있을 때만 `runs_cleanup` 이벤트를 남기고, `deleted_run_ids`는 최대 20개로 제한합니다.
  - `shutil.rmtree()` 실패는 삼켜 다음 기동에서 재시도되도록 했습니다.
- `_launch_runtime()`에서 `_terminate_repo_watchers()` 다음, `_prepare_runtime_surfaces()` 전에 cleanup을 호출하도록 배치했습니다.
- 신규 회귀 테스트를 추가했습니다.
  - runtime launch 중 cleanup 호출 순서
  - current/self/latest run 보존과 cleanup 이벤트 기록
  - disable env 동작
  - 삭제 대상 없음일 때 이벤트 미기록
  - `rmtree` 실패 시 예외 없이 나머지 삭제 계속 진행

## 검증

- 수정 전 실패 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_launch_runtime_runs_cleanup_before_surface_prep_and_spawn tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_cleanup_old_runs_keeps_current_and_recent_and_records_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_cleanup_old_runs_disable_env_skips_deletion_and_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_cleanup_old_runs_does_not_emit_event_when_nothing_deleted tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_cleanup_old_runs_ignores_rmtree_failure_and_continues`
  - 결과: `_cleanup_old_runs`가 없어 5개 테스트가 실패했습니다.
- 수정 후 focused 확인:
  - 같은 5개 테스트
  - `Ran 5 tests in 0.028s` / `OK`.
- 컴파일 확인:
  - `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 통과했습니다.
- 전체 supervisor 테스트 확인:
  - `python3 -m unittest tests.test_pipeline_runtime_supervisor -v`
  - `Ran 193 tests in 1.105s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py work/5/21`
  - closeout 작성 전후 모두 통과했습니다.

## 남은 리스크

- 실제 `.pipeline/runs/`의 기존 334개 디렉터리에 대해 live runtime 기동으로 정리되는지는 실행하지 않았습니다.
- Playwright, E2E, live runtime start 검증은 요청 범위 밖이라 실행하지 않았습니다.
- 이번 정리는 `.pipeline/runs/`에만 적용되며 `.pipeline/logs/`, `.pipeline/state/`, `.pipeline/manifests/`는 건드리지 않았습니다.
- commit, push, PR publish, merge는 수행하지 않았습니다.
