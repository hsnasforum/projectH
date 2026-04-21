# 2026-04-20 pipeline gui G5 degraded watcher only

## 변경 파일
- `pipeline_gui/backend.py`
- `tests/test_pipeline_gui_backend.py`

## 사용 skill
- `work-log-closeout`: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 495까지는 `:1012` recent_active_lane만 DEGRADED로 풀렸고, `:1256` watcher_only_alive_without_pid는 여전히 skip 상태였습니다.
- seq 498 handoff는 branch 수를 더 늘리지 않고, 기존 DEGRADED branch guard를 넓혀 `:1012`와 `:1256`을 같은 `"supervisor_missing_recent_ambiguous"` reason 아래에서 함께 처리하라고 고정했습니다.

## 핵심 변경
- `pipeline_gui/backend.py:141-160`의 기존 DEGRADED branch guard를 broaden했습니다. 새 OR disjunct `(watcher.get("alive") and not watcher.get("pid"))`를 넣어, 기존 `:1012`의 "watcher 없음 + active lane" ambiguity뿐 아니라 `:1256`의 "watcher.alive=True + pid 없음" ambiguity도 같은 branch에서 처리하게 했습니다.
- 위 broadening은 guard만 바꿨고 branch body는 그대로 유지했습니다. `runtime_state`, `degraded_reason`, `degraded_reasons`만 rewrite하며 `watcher`, `control`, `active_round`, `lanes`는 건드리지 않습니다.
- NO new branch was added. `normalize_runtime_status`의 dispatch count는 STOPPING + BROKEN + broadened DEGRADED + RUNNING→BROKEN + quiescent의 5-branch 그대로입니다.
- `tests/test_pipeline_gui_backend.py:1256`의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 한 줄만 제거해 `test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous`를 unskip했습니다.
- post-edit 기준 broadened guard 경계는 `pipeline_gui/backend.py:141-160`, 남은 single skip decorator는 `tests/test_pipeline_gui_backend.py:1194`입니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495 shipped surfaces는 의도적으로 더 수정하지 않았습니다.

## 검증
- `rg -n 'supervisor_missing_recent_ambiguous' pipeline_gui/backend.py`
  - 결과: 2건 hit (`:158`, `:159`)
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 1건 hit (`:1194`)
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 1건 hit (`:1194`)
- `rg -n 'if supervisor_missing and runtime_state' pipeline_gui/backend.py`
  - 결과: 3건 hit (`:96`, `:119`, `:161`)
- `rg -n 'watcher.get\("pid"\)' pipeline_gui/backend.py`
  - 결과: 2건 hit (`:153`, `:188`)
  - handoff의 기대치는 1건이었지만, 기존 quiescent block의 `watcher.get("pid") in {None, ""}`가 이미 `:188`에 있어 총 2건입니다. broadening 적용 여부는 새 hit `:153`으로 확인했습니다.
- `rg -n 'snapshot_age' pipeline_gui/backend.py`
  - 결과: 3건 hit (`:95`, `:144`, `:145`)
- `rg -n 'SNAPSHOT_STALE_THRESHOLD' pipeline_gui/backend.py`
  - 결과: 2건 hit (`:35`, `:145`)
- `rg -n 'has_active_surface' pipeline_gui/backend.py`
  - 결과: 0건 hit
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.126s`, `OK (skipped=1)`
  - baseline transition: `OK (skipped=2) -> OK (skipped=1)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous`
  - 결과: `Ran 1 test in 0.004s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`
  - 결과: `Ran 3 tests in 0.012s`, `OK`
  - `:1012` seq 495는 first disjunct로 계속 DEGRADED입니다.
  - `:1062` aged counterpart는 age guard 덕분에 계속 BROKEN입니다.
  - `:865` seq 483은 `watcher.alive=True AND pid=4242`라서 새 disjunct에 걸리지 않고 계속 BROKEN입니다.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 6 tests in 0.024s`, `OK`
  - 다른 6개 previously-unskipped cell도 계속 green입니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.021s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.077s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.089s`, `OK`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `tests/test_pipeline_gui_backend.py:1194`의 `undated_ambiguous_snapshot_degraded` 1개만 아직 `@unittest.skip` 상태입니다. 이 셀은 `snapshot_age is None` undated path와 `degraded_reason="supervisor_missing_snapshot_undated"`라는 별도 literal이 필요해서, 현재 `:141` branch를 넓히는 것만으로는 처리할 수 없습니다.
- `normalize_runtime_status`는 여전히 STOPPING + BROKEN + broadened DEGRADED + RUNNING→BROKEN + quiescent의 5-branch 구조입니다. 다음 `:1194` 슬라이스는 6번째 branch를 추가하거나, 현재 DEGRADED branch를 reason-switch까지 포함해 다시 넓혀야 하므로 `G12 _apply_shutdown_shape` refactor leverage가 더 커졌습니다.
- future DEGRADED slices는 계속 `supervisor_missing + RUNNING` currently-green cell 전체와 비교하면서 trigger를 넓혀야 합니다. seq 492 regression이 그 교훈입니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 라운드 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다.
- dirty worktree의 다른 변경은 그대로 두었고, 이번 라운드는 target slice 두 파일만 추가 수정했습니다.
