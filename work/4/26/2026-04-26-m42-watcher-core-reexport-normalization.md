# 2026-04-26 M42 watcher_core re-export normalization

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `work/4/26/2026-04-26-m42-watcher-core-reexport-normalization.md`

## 사용 skill
- `onboard-lite`: `watcher_core.py`, `watcher_dispatch.py`, `watcher_state.py`, `verify_fsm.py` 경계를 좁게 확인
- `security-gate`: watcher dispatch/tmux 호출 경로와 patch target 변경이 승인 경계를 우회하지 않는지 확인
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 검증, 잔여 리스크 기록

## 변경 이유
- `watcher_core.py`가 여러 하위 모듈의 심볼을 암묵적으로 재노출해 테스트와 patch target이 실제 소유 모듈 대신 `watcher_core.*`에 결합되어 있었다.
- M42 A1-β 진입 전 dispatch/state/FSM 소유 경계를 더 명확히 해 이후 watcher 분해 작업의 회귀면을 줄이기 위함이다.
- pipeline 자동화/호환성 관점에서는 `watcher_core`가 dispatch/state/FSM truth를 다시 해석하거나 재노출하지 않게 해 false-stop/need_operator 감소 작업의 소유 경계를 좁히는 기반 정리다.

## 핵심 변경
- `watcher_core.py`에서 `watcher_dispatch` 함수/클래스 직접 import를 제거하고 `watcher_dispatch.WatcherDispatchQueue`, `watcher_dispatch.tmux_send_keys`, `watcher_dispatch.DispatchIntent`, `watcher_dispatch._is_pane_dead` 경로로 호출하도록 정규화했다.
- `watcher_core.__all__ = ["WatcherCore", "main"]`을 추가해 star-import 기준의 공개 표면을 명시했다.
- `tests/test_watcher_core.py`의 상태/FSM/stabilizer 참조를 실제 소유 모듈로 옮겼다: `WatcherTurnState`, `ControlSignal`, `PaneLease`는 `watcher_state`, `JobState`, `JobStatus`, `make_job_id`는 `verify_fsm`, `compute_file_sha256`는 `watcher_stabilizer`에서 import한다.
- 테스트의 runtime helper 참조를 실제 소유 경로로 바꿨다: `VERIFY_FOLLOWUP_ROUTE`는 `pipeline_runtime.role_routes`, `legacy_turn_state_name`은 `pipeline_runtime.turn_arbitration`, dispatch 함수/상수는 `watcher_dispatch`에서 사용한다.
- mock patch target을 실제 호출 경로에 맞췄다: `watcher_dispatch.tmux_send_keys`, `watcher_dispatch._is_pane_dead`, `watcher_state.os.kill`.

## 검증
- `python3 -m py_compile watcher_core.py watcher_dispatch.py watcher_state.py verify_fsm.py` 통과
- `python3 -m unittest -v tests.test_watcher_core` 통과: 204 tests OK, `Ran 204 tests in 6.350s`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_proc_ctime_fallback tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_after_watcher_exporter_writes_pointer` 통과: 4 tests OK
- `git diff --check -- watcher_core.py watcher_state.py` 통과
- `git diff --check -- watcher_core.py watcher_state.py tests/test_watcher_core.py` 통과
- `git diff --check -- watcher_core.py tests/test_watcher_core.py work/4/26/2026-04-26-m42-watcher-core-reexport-normalization.md` 통과

## 남은 리스크
- 의도한 변경은 import/patch target 정규화이며 watcher 동작 변경은 없다.
- 브라우저/E2E는 이번 re-export 정리 범위 밖이라 실행하지 않았다.
- 커밋, 푸시, PR 생성은 implement lane 범위 밖이라 수행하지 않았다.
- 기존 dirty tree의 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, 선행 `/work` 미추적 파일은 이번 범위 밖이라 건드리지 않았다.
