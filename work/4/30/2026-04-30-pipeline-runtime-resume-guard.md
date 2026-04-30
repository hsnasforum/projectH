# 2026-04-30 Pipeline runtime resume guard

## 변경 파일

- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/4/30/2026-04-30-pipeline-runtime-resume-guard.md`

## 사용 skill

- `security-gate`: runtime stop/restart와 PID 판정이 실제 프로세스 상태를 과장하지 않는지 점검하는 데 사용
- `release-check`: 변경 범위와 검증 범위를 좁게 정리하는 데 사용
- `work-log-closeout`: 구현 라운드 종료 기록과 실제 검증 결과 정리에 사용

## 변경 이유

- 런처 상태창에서는 Codex가 계속 working으로 보였지만, 실제 `status.json`의 Codex lane은 `READY`, `note=prompt_visible`, `progress_phase=work_closeout_written`였습니다.
- 표시 오판과 별개로 pipeline 재시작 경로도 `supervisor.pid`의 PID를 `os.kill(pid, 0)`만으로 live 판정하고 있었습니다.
- 좀비 프로세스는 `kill(pid, 0)`에 성공할 수 있어, supervisor가 종료된 뒤에도 stop/restart가 살아 있는 프로세스로 취급하는 재발 위험이 있었습니다.

## 핵심 변경

- `pipeline_runtime.cli._pid_is_zombie()`를 추가해 `/proc/<pid>/stat`의 process state가 `Z`인지 확인합니다.
- `_supervisor_running()`이 pidfile PID가 좀비이면 `None`을 반환하게 변경했습니다.
- `_reconcile_supervisors()`가 테스트와 실제 재시작 경로에서 같은 `proc_root` 기반 판정을 쓰도록 연결했습니다.
- `tests/test_pipeline_runtime_cli.py`에 좀비 pidfile은 live supervisor로 보지 않고, non-zombie pidfile은 기존처럼 유지하는 회귀 테스트를 추가했습니다.

## 실제 복구 확인

- `python3 -m pipeline_runtime.cli restart . --session aip-projectH` — PASS
- 새 run id: `20260430T021054Z-p73842`
- 새 supervisor pid: `73910`
- 새 watcher pid: `74135`
- 재시작 후 `python3 -m pipeline_runtime.cli status . --json` 기준:
  - `runtime_state=RUNNING`
  - `automation_health=ok`
  - `turn_state.state=VERIFY_ACTIVE`
  - `Claude` lane은 verification 수행 중
  - `Codex` lane은 실제 상태대로 `READY`, `note=prompt_visible`

## 검증

- `python3 -m py_compile pipeline_runtime/cli.py pipeline_gui/backend.py pipeline_gui/home_presenter.py pipeline_gui/home_controller.py pipeline_gui/app.py` — PASS
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.SupervisorCliTest.test_supervisor_running_ignores_zombie_pidfile_process tests.test_pipeline_runtime_cli.SupervisorCliTest.test_supervisor_running_keeps_non_zombie_pidfile_process tests.test_pipeline_runtime_cli.SupervisorCliTest.test_reconcile_supervisors_rewrites_pidfile_for_single_live_daemon` — PASS
- `python3 -m unittest -v tests.test_pipeline_runtime_cli` — PASS, 32 tests
- `python3 -m unittest -v tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_backend tests.test_controller_server` — PASS, 104 tests
- `git diff --check -- app/frontend/src/components/ReviewQueuePanel.tsx controller/js/cozy.js tests/test_controller_server.py pipeline_gui/backend.py pipeline_gui/home_presenter.py pipeline_gui/home_controller.py pipeline_gui/app.py tests/test_pipeline_gui_home_presenter.py pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/4/30/2026-04-30-controller-lane-state-truth.md work/4/30/2026-04-30-m110-review-queue-search-filter.md` — PASS

## 워크트리 정리

- `git worktree prune --verbose`로 `worktrees/projectH-pr43-zEKqK6`의 prunable gitdir metadata를 제거했습니다.
- `git worktree list --porcelain` 기준 남은 worktree는 `/home/xpdlqj/code/projectH` 하나입니다.

## 남은 리스크

- 이번 수정은 supervisor pidfile의 좀비 판정과 재시작 복구에 한정했습니다.
- stale compat control slot 파일 자체는 이번 라운드에서 삭제하지 않았습니다. 현재 active control은 `implement_handoff.md` seq `1490`이고 stale slot은 낮은 seq라 runtime active 결정에는 쓰이지 않습니다.
