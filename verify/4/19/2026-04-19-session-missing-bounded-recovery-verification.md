# 2026-04-19 session_missing bounded recovery verification

## 변경 파일
- `verify/4/19/2026-04-19-session-missing-bounded-recovery-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/19/2026-04-19-session-missing-bounded-recovery.md`가 supervisor의 bounded `session_missing` recovery와 retry-budget 보강을 닫았다고 주장하므로, 현재 tree의 코드/테스트/문서가 그 설명과 실제로 맞는지 다시 확인해야 했습니다.
- same-day 기존 `/verify`인 `verify/4/19/2026-04-19-watcher-gemini-followup-verify-priority-verification.md`와 `verify/4/19/2026-04-19-manual-cleanup-project-root-blocked-triage-verification.md`는 각각 watcher/manual-cleanup family라 이번 supervisor round truth를 대신하지 못하므로, 별도 `/verify` note를 새로 남기는 편이 맞았습니다.

## 핵심 변경
- latest `/work`의 bounded supervisor slice 주장은 현재 tree와 일치합니다.
  - `pipeline_runtime/supervisor.py`는 `_session_recovery_attempts`를 새로 유지하고, `session_missing` + broken lane 조합에서 `_recover_missing_session()`을 먼저 시도하며, recovery가 성공한 poll에서는 lane별 `restart_lane()`를 다시 돌리지 않습니다.
  - `_spawn_runtime_session()`이 cold start와 session-missing recovery의 공용 scaffold/lane/watcher spawn 경로로 분리돼 있고, `_maybe_recover_lane()`는 restart 실패도 retry budget을 소비하도록 바뀌어 같은 실패를 무한 반복하지 않습니다.
  - `tests/test_pipeline_runtime_supervisor.py`에는 `/work`가 설명한 session-loss boundedness와 failed restart retry-budget 회귀가 실제로 들어 있으며, focused rerun과 module rerun이 모두 통과했습니다.
- `.pipeline/README.md`의 `session loss degraded` 문구는 현재 구현 truth와 맞습니다.
  - 다만 `.pipeline/README.md`는 같은 dirty file 안에 Codex `TASK_ACCEPTED` bullet-accept 문구와 manual cleanup 문구 같은 unrelated hunks도 함께 존재합니다.
  - 이번 verify는 그 전체 diff를 latest `/work` 범위라고 다시 주장하지 않고, `session_missing` recovery paragraph만 독립적으로 확인했습니다.
- same-family 남은 current-risk는 supervisor 바깥의 `TmuxAdapter.create_scaffold()` failure surfacing으로 좁혀졌습니다.
  - `python3 -m unittest -v tests.test_tmux_adapter`는 현재 `Ran 7 tests`, `FAILED (failures=5)`였습니다.
  - 실패한 항목은 `test_create_scaffold_sets_window_size_manual`, `test_create_scaffold_raises_on_required_option_failure`, `test_create_scaffold_raises_on_empty_base_pane_id`, `test_create_scaffold_raises_on_split_window_failure`, `test_create_scaffold_raises_on_select_layout_failure`입니다.
  - 즉 supervisor가 이번 라운드에서 bounded recovery 경로를 추가했더라도, 그 recovery가 재사용하는 `create_scaffold()` 자체는 여전히 required tmux option/pane/layout failure를 충분히 surface하지 못합니다. latest `/work`가 적은 residual risk 문장은 현재 tree에서도 그대로 유효합니다.
- 위 판단에 따라 `.pipeline/claude_handoff.md`를 `CONTROL_SEQ: 350`의 same-family next slice로 갱신했습니다.
  - next slice는 `TmuxAdapter.create_scaffold()`의 required failure surfacing과 pane/layout validation 복구만 요구합니다.
  - next-slice ambiguity나 operator-only decision은 남지 않았으므로 `.pipeline/gemini_request.md`나 `.pipeline/operator_request.md`는 새로 쓰지 않았습니다.

## 검증
- `git status --short`
  - 결과: `.pipeline/README.md`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py`를 포함한 broad dirty worktree가 존재함을 확인했습니다. 이번 verify는 latest `/work` 범위의 supervisor files와 same-family residual-risk probe(`tests.test_tmux_adapter`)만 직접 다뤘습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_recreates_scaffold_once_before_lane_restart tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_failed_recovery_is_bounded_without_lane_restart_loop tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_keeps_session_missing_as_representative_reason_over_lane_recovery_failures tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_failed_pre_accept_restart_consumes_retry_budget tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pre_accept_wrapper_exit_note_consumes_retry_budget_and_restarts`
  - 결과: `Ran 5 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_launch_runtime_spawns_lanes_and_watcher_directly tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_degrades_even_if_lane_health_has_already_dropped_to_off tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_stays_degraded_even_when_watcher_is_also_gone`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 89 tests`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 출력 없음, exit code `0`
- 직접 코드/문서 대조
  - 대상: `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py`, `.pipeline/README.md`
  - 결과: `_spawn_runtime_session()` 분리, `_recover_missing_session()`의 bounded 1회 recovery, `_maybe_recover_lane()`의 실패 retry-budget 소비, `session_missing` 대표 사유 유지, README `session loss degraded` 문구가 latest `/work` 설명과 일치함을 확인했습니다.
- same-family residual-risk probe
  - 명령: `python3 -m unittest -v tests.test_tmux_adapter`
  - 결과: `Ran 7 tests`, `FAILED (failures=5)`
  - 확인된 실패: `test_create_scaffold_sets_window_size_manual`, `test_create_scaffold_raises_on_required_option_failure`, `test_create_scaffold_raises_on_empty_base_pane_id`, `test_create_scaffold_raises_on_split_window_failure`, `test_create_scaffold_raises_on_select_layout_failure`
- live tmux session-loss recovery, `python3 scripts/pipeline_runtime_gate.py fault-check ...`, browser/controller 검증은 이번 verify에서 다시 실행하지 않았습니다.
  - 이유: current-tree truth와 next exact slice를 판정하는 데 focused unit/file checks로 충분했고, live tmux/session 조작은 현재 automation 세션에 영향을 주는 더 넓은 범위이기 때문입니다.

## 남은 리스크
- latest `/work`가 닫은 것은 supervisor 쪽 bounded recovery orchestration입니다. `TmuxAdapter.create_scaffold()`가 required tmux option/pane/layout failure를 surface하지 못하는 문제는 여전히 남아 있어, 실제 host-specific scaffold failure는 recovery 안에서 무음으로 지나갈 수 있습니다.
- live tmux 환경에서 session loss 뒤 scaffold recreation이 실제로 안정적으로 복구되는지는 이번 verify에서 다시 재현하지 않았습니다. 현재 truth는 unit-level recovery path와 same-family adapter failure surface 부재까지입니다.
- `.pipeline/README.md`는 mixed dirty file이라 다음 implementation round가 문서까지 건드린다면 `session_missing` contract만 좁게 맞추고 unrelated hunks를 건드리지 않도록 주의가 필요합니다.
