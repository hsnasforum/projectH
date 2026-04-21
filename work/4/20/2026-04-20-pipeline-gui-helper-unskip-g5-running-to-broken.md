# 2026-04-20 pipeline gui helper unskip G5-running-to-broken

## 변경 파일
- pipeline_gui/backend.py
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 480 handoff는 `supervisor_missing` 판정을 PID-file 존재 여부에서 실제 PID liveness 기준으로 넓히고, `RUNNING` 상태에서 supervisor가 없으면 `BROKEN`으로 전이하는 새 분기를 추가한 뒤 `test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing` 한 셀만 unskip하라고 요구했습니다.
- 이번 라운드는 same-family G5-unskip 진행으로, zombie supervisor처럼 pid file은 남아 있어도 프로세스가 죽은 경우까지 거짓 `RUNNING` 표시를 줄이려는 smallest slice입니다.

## 핵심 변경
- `pipeline_gui/backend.py:90`의 `supervisor_missing`은 이제 `_supervisor_pid(project) is None` 대신 `not supervisor_alive(project)[0]`를 사용합니다. 이로써 missing pid file뿐 아니라 dead-PID zombie case도 같은 조건으로 잡습니다.
- `pipeline_gui/backend.py:136-158`에 새 RUNNING→BROKEN 분기를 추가했습니다. `supervisor_missing AND runtime_state == "RUNNING"`일 때 `runtime_state`를 `"BROKEN"`으로 바꾸고, 나머지 diagnostic/control/active_round/watcher/lane rewrite는 seq 477 BROKEN branch와 같은 `supervisor_missing` shape를 적용합니다. lane은 `state="BROKEN"`, `attachable=False`, `pid=None`, `note="supervisor_missing"`로 강제한 뒤 early-return 합니다.
- 기존 STOPPING branch(`:91-113`)와 seq 477 BROKEN branch(`:114-135`), quiescent block(`:159-187`)은 그대로 유지했습니다. 이번 라운드는 새 RUNNING branch만 추가했고, 기존 분기 내용은 바꾸지 않았습니다.
- `tests/test_pipeline_gui_backend.py:643`(post-edit method line)은 이제 `test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing` 본문만 남고 skip decorator가 제거됐습니다. 남은 6개 skip decorator의 실제 post-edit line은 `:865`, `:943`, `:1014`, `:1063`, `:1198`, `:1260`입니다.
- seq 468 / 471 / 474 / 477에서 unskip된 셀(`test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`, `test_read_runtime_status_from_current_run_pointer`, `test_read_runtime_status_converts_stopping_without_supervisor_into_stopped`, `test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing`)은 이번 widening과 RUNNING→BROKEN 분기 추가 이후에도 모두 green을 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477 shipped surfaces는 의도적으로 더 수정하지 않았습니다. `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, `e2e/tests/*`, `docs/*.md`와 dirty worktree의 다른 파일도 이번 라운드에서 건드리지 않았습니다.

## 검증
- `rg -n 'supervisor_alive\\(project\\)' pipeline_gui/backend.py`
  - 결과: 1건 hit (`:90`)
  - handoff 설명상 definition까지 기대할 수 있었지만, 실제 regex는 exact `supervisor_alive(project)` 형태만 잡아서 call site만 매치됐습니다.
- `rg -n '"note": "supervisor_missing"' pipeline_gui/backend.py`
  - 결과: 2건 hit (`:131`, `:154`)
- `rg -n '"note": "stopped"' pipeline_gui/backend.py`
  - 결과: 1건 hit (`:109`)
- `rg -n 'supervisor_missing' pipeline_gui/backend.py`
  - 결과: 10건 hit
  - line: `90`, `91`, `114`, `115`, `116`, `131`, `136`, `138`, `139`, `154`
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 6건 hit
  - line: `865`, `943`, `1014`, `1063`, `1198`, `1260`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 6건 hit
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.062s`, `OK (skipped=6)`
  - baseline `OK (skipped=7)` -> post-edit `OK (skipped=6)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing`
  - 결과: `Ran 1 test in 0.004s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 4 tests in 0.019s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.029s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.096s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.066s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `TestRuntimeStatusRead`의 6개 cell은 여전히 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 상태입니다. future G5-unskip-* sub-family는 다음과 같습니다.
  - `:865` `recent_quiescent_running_status_broken_without_supervisor` — RUNNING→BROKEN with quiescent-evidence refinement
  - `:943` `converts_aged_ambiguous_snapshot_into_broken` — age-based trigger
  - `:1014` `recent_field_quiescent_running_status_broken_without_pids` — field-quiescent + no pids
  - `:1063` `recent_active_lane_without_supervisor_pid_degraded_ambiguous` — expects DEGRADED
  - `:1198` `undated_ambiguous_snapshot_degraded` — expects DEGRADED
  - `:1260` `watcher_only_alive_without_pid_degraded_ambiguous` — expects DEGRADED
- **DEGRADED family collision**: 이번 새 blanket RUNNING→BROKEN rule은 supervisor가 없으면 `:1063`, `:1198`, `:1260`의 DEGRADED-family fixture에도 먼저 발화할 수 있습니다. 이번 라운드에서는 셋 다 아직 skipped라 green이지만, future DEGRADED slice에서는 RUNNING→BROKEN branch보다 앞에 더 좁은 DEGRADED branch를 넣어 recent-active-lane / undated / watcher-only-alive 신호를 구분해야 합니다.
- branch duplication이 3개(STOPPING + BROKEN + RUNNING→BROKEN, plus quiescent)까지 늘었습니다. 4번째 similar-shape branch가 추가되면 `_apply_shutdown_shape(status, lanes, *, runtime_state_override, lane_state, lane_note, degraded_reason, degraded_reasons)` 같은 shared helper 검토가 필요할 수 있지만, 이번 라운드에서는 도입하지 않았습니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 10개 `LocalOnlyHTTPServer` PermissionError cell도 그대로 열려 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다.
- dirty worktree 파일들은 그대로 남아 있으며, 이번 라운드에서도 targeted file 외 다른 변경은 추가하지 않았습니다.
