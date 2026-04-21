# 2026-04-20 pipeline gui helper unskip G5-aged-ambiguous-bare

## 변경 파일
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 486 handoff는 `test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`가 이미 seq 480의 RUNNING→BROKEN 규칙으로 커버되므로, backend 수정 없이 skip decorator 한 줄만 제거하라고 요구했습니다.
- 이번 라운드는 same-family G5-unskip 진행으로, advice 485의 age machinery 제안을 배제하고 decorator-only로 복구 가능한 셀만 좁게 닫는 smallest slice입니다.

## 핵심 변경
- `tests/test_pipeline_gui_backend.py:1062`(pre-edit)의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")`는 이제 제거됐고, `test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`가 seq 480 RUNNING→BROKEN branch 위에서 그대로 통과합니다. 이번 라운드의 backend change는 0건입니다.
- `pipeline_gui/backend.py`는 이번 라운드에서 의도적으로 수정하지 않았습니다.
- advice 485가 제안한 age machinery(`parse_iso_utc` import, `SNAPSHOT_STALE_THRESHOLD = 15.0`, `snapshot_age` 계산, RUNNING→BROKEN bifurcation)는 verify/handoff owner가 배제했습니다. 이유는 (i) `:1062`의 7개 assertion이 이미 seq 480 shipped output과 bit-for-bit로 맞고, (ii) 그 bifurcation을 넣으면 seq 483의 `:865` green cell과 `:942`의 lane-preservation intent를 깨뜨릴 수 있기 때문입니다.
- 남은 4개 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` decorator의 실제 post-edit line은 `:942`, `:1013`, `:1196`, `:1258`입니다.
- 남은 4개 cell의 corrected method mapping은 다음과 같습니다.
  - `:942` = `recent_field_quiescent_running_status_broken_without_pids`
  - `:1013` = `recent_active_lane_without_supervisor_pid_degraded_ambiguous`
  - `:1196` = `undated_ambiguous_snapshot_degraded`
  - `:1258` = `watcher_only_alive_without_pid_degraded_ambiguous`
- seq 483 / 480 / 477 / 474 / 471 / 468 previously-unskipped cells는 이번 라운드 이후에도 모두 green을 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483 shipped surfaces는 의도적으로 더 수정하지 않았습니다. `pipeline_gui/backend.py`, `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, `e2e/tests/*`, `docs/*.md`와 dirty worktree의 다른 파일도 이번 라운드에서 건드리지 않았습니다.

## 검증
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 4건 hit
  - line: `942`, `1013`, `1196`, `1258`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 4건 hit
- `rg -n 'pipeline_gui_backend_state_transition_deferred' pipeline_gui/ storage/ core/ app/`
  - 결과: 0건 hit
- `rg -n 'SNAPSHOT_STALE_THRESHOLD|parse_iso_utc' pipeline_gui/backend.py`
  - 결과: 0건 hit
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.066s`, `OK (skipped=4)`
  - baseline `OK (skipped=5)` -> post-edit `OK (skipped=4)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`
  - 결과: `Ran 1 test in 0.004s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 6 tests in 0.021s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.021s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.065s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.062s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `TestRuntimeStatusRead`의 4개 cell은 여전히 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 상태입니다.
  - `:942` `recent_field_quiescent_running_status_broken_without_pids` — lane-preservation logic 필요. 현재 seq 480은 lane state를 `BROKEN`으로 바꾸지만, 이 fixture는 lane state가 `OFF`로 유지되길 기대합니다.
  - `:1013` `recent_active_lane_without_supervisor_pid_degraded_ambiguous` — DEGRADED, seq 480 collision으로 막힘
  - `:1196` `undated_ambiguous_snapshot_degraded` — DEGRADED, 막힘
  - `:1258` `watcher_only_alive_without_pid_degraded_ambiguous` — DEGRADED, 막힘
- DEGRADED-family collision은 여전히 미해결입니다. `:1013`, `:1196`, `:1258`는 supervisor_missing이면 seq 480 RUNNING→BROKEN branch에 먼저 잡힐 수 있으므로, future DEGRADED slice에서는 그 앞에 더 좁은 DEGRADED branch를 넣어야 합니다.
- advice 485의 age-bifurcation 아이디어는 이번 라운드에서는 배제됐지만, future DEGRADED family에서 정말 필요한 fixture가 나오면 다시 검토할 수 있습니다. 다만 그때도 먼저 각 DEGRADED 테스트 fixture를 개별로 확인해야 합니다.
- branch duplication은 여전히 3개 수준입니다. G12 `_apply_shutdown_shape` refactor는 계속 후보입니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 10개 `LocalOnlyHTTPServer` PermissionError cell도 그대로 열려 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다.
- dirty worktree 파일들은 그대로 남아 있으며, 이번 라운드에서도 targeted file 외 다른 변경은 추가하지 않았습니다.
