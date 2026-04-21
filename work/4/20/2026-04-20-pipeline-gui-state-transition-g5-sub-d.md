# 2026-04-20 pipeline gui state transition G5 sub-D

## 변경 파일
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 현재 shipped `pipeline_gui/backend.py::read_runtime_status`가 제공하지 않는 state-transition spec을 11개 cell에서 강하게 요구하고 있어 baseline이 `failures=8, errors=3`으로 깨져 있었습니다.
- 이번 라운드는 advice 464의 unbounded한 "test-side rewrite"를 그대로 따르지 않고, drifted 11개 cell만 stable skip reason으로 명시적 defer 처리해 현재 thin-reader contract와 테스트 truth를 투명하게 맞추는 것이 목적이었습니다.

## 핵심 변경
- `tests/test_pipeline_gui_backend.py`에서 지정된 11개 `TestRuntimeStatusRead` 메서드 위에 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")`를 추가했습니다. 적용 위치는 `:594`, `:644`, `:719`, `:794`, `:869`, `:947`, `:1018`, `:1067`, `:1135`, `:1203`, `:1265`였습니다.
- skip 대상 11개는 handoff가 지정한 exact method set만 포함합니다:
  - `test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - `test_read_runtime_status_from_current_run_pointer`
  - `test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`
  - `test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`
  - `test_read_runtime_status_converts_stopping_without_supervisor_into_stopped`
  - `test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous`
  - `test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids`
  - `test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing`
  - `test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded`
  - `test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous`
  - `test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing`
- `pipeline_gui/backend.py`는 의도적으로 수정하지 않았습니다. `read_runtime_status` / `runtime_state`의 thin-reader shipped contract는 그대로 유지했고, supervisor liveness detection / RUNNING→BROKEN / STOPPING→STOPPED / RUNNING→DEGRADED / degraded_reason normalization feature는 skip reason string으로 future unskipping round가 다시 찾을 수 있게 남겼습니다.
- 이번 slice는 advice 464의 broad한 "test-side rewrite" framing을 G5-sub-D의 truthful-deferral form으로 좁힌 것입니다. helper를 새로 만들거나 기대값을 조용히 rewrite하지 않고, defer 상태를 skip reason literal로 노출했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459 shipped surfaces는 전부 미편집입니다. `pipeline_gui/backend.py`, `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, client/serializer/Playwright도 건드리지 않았습니다. G3 / G5 나머지 축 / G7 / G8 / G9 / G10 / G11은 계속 deferred 상태입니다.

## 검증
- baseline 참고:
  - `python3 -m unittest tests.test_pipeline_gui_backend`
  - baseline 결과: `Ran 45 tests in 0.054s`, `FAILED (failures=8, errors=3)`
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 11건 hit
  - line: `594`, `644`, `719`, `794`, `869`, `947`, `1018`, `1067`, `1135`, `1203`, `1265`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 11건 hit
  - 기존 다른 skip은 없었고, 이번 라운드 추가분만 잡혔습니다.
- `rg -n 'def test_read_runtime_status' tests/test_pipeline_gui_backend.py`
  - 결과: 12건 hit
  - `TestRuntimeStatusRead`의 read_runtime_status 계열 메서드는 총 12개였고, 그중 `test_read_runtime_status_returns_none_without_current_run` 1개는 그대로 활성 상태로 남았습니다.
- `rg -n 'pipeline_gui_backend_state_transition_deferred' pipeline_gui/ storage/ core/ app/`
  - 결과: 0건 hit
  - stable skip reason은 테스트 파일에만 존재합니다.
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.050s`, `OK (skipped=11)`
  - baseline `failures=8, errors=3`에서 post-edit `skipped=11, failures=0, errors=0`으로 바뀌었습니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.018s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.057s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.065s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드 범위 밖이라 실행하지 않았습니다.

## 남은 리스크
- 11개 cell은 이제 `@unittest.skip`으로 표시된 것이지 fix된 것이 아닙니다. underlying state-transition feature는 여전히 `pipeline_gui/backend.py`에 구현되어 있지 않습니다. 이후 round에서 (i) unskip + 구현, (ii) spec 삭제, (iii) indefinite skip 중 하나를 결정할 수 있고, `pipeline_gui_backend_state_transition_deferred` grep으로 위치를 다시 찾을 수 있습니다.
- `.pipeline/operator_request.md`의 seq 462 stop은 이제 최신 valid control인 seq 465 handoff로 자연스럽게 supersede되었습니다. 당시의 4개 option path(`SCOPE_G5_AS_MULTI_ROUND` / `ACCEPT_TEST_DRIFT` / `DEFER_G5` / `ACKNOWLEDGE_INFORMATIONAL`)는 future arbitration framing으로만 남습니다. 이번 G5-sub-D는 그중 `ACCEPT_TEST_DRIFT`와 가장 가깝지만, delete가 아니라 skip이고 drifted 11개에만 한정된 더 좁은 형태입니다.
- unrelated `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError cell은 여전히 G6-sub2 후보로 남아 있습니다. `tests.test_web_app` whole-family truth-sync의 추가 judgment도 G6-sub3 후보로 남아 있습니다. G3 / G7 / G8 / G9 / G10 / G11도 모두 deferred 상태입니다.
- 오늘(2026-04-20) docs-only round count는 계속 0입니다. 이번 라운드는 tests-only slice였습니다.
- dirty worktree의 다른 파일들은 이번 라운드에서 건드리지 않았습니다.
