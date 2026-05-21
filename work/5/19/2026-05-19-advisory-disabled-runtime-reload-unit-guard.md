# 2026-05-19 advisory disabled runtime reload unit guard

## 변경 파일

- `work/5/19/2026-05-19-advisory-disabled-runtime-reload-unit-guard.md`
- 검증 대상 기존 dirty/runtime bundle
  - `pipeline_runtime/cli.py`
  - `pipeline_runtime/supervisor.py`
  - `watcher_core.py`
  - `tests/test_pipeline_runtime_cli.py`
  - `tests/test_pipeline_runtime_supervisor.py`
  - `.pipeline/README.md`
  - `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- 이번 라운드에서는 source/test/docs 파일을 수정하지 않았습니다.

## 사용 skill

- `work-log-closeout`: handoff #1962의 focused reload guard 결과, 실제 검증 명령, publication hold 상태, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1962`가 최신 watcher runtime status exporter 수정 뒤, 이미 실행 중인 watcher/supervisor가 새 코드를 import하기 전까지의 잔여 리스크를 source-reload 단위 증거로 닫으라고 지시했습니다.
- 이 라운드는 live runtime restart가 아니라 기존 CLI/supervisor reload safety net을 focused unit test로 확인하는 범위였습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `pipeline_runtime.cli._runtime_source_newer_than_supervisor_pidfile(...)`가 `watcher_core.py` source freshness를 reload 조건으로 감지하는 단위 테스트를 재확인했습니다.
- live supervisor spawn path가 runtime source 변경 시 기존 daemon을 stop 후 새 daemon으로 교체하는 단위 테스트를 재확인했습니다.
- `RuntimeSupervisor._maybe_restart_watcher_for_source_change()`가 watcher source 변경 시 experimental watcher를 operator decision 없이 self-restart하는 단위 테스트를 재확인했습니다.
- focused unit evidence가 모두 통과해 source/test/docs 수정은 하지 않았습니다.

## 검증

- `python3 -m py_compile pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_supervisor.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.SupervisorCliTest.test_runtime_source_newer_than_supervisor_pidfile_requests_reload tests.test_pipeline_runtime_cli.SupervisorCliTest.test_spawn_supervisor_replaces_live_daemon_when_runtime_source_changed tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_source_change_restarts_watcher_without_operator_decision`
  - 통과: `Ran 3 tests ... OK`.
- `git diff --check -- pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-advisory-disabled-runtime-reload-unit-guard.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.
- `git status --short -- pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-advisory-disabled-runtime-reload-unit-guard.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - source-reload guard 관련 기존 dirty 파일과 이번 `/work` closeout 추가 상태를 확인했습니다.

## 남은 리스크

- Playwright/E2E, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다. handoff #1962가 socket/tmux-dependent live restart 대신 focused unit evidence를 요구했기 때문입니다.
- 이번 라운드는 release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
