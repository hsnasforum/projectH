# 2026-05-12 Pipeline launcher stale active_round surface

## 변경 파일

- `.pipeline/README.md`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `watcher_dispatch.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md`

## 사용 skill

- `security-gate`: 런처 status, task hint, health surface 변경이 로컬 runtime 판단에만 머물고 승인/게시/merge 경계를 넓히지 않는지 확인했습니다.
- `doc-sync`: no-silent-stall runtime 계약을 `.pipeline/README.md`에 현재 구현과 맞췄습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.
- `release-check`: handoff 전 테스트, 문서 동기화, 미실행 범위, live 확인 필요성을 점검했습니다.

## 변경 이유

- 최신 `/work`와 matching `/verify`가 이미 있는데도 오래된 verify job이 public `active_round=VERIFYING`처럼 남으면 controller/browser 소비자가 현재 검증이 계속 진행 중이라고 오해할 수 있습니다.
- 이번 live stall에서는 `CONTROL_SEQ 1621`이 active implement로 남았지만 Codex lane이 `READY`, note `closed`로 돌아왔고 health가 `ok/continue`였습니다. 이 상태도 active implement가 실제로 멈춘 신호로 표면화해야 합니다.

## 핵심 변경

- `RuntimeSupervisor._write_status()`에서 artifacts를 active lane/task hint 계산 전에 만들고, 최신 work가 matching verify로 닫힌 duplicate idle 상태라면 오래된 `VERIFY_PENDING`/`VERIFYING`/`RECEIPT_PENDING` active round를 public status에서 suppress하도록 했습니다.
- stale active round suppress 이후의 active lane, task hint, lane status가 suppress된 `active_round` 기준으로 다시 계산되게 정리했습니다.
- active implement lane이 장시간 `READY/closed` 상태일 때도 기존 `implement_active_idle` health로 분류되도록 `automation_health.py`의 active implement ready 판단을 확장했습니다.
- Codex pane에 stale `[Pasted Content ...]`가 남은 pending 재시도도 defer하지 않고 replacement 경로를 타게 했으며, Codex dispatch 직전 stale pasted prompt를 `C-c` + `C-u`로 정리한 뒤 새 prompt를 넣도록 했습니다.
- Codex TUI가 paste 직후 첫 `Enter`를 놓쳐 prompt가 남는 경우 같은 prompt를 다시 붙이지 않고 `Enter`만 1회 재시도하도록 했습니다.
- supervisor 회귀에 “최신 work/verify는 닫혔고 오래된 verify job만 남은 duplicate idle” 시나리오를 추가했습니다.
- automation health 회귀에 active implement lane `READY/closed`가 `attention / implement_active_idle / retrying`으로 표면화되는지 추가했고, watcher 회귀에 stale pasted prompt replacement와 Enter retry를 추가했습니다.
- `.pipeline/README.md`의 no-silent-stall 계약에 stale active round suppression과 `READY/closed` implement idle 표면화를 반영했습니다.

## 검증

- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_active_implement_lane_closed_too_long_is_not_silent_ok tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_active_implement_lane_ready_too_long_is_not_silent_ok tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_suppresses_stale_active_round_after_latest_work_verified tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_prefers_current_control_seq_match tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_prefers_live_verify_over_stale_real_job tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_duplicate_handoff_verify_followup_progress`
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest`
- PASS: `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest tests.test_watcher_core.CodexDispatchConfirmationTest`
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest tests.test_watcher_core`
- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py && git diff --check -- .pipeline/README.md pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_dispatch.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py && git diff --check -- .pipeline/README.md pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_dispatch.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py work/5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md`
- LIVE: `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach` 후 status에서 최신 work가 verify 대상 `VERIFY_PENDING`으로 잡히는 것을 확인했습니다. 이후 live Codex pane에서 stale pasted prompt가 submit되지 않는 현상을 확인했고, 수동 `Enter` 1회로 제출되는 것을 관찰해 watcher dispatch에 Enter retry를 추가했습니다.
- LIVE: Enter retry 적용 후 `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`를 다시 실행했습니다. 이후 status에서 Codex verify dispatch가 `TASK_ACCEPTED`/`TASK_DONE`까지 진행했고, matching `/verify` 작성 후 `active_round.state=CLOSED`, `artifacts.latest_verify.path=5/12/2026-05-12-pipeline-launcher-stale-active-round-surface.md`, 다음 control `.pipeline/advisory_request.md CONTROL_SEQ 1622`가 active가 된 것을 확인했습니다.

## 남은 리스크

- 현재 live runtime은 멈춤이 아니라 `.pipeline/advisory_request.md CONTROL_SEQ 1622`를 Claude advisory lane에서 처리 중입니다. 다만 Codex-only 전환 전까지는 advisory lane 사용 여부와 single-agent mode의 다음-control 정책을 별도 정리해야 합니다.
- browser/E2E는 실행하지 않았습니다. 이번 변경은 런처 runtime status, health 파생, supervisor 단위 회귀에 한정했습니다.
- 작업 시작 전부터 worktree에 다수의 파이프라인/문서/GUI 변경과 untracked `work/`, `verify/`, `report/gemini/` 기록이 있었습니다. 이번 라운드는 위 변경 파일 범위만 다뤘습니다.
