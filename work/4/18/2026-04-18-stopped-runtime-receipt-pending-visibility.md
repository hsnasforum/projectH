# 2026-04-18 stopped runtime에서 RECEIPT_PENDING active_round visible 유지

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `.pipeline/README.md`

## 사용 skill
- `superpowers:using-superpowers`: implement lane 진입 전에 skill 경계와 handoff 규약을 그대로 따르기 위해 사용했습니다.

## 변경 이유
- latest `/work` + `/verify`(`work/4/18/2026-04-18-active-round-live-verify-preference.md` + matching verification)은 `_build_active_round()` liveness ranking까지 닫아 줬지만, 같은 family의 남은 current-risk는 `_write_status()` 상단에서 `runtime_state ∈ {STOPPING, STOPPED, BROKEN}`이면 `surfaced_active_round`를 무조건 `None`으로 지우는 경로였습니다.
- 이 경로 때문에 VERIFY_DONE without receipt(= `state="RECEIPT_PENDING"`)인 round가 남아 있어도, runtime이 STOPPED면 thin-client `status.json`에서 `active_round`가 통째로 비워졌고, launcher/controller가 "Receipt: pending close" current truth를 읽을 수 없었습니다. 실제로 baseline 테스트 집합에서도 `test_verify_done_without_receipt_stays_receipt_pending`가 `status["active_round"]` None으로 인해 ERROR로 실패하고 있었습니다.
- `.pipeline/README.md` 현재 문구도 “receipt close 대기 상태는 '멈춤'이 아니라 current runtime truth로 보여야 한다”는 규약을 이미 담고 있었으므로, stopped runtime에서 receipt-close visibility를 예외적으로 보존하는 것은 `_build_active_round` 이후 남은 가장 좁은 후속 슬라이스였습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py::_write_status()`에서 `runtime_state ∈ {STOPPING, STOPPED, BROKEN}` 블록을 다음과 같이 좁혔습니다.
  - `control_block`(active_control_file/seq/status/updated_at)은 기존처럼 비움.
  - `self._write_task_hints(active_lane="", active_round=None, ...)`도 그대로 호출해 verify/receipt task hint가 stopped runtime에서 되살아나지 않게 계속 초기화.
  - `surfaced_active_round`는 **이미 `None`이거나 `state != "RECEIPT_PENDING"`일 때만** `None`으로 덮어쓰도록 조건을 추가. 즉 live `VERIFY_PENDING`/`VERIFYING` surface는 여전히 fail-safe로 사라지지만, receipt-close 대기 round는 status 바깥 surface로 유지됩니다.
  - 이 이후의 `dispatch_stall_marker` / `completion_stall_marker` 계산은 같은 `surfaced_active_round`를 받게 되어, 남긴 RECEIPT_PENDING round와 매칭되는 존재하는 job의 completion_stage 같은 메타데이터를 그대로 surface할 수 있습니다.
- `autonomy` 블록은 이미 line 1288–1289에서 `runtime_state ∈ {STOPPING, STOPPED}`일 때 `_default_autonomy_block()`으로 초기화되므로, 이번 변경 때문에 stopped 상태에서 autonomy가 되살아나는 부작용은 없습니다.
- `.pipeline/README.md`에 한 줄을 추가해 “`STOPPING`/`STOPPED`/`BROKEN` runtime이어도 마지막 `active_round.state == "RECEIPT_PENDING"`이면 status surface는 그 round만 visible하게 유지하고, live verify surface와 `control`/task hint/autonomy block은 계속 fail-safe로 비운다”는 경계 조건을 명시했습니다. 기존 문구(launcher thin client가 `Receipt: pending close`를 current runtime truth로 읽을 수 있어야 한다)와 같은 줄 근처에 두어 읽는 순서가 자연스럽게 맞물립니다.
- 테스트는 기존에 이미 존재하던 4개(`test_verify_done_without_receipt_stays_receipt_pending`, `test_write_status_clears_verify_task_hint_when_runtime_is_stopped`, `test_receipt_pending_does_not_keep_codex_active_lane_when_turn_is_idle`, `test_receipt_pending_keeps_codex_active_lane_during_codex_followup_turn`)가 이번 슬라이스의 regression surface를 이미 덮고 있어서 추가로 test를 넣지 않고, 이 4개가 모두 통과하는지 focused로 다시 확인했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py tests/test_turn_arbitration.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_done_without_receipt_stays_receipt_pending tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_verify_task_hint_when_runtime_is_stopped tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_receipt_pending_does_not_keep_codex_active_lane_when_turn_is_idle tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_receipt_pending_keeps_codex_active_lane_during_codex_followup_turn tests.test_turn_arbitration`
  - 결과: `Ran 11 tests`, `OK` (handoff가 요구한 4개 focused supervisor test + turn_arbitration 전체 모두 통과)
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration`
  - 결과: `Ran 75 tests`, `FAILED (failures=6)` — baseline의 errors=1(= `test_verify_done_without_receipt_stays_receipt_pending`)은 이번 슬라이스로 해결되어 **errors=0**으로 줄었고, 남은 6개 failure는 이번 범위 밖의 degraded/restart family(`test_manifest_mismatch_blocks_receipt_and_marks_degraded`, `test_write_status_marks_runtime_degraded_on_active_lane_auth_failure`, `test_auth_failure_breakage_blocks_restart`, `test_claude_post_accept_breakage_blocks_blind_replay`, `test_codex_breakage_stops_after_retry_budget`, `test_codex_pre_completion_breakage_restarts_within_retry_budget`)가 그대로 유지되었습니다. scope를 넓히지 않았습니다.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py tests/test_turn_arbitration.py .pipeline/README.md`
  - 결과: 통과
- controller/browser smoke와 launcher live replay는 이번 라운드에 돌리지 않았습니다. 이유: 이번 변경은 `status.json`의 `active_round` visibility 규칙을 STOPPING/STOPPED/BROKEN에서만 좁게 조정한 것이고, browser-visible 계약(selector, 시나리오 수, gate 의미)을 바꾸지 않았기 때문입니다.

## 남은 리스크
- STOPPED runtime에서 `RECEIPT_PENDING` round가 유지되는 동안 `_dispatch_stall_marker` / `_completion_stall_marker`가 job state와 매칭해 marker를 계속 만들 가능성이 남습니다. 다만 `degraded_reasons`는 `runtime_inactive`일 때 line 1230에서 비워지고, autonomy block도 초기화되므로 현재 surface에서 `degraded_reason` 문자열로 올라오지는 않습니다. 이 edge가 실제 tmux live에서 어떻게 보이는지는 다음 라운드에서 한 번 더 확인하는 편이 맞습니다.
- 이번 라운드는 `_write_status`에서 RECEIPT_PENDING만 특정해서 예외 처리했습니다. `_build_active_round`가 앞으로 `NEW_ARTIFACT`/`STABILIZING` 같은 verify 이전 단계를 더 세분화해 `RECEIPT_PENDING`처럼 stopped에서도 보이고 싶어지면, 이 조건도 같이 확장하거나 별도 helper로 정리하는 편이 맞습니다.
- 남은 baseline 실패 family(6 failures)는 여전히 degraded/restart/manifest-mismatch 계약 쪽이라, 다음 supervisor slice에서 그 family를 직접 좁게 건드릴 때 함께 조사할 대상으로 남겨 둡니다.
