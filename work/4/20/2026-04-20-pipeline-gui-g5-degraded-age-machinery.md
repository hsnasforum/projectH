# 2026-04-20 pipeline gui G5 degraded age machinery

## 변경 파일
- `pipeline_gui/backend.py`
- `tests/test_pipeline_gui_backend.py`

## 사용 skill
- `work-log-closeout`: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 492의 non-age narrow trigger는 `:1012` recent DEGRADED와 `:1062` aged BROKEN을 구분하지 못해 `FAILED (failures=1, skipped=2)`를 만들었습니다.
- seq 495 handoff는 advice 494를 따라 `parse_iso_utc` 기반 age discriminator를 되살리되, `:1012` 한 셀만 unskip하고 `:1195`, `:1257`은 그대로 defer하라고 고정했습니다.

## 핵심 변경
- `pipeline_gui/backend.py:13`의 기존 `pipeline_runtime.schema` import에 `parse_iso_utc`를 추가했고, module-level constant `SNAPSHOT_STALE_THRESHOLD = 15.0`를 `pipeline_gui/backend.py:35`에 추가했습니다.
- `normalize_runtime_status` 안에 `updated_at_raw` / `snapshot_ts` / `snapshot_age` 계산을 `pipeline_gui/backend.py:93-95`에 넣었습니다. `updated_at`이 비어 있거나 invalid면 `parse_iso_utc(...) == 0.0`이므로 `snapshot_age = None`으로 떨어집니다.
- seq 477 BROKEN return 뒤와 seq 480 RUNNING→BROKEN guard 앞 사이에 새 narrow DEGRADED branch를 `pipeline_gui/backend.py:141-152`에 추가했습니다. guard는 `supervisor_missing AND runtime_state == "RUNNING" AND not watcher.get("alive") AND any lane state != "OFF" AND snapshot_age is not None AND snapshot_age <= SNAPSHOT_STALE_THRESHOLD`이고, rewrite는 `runtime_state`, `degraded_reason`, `degraded_reasons` 3개만 수행하며 `lanes` / `control` / `active_round` / `watcher`는 그대로 둡니다.
- `tests/test_pipeline_gui_backend.py:1012` 앞의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 한 줄만 제거해 `test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous`를 unskip했습니다. 남은 skip decorator는 `tests/test_pipeline_gui_backend.py:1194`, `tests/test_pipeline_gui_backend.py:1256`입니다.
- advice 491의 3-cell-at-once scope, `has_active_surface` helper, lane rewrite (`pid=None`, `attachable=False`)는 계속 거부했습니다. 이번 라운드는 advice 494가 복권한 age machinery 부분만 재도입했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489 shipped surfaces는 의도적으로 더 수정하지 않았습니다.

## 검증
- `rg -n 'parse_iso_utc' pipeline_gui/backend.py`
  - 결과: 2건 hit (`:13`, `:94`)
- `rg -n 'SNAPSHOT_STALE_THRESHOLD' pipeline_gui/backend.py`
  - 결과: 2건 hit (`:35`, `:147`)
- `rg -n 'supervisor_missing_recent_ambiguous' pipeline_gui/backend.py`
  - 결과: 2건 hit (`:150`, `:151`)
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 2건 hit (`:1194`, `:1256`)
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 2건 hit (`:1194`, `:1256`)
- `rg -n 'if supervisor_missing and runtime_state' pipeline_gui/backend.py`
  - 결과: 3건 hit (`:96`, `:119`, `:153`)
- `rg -n 'snapshot_age' pipeline_gui/backend.py`
  - 결과: 3건 hit (`:95`, `:146`, `:147`)
- `rg -n 'has_active_surface' pipeline_gui/backend.py`
  - 결과: 0건 hit
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.126s`, `OK (skipped=2)`
  - baseline transition: `OK (skipped=3) -> OK (skipped=2)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous`
  - 결과: `Ran 1 test in 0.006s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`
  - 결과: `Ran 1 test in 0.003s`, `OK`
  - critical counterpart `:1062 aged_ambiguous`는 이번 라운드에서도 `BROKEN`으로 유지됐습니다.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 7 tests in 0.029s`, `OK`
  - 다른 7개 previously-unskipped cell도 계속 green입니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.018s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.080s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.002s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.073s`, `OK`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `@unittest.skip`가 남은 DEGRADED cell은 2개입니다.
  - `tests/test_pipeline_gui_backend.py:1194` `undated_ambiguous_snapshot_degraded`: `snapshot_age is None`인 undated guard path가 따로 필요합니다. 이번 branch의 `snapshot_age is not None` guard가 이 셀을 의도적으로 제외합니다.
  - `tests/test_pipeline_gui_backend.py:1256` `watcher_only_alive_without_pid_degraded_ambiguous`: `watcher.alive=True AND watcher.pid in {None, ""}` 쪽 differentiator가 따로 필요합니다. 이번 branch의 `not watcher.get("alive")` guard가 이 셀을 의도적으로 제외합니다.
- future DEGRADED slices는 각자 narrow trigger가 필요합니다. 3개 DEGRADED variant를 비교표로 다시 고정하기 전에는 unified branch를 다시 시도하면 안 됩니다. seq 492 collision이 그 반례입니다.
- `normalize_runtime_status`는 이제 STOPPING + BROKEN + new DEGRADED + RUNNING→BROKEN + quiescent의 5-branch 구조입니다. 남은 2개 DEGRADED variant를 넣기 전 `G12 _apply_shutdown_shape` refactor leverage가 더 커졌습니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 라운드 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다.
- dirty worktree의 다른 변경은 그대로 두었고, 이번 라운드는 target slice 두 파일만 추가 수정했습니다.
