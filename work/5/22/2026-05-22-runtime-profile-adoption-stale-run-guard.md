# 2026-05-22 runtime profile adoption stale run guard

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/22/2026-05-22-runtime-profile-adoption-stale-run-guard.md`

## 사용 skill
- `security-gate`: runtime status/control surface와 degraded reason을 바꾸는 작업이라 로컬/운영 경계, operator stop 비전환, profile 파일 비수정 범위를 확인했습니다.
- `finalize-lite`: 구현 마무리에서 실행한 focused checks, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 한국어 closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2145 handoff에 따라 active `.pipeline/config/agent_profile.json`과 이미 실행 중인 supervisor lane/role plan이 어긋날 때 이를 runtime status에 명시적으로 드러내도록 했습니다.
- trigger-6 verify에서는 profile 파일이 `verify=Claude`라고 주장했지만 dispatcher status/events는 Codex lane 처리를 보여 줬으므로, 또 다른 metadata trigger 전에 profile adoption truth를 status surface에서 구분해야 했습니다.

## 핵심 변경
- `RuntimeSupervisor`에 running plan과 fresh active profile plan을 비교하는 helper를 추가했습니다.
- `_write_status()`가 `profile_adoption` 블록을 포함하도록 했습니다. 블록은 `state`, `reason_code`, `running`, `active` 요약을 제공합니다.
- running plan과 active profile plan이 다르면 `profile_adoption.state`를 `stale_runtime_plan`으로 표시하고 `reason_code`를 `active_profile_runtime_plan_mismatch`로 기록합니다.
- active runtime이 있는 상태에서 plan mismatch가 감지되면 `runtime_profile_adoption_stale`을 `degraded_reasons`에 추가해 automation surface가 READY처럼 보이지 않게 했습니다.
- `verify=Claude`가 현재 running plan에도 반영된 경우 Claude task hint가 active verify round identity를 받는 focused test를 추가했습니다.
- 같은 파일에는 이전 round에서 남긴 `verify_done_deadline_sec` runtime policy 미커밋 변경도 유지되어 있으며, 이번 slice에서 되돌리지 않았습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_stale_active_profile_runtime_plan -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_activates_claude_task_hint_for_verify_round_when_profile_current -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_activates_codex_task_hint_for_verify_round_without_control_slot -v`
  - 결과: `Ran 1 test`, `OK`

## 남은 리스크
- 이번 변경은 local unit/status regression입니다. live Claude trigger 재발행, pipeline restart, tmux, supervisor live run, controller/browser/full smoke는 실행하지 않았습니다.
- `TASK_DONE source=wrapper lane=Claude` end-to-end 관찰은 아직 완료되지 않았습니다. 다음 verify round가 새 status block과 runtime events를 함께 확인해야 합니다.
- `.pipeline/config/agent_profile.json`은 수정하지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.
