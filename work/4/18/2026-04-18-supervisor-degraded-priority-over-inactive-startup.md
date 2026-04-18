# Supervisor degraded precedence over inactive/startup surface

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 297, HANDOFF_SHA `eee2e38...`)가 active receipt/auth breakage가 남아 있는데도 `runtime_state`가 `STOPPED` 또는 `STARTING`으로 내려가 current truth를 가리는 `_write_status()` + `_maybe_recover_lane()` 축 하나를 다음 current-risk slice로 지목함.
- focused 재실행에서 `tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_manifest_mismatch_blocks_receipt_and_marks_degraded`, `test_write_status_marks_runtime_degraded_on_active_lane_auth_failure` 두 케이스가 이 경계 오류에 해당했고, 이전 `/verify` 기록이 watcher dispatch 축은 이미 truthfully 닫혔음을 확인했기 때문에 supervisor 쪽 surface truth를 먼저 맞추는 편이 다음 live gate보다 우선함.

## 핵심 변경

- `_maybe_recover_lane`: `self._stop_requested or not self._runtime_started` 조건을 `self._stop_requested`만 남기도록 좁혀, startup이 아직 inactive인 상태에서도 active lane `BROKEN` + auth/post-accept failure reason을 그대로 surface함. lane이 `OFF`인 inactive stop path에서는 여전히 `str(lane.state) != "BROKEN"` 가드가 먼저 걸려 stale degrade를 재생산하지 않음. restart_lane 실제 실행 경로는 그대로 보존.
- `_write_status`: active breakage(`receipt_degraded` + `_maybe_recover_lane` 결과)와 stale job-state `degraded_reason`을 명시적으로 분리. `runtime_inactive and not self._launch_failed_reason`일 때는 stale job-state reason만 drop하고 active breakage는 `degraded_reasons`에 남김. `runtime_state` 매핑에서 `elif self.degraded_reason: DEGRADED`를 `elif runtime_inactive: STOPPED`보다 앞으로 옮겨 current boundary 파손이 inactive/startup surface보다 먼저 판정되게 함.
- `.pipeline/README.md`: 기존 "STOPPED로 내려갈 때 stale degrade 지움" 문장 바로 다음에 "current receipt manifest mismatch 또는 active lane auth/post-accept breakage는 `_runtime_started`가 false여도 `runtime_state=DEGRADED`로 surface" 문장 한 줄을 추가해 docs가 code와 일치하게 함.

## 검증

- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_manifest_mismatch_blocks_receipt_and_marks_degraded tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_runtime_degraded_on_active_lane_auth_failure tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_stale_degraded_reason_after_runtime_has_stopped tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_done_without_receipt_stays_receipt_pending` → 4/4 pass.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` → 71 tests pass (이전 라운드에서 같은 family로 실패했던 `test_claude_post_accept_breakage_blocks_blind_replay`, `test_auth_failure_breakage_blocks_restart`, `test_codex_pre_completion_breakage_restarts_within_retry_budget`, `test_codex_breakage_stops_after_retry_budget`도 함께 복원됨).
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md` → clean.
- `make e2e-test`, live soak, launcher live gate는 이 slice에서 실행하지 않음. 변경이 supervisor status surface 판정 우선순위에 한정돼 browser 계약/launcher contract가 넓어지지 않았으므로 좁은 focused unit suite로 충분함.

## 남은 리스크

- `_runtime_started` 가드 제거가 `_maybe_recover_lane`의 `restart_lane` 실제 호출을 startup 이전에도 허용함. 다만 이 경로는 lane state가 `BROKEN`이고 accepted_task/failure_reason이 이미 있어야 활성화되므로 blind restart 재개가 아닌 기존 retry budget 내 재시작이며, live runtime에서 blind replay를 일으키려면 별도 failure context가 먼저 필요함. 다음 live gate에서 이 경로가 실제 pid churn을 만드는지는 live stability gate로 확인해야 함.
- `runtime_inactive` filter가 `session_missing`을 drop하지만 이 path는 `self._runtime_started`일 때만 append되므로 동일 결과. 추후 session_missing을 inactive/startup에도 surface하려면 별도 slice가 필요함.
- `.pipeline/README.md` 업데이트 한 줄은 supervisor 코드와 정합하지만, launcher / controller thin-client 쪽 degraded reason 표시 문구는 이번 slice에서 건드리지 않음. 동일 reason code를 그대로 쓰므로 회귀 범위는 좁을 것으로 보이나, 다음 controller 라운드에서 visible copy 점검이 필요할 수 있음.
