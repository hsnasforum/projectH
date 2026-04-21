# 2026-04-20 pipeline gui helper unskip G5-unskip-thin-reader

## 변경 파일
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 471 handoff는 `tests/test_pipeline_gui_backend.py:594`의 `test_read_runtime_status_from_current_run_pointer`만 unskip하는 exact slice를 요구했습니다.
- 이 셀은 shipped thin-reader `read_runtime_status`가 이미 `current_run.json -> status.json` 포인터 체인을 그대로 읽는지 검증하는 happy-path이고, `pipeline_gui/backend.py`의 추가 wiring 없이 decorator 삭제만으로 통과 가능한 범위였습니다.
- advice 470은 이 대상을 `G5-unskip-B`라고 불렀지만, seq 469 메뉴에서 `G5-unskip-B`는 STOPPING→STOPPED state-transition rule을 뜻했습니다. 이번 shipped slice는 더 정확히 `G5-unskip-thin-reader`입니다.

## 핵심 변경
- `tests/test_pipeline_gui_backend.py:594`는 더 이상 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator를 갖지 않습니다. `test_read_runtime_status_from_current_run_pointer` 본문은 그대로 두었고, shipped thin-reader `read_runtime_status` against raw JSON pass-through assertions(`result is not None`, `run_id`, `runtime_state == "RUNNING"`)로 clean pass 했습니다.
- `pipeline_gui/backend.py`는 이번 라운드에서 의도적으로 수정하지 않았습니다. `_supervisor_pid`, `_pid_is_alive`, `supervisor_alive`, `read_runtime_status`, `runtime_state`에 state-transition wiring을 추가하지 않았습니다.
- 남은 9개 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator의 실제 post-edit line은 `:643`, `:718`, `:793`, `:868`, `:946`, `:1017`, `:1066`, `:1201`, `:1263`입니다.
- `tests.test_pipeline_gui_backend` baseline은 `OK (skipped=10)`에서 `OK (skipped=9)`로 줄었고, 이번 라운드의 추가 구현은 decorator 한 줄 삭제뿐이었습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468 shipped surfaces는 의도적으로 수정하지 않았습니다. `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, `pipeline_gui/backend.py`, `e2e/tests/*`, `docs/*.md`와 dirty worktree의 다른 파일들도 이번 라운드에서 건드리지 않았습니다.

## 검증
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 9건 hit
  - line: `643`, `718`, `793`, `868`, `946`, `1017`, `1066`, `1201`, `1263`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 9건 hit
- `rg -n 'pipeline_gui_backend_state_transition_deferred' pipeline_gui/ storage/ core/ app/`
  - 결과: 0건 hit
- `rg -n 'def test_read_runtime_status_from_current_run_pointer' tests/test_pipeline_gui_backend.py`
  - 결과: 1건 hit (`:594`)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.039s`, `OK (skipped=9)`
  - baseline `OK (skipped=10)` -> post-edit `OK (skipped=9)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer`
  - 결과: `Ran 1 test in 0.003s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.015s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.063s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.052s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `TestRuntimeStatusRead`의 9개 cell은 여전히 stable reason string `pipeline_gui_backend_state_transition_deferred`로 skip 상태입니다. 후속 G5-unskip-* 라운드는 sub-family별로 좁게 풀 수 있지만, 실제 feature work는 `read_runtime_status` 안의 state-transition wiring(RUNNING→BROKEN, STOPPING→STOPPED, RUNNING→DEGRADED, degraded_reason vocabulary)입니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 모두 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 10개 `LocalOnlyHTTPServer` PermissionError cell도 그대로 열려 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다. 이번 라운드는 test-file-only slice였습니다.
- dirty worktree 파일들은 그대로 남아 있으며, 이번 라운드는 `tests/test_pipeline_gui_backend.py` 외 파일을 추가로 수정하지 않았습니다.
