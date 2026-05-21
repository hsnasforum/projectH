# 2026-05-20 active verify round status surface aggregate unit guard

## 변경 파일

- `work/5/20/2026-05-20-active-verify-round-status-surface-aggregate-unit-guard.md`

## 사용 skill

- `finalize-lite`: aggregate unit guard 결과와 문서/브라우저 검증 확대 필요 여부를 점검하기 위해 사용했습니다.
- `work-log-closeout`: 실제 실행한 명령, 결과, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1999`가 active verify round status surface family의 bounded aggregate unit guard를 요구했습니다.
- 직전 focused exporter regression은 통과했지만, helper-level automation health 테스트와 supervisor lane/status 테스트를 한 번에 묶은 검증은 아직 남아 있었습니다.
- 이번 라운드는 실패가 없으면 source edit 없이 aggregate 검증과 `/work` closeout만 남기는 범위였습니다.

## 핵심 변경

- source/test 파일은 이번 라운드에서 수정하지 않았습니다.
- `pipeline_runtime/automation_health.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_automation_health.py`, `tests/test_pipeline_runtime_supervisor.py`를 대상으로 compile과 aggregate unit guard를 실행했습니다.
- aggregate unit guard는 `IDLE + active VERIFY_PENDING|VERIFYING`이 `ok/continue`로 숨겨지지 않고 `recovering/dispatch_stall/retrying`으로 표면화되는 helper/supervisor 경로와 관련 lane-note surface를 함께 확인했습니다.
- 모든 handoff 지정 검증이 통과해 code change는 필요하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `706e82bd6c9364d272b77685e4bb53d9a44baf34d7c603801fde2b5dd470e2bc`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verify_pending_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verifying_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_current_work_verify_round_is_not_misread_as_idle_release tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_idle_active_verify_round_as_recovering tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_requeued_dispatch_wait_as_recovering tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_idle_verify_round_keeps_codex_ready_even_if_round_is_running tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_prompt_visible_verify_pending_keeps_codex_working_while_task_is_accepted tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_dispatch_stall_active_round_surfaces_machine_note_on_codex_lane`
  - 결과: PASS. `Ran 8 tests in 0.023s`, `OK`.
- `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- 이번 라운드는 bounded aggregate unit guard만 수행했습니다. full `tests.test_pipeline_runtime_supervisor`, full `tests.test_pipeline_runtime_automation_health`, full runtime/watcher suite, controller startup, Playwright/e2e, long soak는 실행하지 않았습니다.
- `pipeline_runtime/supervisor.py`, `pipeline_runtime/automation_health.py`, `tests/test_pipeline_runtime_supervisor.py`, `tests/test_pipeline_runtime_automation_health.py`에는 이번 라운드 이전부터 존재하던 미커밋 변경이 섞여 있습니다. 이번 라운드에서는 source/test를 수정하지 않았고 기존 변경은 되돌리지 않았습니다.
- dispatcher surface가 이전에 `IDLE + active VERIFY_PENDING`을 `ok/continue`로 보여 준 live 상태 자체를 재현/soak하지는 않았습니다. 이번 검증은 local unit guard 범위입니다.
