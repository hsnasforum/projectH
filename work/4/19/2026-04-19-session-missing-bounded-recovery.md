# 2026-04-19 session_missing bounded recovery

## 변경 파일
- 이번 라운드 직접 편집:
  - `pipeline_runtime/supervisor.py`
  - `tests/test_pipeline_runtime_supervisor.py`
  - `.pipeline/README.md`
  - `work/4/19/2026-04-19-session-missing-bounded-recovery.md`
- 이번 라운드 범위 밖의 기존 dirty worktree:
  - controller cozy/runtime 반영 파일들
  - manual cleanup 관련 `.pipeline/*`, `tests/test_pipeline_smoke_cleanup.py`
  - 기타 4/18 closeout / verify 파일들

## 사용 skill
- `work-log-closeout`: 이번 supervisor/session recovery 구현 라운드의 `/work` 기록을 repo 규약 형식으로 남기기 위해 사용.

## 변경 이유
- 실제 live runtime 조사 결과, Claude만 멈춘 것이 아니라 `aip-projectH` tmux session 자체가 사라지면서 `session_missing`이 발생했고, supervisor가 lane별 `restart_lane()`만 반복 호출하면서 `recovery_started`가 끝없이 쌓이는 상태였습니다.
- 기존 구현은 tmux session이 이미 없는 상황에서도 lane pane restart를 먼저 시도했고, restart 실패가 retry budget을 소비하지 않아 같은 실패를 매 poll마다 다시 반복할 수 있었습니다.
- 이번 라운드는 session loss의 owner를 supervisor로 고정해, missing session에는 lane restart 대신 bounded session 재생성을 먼저 시도하고, 실패한 lane restart도 retry budget을 소비하도록 좁게 수정했습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py`에 `_spawn_runtime_session()`을 분리해, cold start와 session-missing recovery가 같은 tmux scaffold/lane spawn/watcher spawn 경로를 재사용하게 했습니다.
- `session_missing` + broken lanes 조합에서는 supervisor가 bounded `session_recovery_started`/`session_recovery_completed`/`session_recovery_failed` 경로로 tmux scaffold를 한 번 다시 세우도록 추가했습니다.
- session recovery가 성공한 poll에서는 lane별 `restart_lane()`를 같은 라운드에서 다시 돌리지 않게 막아, nonexistent pane을 상대로 한 중복 recovery noise를 줄였습니다.
- `_maybe_recover_lane()`는 restart 성공뿐 아니라 restart 실패도 retry budget을 소비하도록 바꿔, same failure가 무한 `recovery_started` loop로 남지 않게 했습니다.
- `.pipeline/README.md`에 `session_missing` contract를 업데이트해, session loss에서는 bounded scaffold recovery를 먼저 시도하고 실패 후에도 next `session_alive` 전까지 retry storm을 만들지 않는 경계를 명시했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 session recovery 성공/실패 boundedness와 failed restart retry-budget 소비 회귀를 추가했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_recreates_scaffold_once_before_lane_restart tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_failed_recovery_is_bounded_without_lane_restart_loop tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_keeps_session_missing_as_representative_reason_over_lane_recovery_failures tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_failed_pre_accept_restart_consumes_retry_budget tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pre_accept_wrapper_exit_note_consumes_retry_budget_and_restarts`
  - 결과: `Ran 5 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_launch_runtime_spawns_lanes_and_watcher_directly tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_degrades_even_if_lane_health_has_already_dropped_to_off tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_stays_degraded_even_when_watcher_is_also_gone`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 89 tests`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 출력 없음

## 남은 리스크
- 이번 라운드는 unit regression과 상태/이벤트 경계까지만 닫았습니다. 실제 tmux live session이 사라진 뒤 새 scaffold가 현 환경에서 즉시 정상 복구되는지는 별도 live stability gate로 한 번 더 확인해야 합니다.
- session recovery는 bounded 1회로 제한했습니다. 따라서 tmux 자체가 계속 비정상인 환경에서는 retry storm은 멈추지만 runtime은 `DEGRADED(session_missing)`로 남고, 추가 operator 조치가 여전히 필요합니다.
- `tmux_adapter.create_scaffold()` 내부의 세부 오류 surface/검증 강화는 이번 범위에 넣지 않았습니다. session_missing 이후 scaffold 생성 자체가 실패하는 host-specific 문제까지 더 줄이려면 다음 라운드에서 tmux adapter contract를 별도로 다루는 편이 맞습니다.
