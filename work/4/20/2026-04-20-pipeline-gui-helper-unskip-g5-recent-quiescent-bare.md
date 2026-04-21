# 2026-04-20 pipeline gui helper unskip G5-recent-quiescent-bare

## 변경 파일
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 483 handoff는 `test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`가 이미 seq 480의 RUNNING→BROKEN 규칙으로 커버되므로, backend 수정 없이 skip decorator 한 줄만 제거하라고 요구했습니다.
- 이번 라운드는 same-family G5-unskip 진행으로, 기존 상태 전이 규칙이 추가 구현 없이도 통과시키는 셀을 decorator-only로 복구하는 smallest slice입니다.

## 핵심 변경
- `tests/test_pipeline_gui_backend.py:865`(pre-edit)의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")`는 이제 제거됐고, `test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`가 그대로 통과합니다. advice 482는 `:866`을 가리켰지만, 그 줄은 method def이고 실제 decorator 위치는 `:865`였습니다.
- `pipeline_gui/backend.py`는 이번 라운드에서 의도적으로 수정하지 않았습니다. seq 480 RUNNING→BROKEN branch가 이미 이 테스트의 기대값을 모두 만족하므로 backend change는 0건입니다.
- 남은 5개 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator의 실제 post-edit line은 `:942`, `:1013`, `:1062`, `:1197`, `:1259`입니다.
- `tests.test_pipeline_gui_backend` baseline은 `OK (skipped=6)`에서 `OK (skipped=5)`로 줄었고, 신규 구현은 테스트 파일의 decorator 한 줄 삭제뿐이었습니다.
- seq 480 / 477 / 474 / 471 / 468 previously-unskipped cells는 이번 라운드 이후에도 모두 green을 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480 shipped surfaces는 의도적으로 더 수정하지 않았습니다. `pipeline_gui/backend.py`, `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, `e2e/tests/*`, `docs/*.md`와 dirty worktree의 다른 파일도 이번 라운드에서 건드리지 않았습니다.

## 검증
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 5건 hit
  - line: `942`, `1013`, `1062`, `1197`, `1259`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 5건 hit
- `rg -n 'pipeline_gui_backend_state_transition_deferred' pipeline_gui/ storage/ core/ app/`
  - 결과: 0건 hit
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.063s`, `OK (skipped=5)`
  - baseline `OK (skipped=6)` -> post-edit `OK (skipped=5)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`
  - 결과: `Ran 1 test in 0.004s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 5 tests in 0.015s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.023s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.083s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.063s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `TestRuntimeStatusRead`의 5개 cell은 여전히 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 상태입니다.
  - `:942` `converts_aged_ambiguous_snapshot_into_broken` — age-based trigger
  - `:1013` `recent_field_quiescent_running_status_broken_without_pids` — seq 480과 비슷하게 이미 커버될 수 있음; assertion inspection 필요
  - `:1062` `recent_active_lane_without_supervisor_pid_degraded_ambiguous` — DEGRADED, seq 480 broad rule과 충돌
  - `:1197` `undated_ambiguous_snapshot_degraded` — DEGRADED, 충돌
  - `:1259` `watcher_only_alive_without_pid_degraded_ambiguous` — DEGRADED, 충돌
- DEGRADED-family collision은 여전히 미해결입니다. `:1062`, `:1197`, `:1259`는 supervisor_missing이면 seq 480 RUNNING→BROKEN branch에 먼저 잡힐 수 있으므로, future DEGRADED slice에서는 그 앞에 더 좁은 DEGRADED branch를 넣어 recent-active-lane / undated / watcher-only-alive 신호를 구분해야 합니다.
- branch duplication은 여전히 3개 수준입니다. G12 `_apply_shutdown_shape` refactor는 4번째 유사 분기가 추가될 때 검토 후보로 남아 있습니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 10개 `LocalOnlyHTTPServer` PermissionError cell도 그대로 열려 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다.
- dirty worktree 파일들은 그대로 남아 있으며, 이번 라운드에서도 targeted file 외 다른 변경은 추가하지 않았습니다.
