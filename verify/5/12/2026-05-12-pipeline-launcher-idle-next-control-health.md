STATUS: verified

# 2026-05-12 Pipeline launcher idle next-control health 검증

## 대상

- `work/5/12/2026-05-12-pipeline-launcher-idle-next-control-health.md`

## 변경 파일

- 없음

## 결론

- 통과입니다. duplicate handoff 완료 상태에서 active control이 없고 public turn이 `IDLE`인 경우를 더 이상 `automation_health=ok`, `automation_next_action=continue`로 표면화하지 않고 `attention/duplicate_handoff/verify_followup`으로 분류하는 것을 단위 회귀로 확인했습니다.
- `waiting_next_control` lane note도 `verify_followup` 계열 attention으로 분류됩니다.
- 같은 변경 파일 안에 `VERIFY_PENDING` dispatch wait 상태를 non-degraded이면 `recovering/retrying`, degraded `dispatch_stall`이면 `attention/verify_followup`으로 나누는 추가 diff가 함께 보였고, 해당 `recovering` 경로도 포함해 검증했습니다. 최신 `/work`의 핵심 duplicate-handoff claim은 사실과 일치하지만, 이 추가 dispatch wait 세부사항은 `/work` 본문에 별도 핵심 변경으로 자세히 쓰여 있지는 않습니다.

## 확인한 사실

- `derive_automation_health()`는 `turn_state.reason=handoff_already_completed` 또는 `duplicate_handoff`, `control.active_control_status=none`, `turn_state.state=IDLE` 조건을 `automation_health=attention`, `automation_reason_code=duplicate_handoff`, `automation_next_action=verify_followup`으로 분류합니다.
- lane note `waiting_next_control`은 `automation_reason_code=waiting_next_control`, `automation_next_action=verify_followup`으로 분류됩니다.
- supervisor duplicate handoff 회귀는 public `control.active_control_status=none`, `turn_state.state=IDLE`, `progress={}`를 유지하면서 automation health만 attention으로 올립니다.
- 현재 live status 조회 시 런타임은 `RUNNING`, active control은 `.pipeline/implement_handoff.md` `CONTROL_SEQ=1620`, active round는 검증 중(`VERIFYING`)으로 보였습니다. 이 상태는 현재 검증 턴의 표면이며, duplicate-handoff idle edge 자체는 단위 회귀로 확인했습니다.

## 실행한 검증

- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_duplicate_handoff_verify_followup_progress tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_from_canonical_blocked_triage_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_requeued_dispatch_wait_as_recovering`
  - 32 tests
- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
- PASS: `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py work/5/12/2026-05-12-pipeline-launcher-idle-next-control-health.md`
- 참고 확인: `python3 -m pipeline_runtime.cli status --json /home/xpdlqj/code/projectH`

## 실행하지 않은 검증

- browser/E2E는 실행하지 않았습니다. 이번 검증 대상은 runtime health 파생 로직과 supervisor status 단위 표면화입니다.
- live restart나 장시간 soak는 실행하지 않았습니다. 현재 런타임은 이미 active verify turn에 있었고, duplicate-handoff idle edge는 단위 회귀가 직접 재현합니다.

## 남은 리스크

- worktree에는 이번 범위 밖의 미커밋 변경과 미추적 기록 파일이 다수 남아 있습니다. 이번 검증은 `pipeline_runtime/automation_health.py`, `tests/test_pipeline_runtime_automation_health.py`, `tests/test_pipeline_runtime_supervisor.py`의 latest `/work` claim에 한정했습니다.
- `/work`는 duplicate handoff idle health 보강을 중심으로 기록되어 있으며, 같은 diff 안의 dispatch wait recovering 세부 변경은 검증했지만 closeout 본문에는 자세히 설명되어 있지 않습니다.
