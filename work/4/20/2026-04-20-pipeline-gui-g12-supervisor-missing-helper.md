# 2026-04-20 pipeline gui G12 supervisor missing helper

## 변경 파일
- `pipeline_gui/backend.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 검증, doc-sync 필요 여부, `/work` closeout readiness만 묶어 구현 라운드를 마감했습니다.

## 변경 이유
- `normalize_runtime_status`의 `supervisor_missing` 계열 4개 branch(STOPPING / BROKEN / broadened-DEGRADED / RUNNING→BROKEN)가 같은 shutdown-shape reset을 반복하고 있었고, seq 501까지 오면서 DEGRADED branch는 nested-OR guard와 ternary reason까지 품게 되어 다음 state-transition 수정의 diff surface가 더 커진 상태였습니다.
- 이번 슬라이스는 branch 순서나 의미를 바꾸지 않고 body만 공통 helper로 접어, 현재 green cell 11개를 그대로 유지한 채 중복된 reset 경로를 한 곳으로 모으는 순수 refactor가 목적이었습니다.

## 핵심 변경
- `pipeline_gui/backend.py:73-117`에 새 module-level helper `_apply_supervisor_missing_status(status, lanes, *, state, reason, shutdown=True)`를 추가했습니다. `lanes`는 `normalize_runtime_status`의 local filtered list를 그대로 받아 사용하고, `shutdown=True`일 때만 `control` / `active_round` / `watcher` / `lanes`를 reset합니다.
- STOPPING / BROKEN / broadened-DEGRADED / RUNNING→BROKEN branch body는 이제 모두 helper 호출로 바뀌었습니다.
  - STOPPING call site: `pipeline_gui/backend.py:144-149`
  - BROKEN call site: `pipeline_gui/backend.py:152-157`
  - broadened-DEGRADED call site: `pipeline_gui/backend.py:182-187`
  - RUNNING→BROKEN call site: `pipeline_gui/backend.py:190-195`
- broadened-DEGRADED branch는 `pipeline_gui/backend.py:177-187`에서 inline ternary `reason`은 그대로 유지하고, helper를 `shutdown=False`로 호출하도록 바꿨습니다. 그래서 `:1012` / `:1255` / `:1194`가 의존하는 `control.active_control_status`, `watcher.alive`, `lanes[0].state` 보존 동작은 그대로입니다.
- STOPPING / BROKEN / broadened-DEGRADED / RUNNING→BROKEN의 guard는 post-edit 기준 `pipeline_gui/backend.py:143`, `:151`, `:159-176`, `:189`에서 그대로 유지됐고, quiescent branch도 `pipeline_gui/backend.py:197-224`에서 unchanged입니다.
- 이번 라운드에서는 test file을 수정하지 않았습니다. `tests/test_pipeline_gui_backend.py`의 기존 dirty worktree 상태는 그대로 두고 read-only regression 기준으로만 사용했습니다.
- doc-sync triage 결과 없음: 이번 변경은 `pipeline_gui/backend.py` 내부 refactor만 수행했고 shipped UI/approval/doc contract를 바꾸지 않았습니다.

## 검증
- grep 확인
  - `rg -n 'def _apply_supervisor_missing_status' pipeline_gui/backend.py`
    - 결과: 1건 (`:73`)
  - `rg -n '_apply_supervisor_missing_status\(' pipeline_gui/backend.py`
    - 결과: 5건 (`:73` helper 정의 + `:144`, `:152`, `:182`, `:190` 4개 call site)
  - `rg -n 'supervisor_missing_recent_ambiguous' pipeline_gui/backend.py`
    - 결과: 1건 (`:180`)
  - `rg -n 'supervisor_missing_snapshot_undated' pipeline_gui/backend.py`
    - 결과: 1건 (`:178`)
  - `rg -n 'if supervisor_missing and runtime_state' pipeline_gui/backend.py`
    - 결과: 3건 (`:143`, `:151`, `:189`)
  - `rg -n 'watcher.get\("pid"\)' pipeline_gui/backend.py`
    - 결과: 2건 (`:173`, `:201`)
  - `rg -n 'snapshot_age is None' pipeline_gui/backend.py`
    - 결과: 2건 (`:163`, `:179`)
  - `rg -n 'snapshot_age' pipeline_gui/backend.py`
    - 결과: 4건 (`:142`, `:163`, `:164`, `:179`)
  - `rg -n '"supervisor_missing"' pipeline_gui/backend.py`
    - 결과: 2건 (`:156`, `:194`)
  - `rg -n '"active_control_file": ""' pipeline_gui/backend.py`
    - 결과: 2건 (`:87`, `:209`)
    - handoff 기대치는 1건이었지만, quiescent branch를 의도적으로 untouched로 유지해서 helper 내부 reset block과 quiescent branch reset block이 함께 잡혔습니다.
  - `rg -n 'status\["active_round"\] = None' pipeline_gui/backend.py`
    - 결과: 2건 (`:92`, `:214`)
    - handoff 기대치는 1건이었지만, 위와 같은 이유로 quiescent branch의 기존 assignment도 함께 남아 있습니다.
  - `rg -n '"alive": False, "pid": None' pipeline_gui/backend.py`
    - 결과: 2건 (`:93`, `:215`)
    - handoff 기대치는 1건이었지만, quiescent branch의 기존 watcher reset이 그대로 있어 총 2건입니다.
  - `rg -n 'has_active_surface' pipeline_gui/backend.py`
    - 결과: 0건
  - `rg -n 'def _degraded_reason' pipeline_gui/backend.py`
    - 결과: 0건
  - `rg -n 'def _apply_shutdown_shape' pipeline_gui/backend.py`
    - 결과: 0건
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.217s`, `OK`
  - baseline `OK (skipped=0)` 유지
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`
  - 결과: `Ran 4 tests in 0.016s`, `OK`
  - `:1194` undated DEGRADED, `:1255` watcher-only DEGRADED, `:1012` recent-active-lane DEGRADED, `:1060` aged BROKEN이 모두 유지됐습니다.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_normalize_runtime_status_drops_non_mapping_payload tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_normalize_runtime_status_converts_inactive_degraded_snapshot_to_stopped`
  - 결과: `Ran 8 tests in 0.024s`, `OK`
  - quiescent path direct-normalize까지 포함한 추가 regression set이 green으로 유지됐습니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.029s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.079s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.086s`, `OK`
- `python3 -m py_compile pipeline_gui/backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py`
  - 결과: 출력 없음, 통과
- `tests.test_web_app`, Playwright, `make e2e-test`는 handoff 범위 밖이라 실행하지 않았습니다.

## 남은 리스크
- helper 추출은 순수 refactor로 끝냈지만, quiescent branch는 일부러 helper에 합치지 않았기 때문에 `control` / `active_round` / `watcher` reset literal은 helper와 quiescent branch에 각각 1개씩 남아 있습니다. handoff grep 기대치 일부가 1건으로 적혀 있었지만, 실제 코드는 quiescent unchanged 조건과 함께 보면 2건이 정상입니다.
- `normalize_runtime_status`는 계속 5-branch(STOPPING + BROKEN + broadened-DEGRADED + RUNNING→BROKEN + quiescent)이고, branch precedence와 early return semantics는 유지됩니다. 이후 supervisor-missing 계열을 더 손댈 때도 이 순서는 그대로 비교해야 합니다.
- DEGRADED branch는 여전히 가장 복잡한 guard를 갖고 있고, ternary reason도 inline으로 남아 있습니다. 이번 라운드는 helper-level duplication만 줄였고, classification 자체를 새 helper로 분리하지는 않았습니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 구현 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree의 다른 파일은 건드리지 않았고, 이번 라운드의 추가 수정은 `pipeline_gui/backend.py` 한 파일에만 한정했습니다.
