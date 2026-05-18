# 2026-05-12 Pipeline launcher non-stop guard

## 변경 파일

- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `.pipeline/README.md`
- `verify_fsm.py`
- `watcher_dispatch.py`
- `watcher_state.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/5/12/2026-05-12-pipeline-launcher-nonstop-guard.md`

## 사용 skill

- `security-gate`: 런처 health, watcher dispatch, local 상태 기록 변경이 승인/저장/게시/merge 경계를 넓히지 않고 로컬 런타임 복구 표면화에만 머무르는지 확인했습니다.
- `doc-sync`: no-silent-stall runtime health 계약이 구현과 테스트에 맞게 `.pipeline/README.md`에 좁게 반영됐는지 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, live 확인 결과, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.
- `release-check`: 테스트, 문서 동기화 필요 여부, 미실행 범위, 잔여 리스크를 handoff 전 점검했습니다.

## 변경 이유

- 완료된 duplicate handoff, 다음 control 부재, verify dispatch 접수 대기 상태가 `ok/continue`로 보이면 런처가 실제로 멈췄는데도 정상처럼 보일 수 있었습니다.
- 첫 `task_accept_missing`은 자동 재시도 중인 상태로 보여야 하고, 반복된 동일 fingerprint stall은 `dispatch_stall` degraded로 올려 silent loop를 끊어야 합니다.
- stale pasted prompt, stale dispatch id, persisted dedupe key가 새 dispatch 재시도를 막지 않도록 기존 watcher/FSM 경로를 강화해야 했습니다.

## 핵심 변경

- `derive_automation_health()`가 `VERIFY_PENDING + dispatch_stage=task_accept_missing|dispatch_seen_missing`를 non-degraded 상태에서는 `recovering / dispatch_stall / retrying`으로 분류하고, `degraded_reason=dispatch_stall` 이후에는 `attention / dispatch_stall / verify_followup`으로 분류하도록 했습니다.
- duplicate handoff idle과 `waiting_next_control` lane note가 no-active-control 상태에서 `ok/continue`로 떨어지지 않고 verify-followup attention으로 보이도록 health 회귀를 보강했습니다.
- supervisor 회귀에서 public `control=none`, `turn_state=IDLE`, `progress={}` 정리는 유지하면서 health만 `attention`으로 표면화되는지 확인했습니다.
- verify FSM은 첫 dispatch 접수 누락에서 dedupe/lease/dispatch tracking을 정리하고 1회 requeue하며, 같은 fingerprint 반복 시 `degraded_reason=dispatch_stall`로 올리도록 보강했습니다.
- watcher dispatch/state 경로는 stale pasted prompt 교체, persisted dedupe forget tombstone, 새 dispatch 처리 회귀를 추가해 같은 명령문 반복 붙여넣기 루프를 줄였습니다.
- `.pipeline/README.md`의 no-silent-stall 계약에 non-degraded verify dispatch wait, degraded dispatch stall, duplicate handoff, waiting-next-control health 표면화 규칙을 맞췄습니다.
- security-gate 메모: 변경은 local tmux/runtime status, local JSON/event, `.pipeline` control-slot 관찰 및 재시도 판단에 한정됩니다. commit/push/PR/merge, 외부 게시, auth/credential, approval-record repair 권한은 추가하지 않았습니다.

## 검증

- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_duplicate_handoff_verify_followup_progress tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_from_canonical_blocked_triage_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_requeued_dispatch_wait_as_recovering tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_dispatch_stall_degraded_reason_and_event`
- PASS: `python3 -m unittest -v tests.test_watcher_core.DedupeGuardPersistenceTest tests.test_watcher_core.PanePromptDetectionTest tests.test_watcher_core.CodexDispatchConfirmationTest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest tests.test_watcher_core.VerifyPendingBackoffTest`
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest`
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_watcher_core`
- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py verify_fsm.py watcher_dispatch.py watcher_state.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
- PASS: `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py verify_fsm.py watcher_dispatch.py watcher_state.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/implement_handoff.md work/5/12/2026-05-12-pipeline-launcher-idle-next-control-health.md`
- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py verify_fsm.py watcher_dispatch.py watcher_state.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py && git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py verify_fsm.py watcher_dispatch.py watcher_state.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py work/5/12/2026-05-12-pipeline-launcher-nonstop-guard.md`
- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py verify_fsm.py watcher_dispatch.py watcher_state.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py && git diff --check -- .pipeline/README.md pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py verify_fsm.py watcher_dispatch.py watcher_state.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py work/5/12/2026-05-12-pipeline-launcher-nonstop-guard.md`
- PASS: `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`
- PASS(live): `python3 -m pipeline_runtime.cli status --json /home/xpdlqj/code/projectH`
  - 재시작 후 이전 `VERIFY_PENDING + task_accept_missing` 상태는 `VERIFYING`으로 진행됐고, live `automation_health=ok`, `automation_next_action=continue`는 `active_round.state=VERIFYING`, `status=VERIFY_RUNNING`, `completion_stage=task_done_pending`인 실제 진행 상태였습니다.
- PASS(live): `python3 -m pipeline_runtime.cli status --json /home/xpdlqj/code/projectH`
  - 최종 확인에서는 `turn_state.reason=handoff_already_completed`, `control.active_control_status=none` 상태가 `automation_health=attention`, `automation_reason_code=duplicate_handoff`, `automation_next_action=verify_followup`으로 표면화됐습니다.

## 남은 리스크

- browser/E2E는 실행하지 않았습니다. 이번 변경은 런처 health 파생, supervisor status, watcher dispatch/FSM 단위 경로에 한정했습니다.
- live status는 재시작 직후 검증 라운드가 진행 중임을 확인했습니다. 해당 별도 Codex verify pane의 최종 closeout까지 장시간 대기하지는 않았습니다.
- 작업 시작 전부터 worktree에는 여러 파이프라인/문서/GUI 변경과 많은 untracked `work/`, `verify/`, `report/gemini/` 기록이 있었습니다. 이번 라운드는 위 변경 파일 범위만 검증했습니다.
