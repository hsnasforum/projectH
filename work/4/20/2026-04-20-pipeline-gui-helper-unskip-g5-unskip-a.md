# 2026-04-20 pipeline gui helper unskip G5-unskip-A

## 변경 파일
- pipeline_gui/backend.py
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- seq 465에서 `TestRuntimeStatusRead` 11개 cell을 skip으로 defer했지만, 그중 `test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`는 실제 shipped `read_runtime_status` thin-reader contract만으로도 통과 가능한 셀이었습니다.
- 이번 라운드는 broader state-transition logic을 구현하지 않고도, 테스트가 mock target으로 기대하는 `_supervisor_pid` / `_pid_is_alive`를 module-level helper로 노출해 한 셀을 다시 활성화하는 smallest same-family slice를 닫는 것이 목적이었습니다.

## 핵심 변경
- `pipeline_gui/backend.py`는 이제 `_supervisor_pid(project)`와 `_pid_is_alive(pid)`를 module-level helper로 노출합니다. post-edit line은 각각 `:560`, `:580`이고, `supervisor_alive(project)`는 `:592`에서 두 helper를 조합하는 wrapper로 축소됐습니다. public 반환 계약 `tuple[bool, int | None]`은 그대로 유지했습니다.
- helper 추출은 semantic no-op입니다. Windows/WSL 쪽 `cat` + `kill -0`, Linux 쪽 `Path.read_text` + `os.kill(pid, 0)` 흐름을 그대로 분리했을 뿐이고, `read_runtime_status` / `runtime_state`에는 wiring을 추가하지 않았습니다.
- `tests/test_pipeline_gui_backend.py:1135`는 더 이상 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator를 갖지 않습니다. 바로 이어지는 `test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`는 shipped thin-reader `read_runtime_status` against raw JSON pass-through assertions(`runtime_state == "RUNNING"`, `control.active_control_status == "implement"`, `lanes[0].state == "READY"`)로 clean pass 했습니다.
- `tests.test_pipeline_gui_backend` baseline은 `OK (skipped=11)`에서 `OK (skipped=10)`으로 바뀌었습니다. 즉 새 helper 노출과 unskip된 한 셀 pass만 추가됐고, 나머지 10개 `pipeline_gui_backend_state_transition_deferred` skip은 그대로 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465 shipped surfaces는 의도적으로 수정하지 않았습니다. 특히 `read_runtime_status` / `runtime_state` thin-reader contract, 나머지 10개 skip decorator, `tests/test_web_app`, `tests/test_smoke`, client/serializer/Playwright는 모두 미편집입니다. 이번 라운드는 advice 467을 G5-unskip-A 한 셀 범위로만 구현했습니다.

## 검증
- `rg -n '_supervisor_pid|_pid_is_alive' pipeline_gui/`
  - 결과: 4건 hit
  - `pipeline_gui/backend.py:560` `_supervisor_pid` definition
  - `pipeline_gui/backend.py:580` `_pid_is_alive` definition
  - `pipeline_gui/backend.py:594` `_supervisor_pid(project)` call inside `supervisor_alive`
  - `pipeline_gui/backend.py:597` `_pid_is_alive(pid)` call inside `supervisor_alive`
- `rg -n '_supervisor_pid|_pid_is_alive' tests/test_pipeline_gui_backend.py`
  - 결과: 6건 hit
  - `631`, `632`, `929`, `1192`, `1193` mock.patch references
  - `1019` existing method name `test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous`
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 10건 hit
  - line: `594`, `644`, `719`, `794`, `869`, `947`, `1018`, `1067`, `1202`, `1264`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 10건 hit
  - stable deferred decorators는 10개로 감소했습니다.
- `rg -n 'def supervisor_alive' pipeline_gui/backend.py`
  - 결과: 1건 hit
  - `pipeline_gui/backend.py:592`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.100s`, `OK (skipped=10)`
  - baseline `OK (skipped=11)`에서 post-edit `OK (skipped=10)`으로 바뀌었고, 새 failures/errors는 없었습니다.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 1 test in 0.006s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.033s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.091s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.084s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드 범위 밖이라 실행하지 않았습니다.

## 남은 리스크
- `TestRuntimeStatusRead`의 10개 cell은 여전히 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 상태입니다. 후속 G5-unskip-B/C/... round에서 `STOPPING→STOPPED`, `RUNNING→BROKEN`, `RUNNING→DEGRADED`, `degraded_reason` vocabulary sub-family를 각각 bounded slice로 나눠 풀 수 있습니다.
- `_supervisor_pid` / `_pid_is_alive`는 이제 mockable module attribute로 존재하지만, `read_runtime_status`는 아직 이 helper들을 소비하지 않습니다. 이후 wiring slice는 specific cell unskip와 함께 실제 state-transition이 기대값을 만드는지 검증한 뒤 진행해야 합니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 모두 deferred 상태입니다.
- unrelated `tests.test_web_app`의 10개 `LocalOnlyHTTPServer` PermissionError cell은 그대로 열려 있습니다.
- 오늘(2026-04-20) docs-only round count는 계속 0입니다. 이번 라운드는 `pipeline_gui` + tests slice였습니다.
- dirty worktree의 다른 파일들은 이번 라운드에서 건드리지 않았습니다.
