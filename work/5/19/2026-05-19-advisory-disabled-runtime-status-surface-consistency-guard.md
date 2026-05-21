# 2026-05-19 advisory disabled runtime status surface consistency guard

## 변경 파일

- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- 기존 dirty bundle 유지 및 검증 대상
  - `pipeline_runtime/automation_health.py`
  - `pipeline_runtime/supervisor.py`
  - `watcher_prompt_assembly.py`
  - `tests/test_pipeline_runtime_automation_health.py`
  - `tests/test_pipeline_runtime_supervisor.py`
  - `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/19/2026-05-19-advisory-disabled-runtime-status-surface-consistency-guard.md`

## 사용 skill

- `work-log-closeout`: 실제 수정 파일, 실행한 검증, publication hold 및 잔여 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1961`이 `ADVISORY_ENABLED=false` 상태에서도 dispatcher surface가 `automation_next_action: advisory_followup`을 보고한 경로를 좁혀 수정하라고 지시했습니다.
- 기존 `pipeline_runtime.supervisor` status writer는 `runtime_controls`를 포함하도록 보강되어 있었지만, watcher runtime exporter가 같은 status 파일을 쓸 때는 `runtime_controls`를 빠뜨려 `derive_automation_health()`가 advisory enabled 기본값으로 `stale_control_advisory -> advisory_followup`을 계산할 수 있었습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `watcher_core._write_runtime_status()`가 status payload에 `runtime_controls`를 함께 쓰도록 했습니다.
- `WatcherPromptAssemblyTest.test_verify_prompt_context_includes_runtime_dispatch_surface`가 advisory-disabled profile에서 stale advisory grace 상태를 직접 status로 내보내고, prompt의 `RUNTIME_STATUS_AT_DISPATCH`가 `automation_next_action: verify_followup`을 표시하는지 검증하도록 확장했습니다.
- `.pipeline/README.md`의 runtime status 계약을 supervisor 단독이 아니라 watcher runtime exporter도 같은 `runtime_controls`와 derived health/action surface를 써야 한다는 설명으로 맞췄습니다.
- 기존 `automation_health` / supervisor / operator retriage 회귀 테스트는 그대로 유지했고, watcher exporter가 같은 helper 입력을 제공하도록 경계를 맞췄습니다.

## 검증

- `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.AutomationHealthTest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_advisory_disabled_operator_candidate_routes_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_next_direction_after_launcher_close tests.test_watcher_core.WatcherPromptAssemblyTest.test_verify_prompt_context_includes_runtime_dispatch_surface tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_advisory_disabled_returns_to_verify`
  - 통과: `Ran 11 tests ... OK`.

## 남은 리스크

- Playwright/E2E, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다. 이번 수정은 watcher status exporter와 단위 회귀 테스트 범위에 한정되어 socket/browser 검증으로 넓히지 않았습니다.
- 현재 실행 중인 watcher/supervisor 프로세스가 이미 import한 오래된 코드로 status를 쓰는 경우, 다음 runtime self-restart 또는 재시작 전까지 live `status.json`에는 이전 surface가 잠시 남을 수 있습니다. 이번 변경은 다음 code load 이후 같은 advisory-disabled profile에서 `runtime_controls`가 status에 포함되도록 하는 로컬 코드 수정입니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
