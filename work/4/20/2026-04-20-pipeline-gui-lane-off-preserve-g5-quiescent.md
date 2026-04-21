# 2026-04-20 pipeline gui lane OFF preserve G5-quiescent

## 변경 파일
- pipeline_gui/backend.py
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 489 handoff는 `pipeline_gui/backend.py`의 supervisor-missing `BROKEN`/`RUNNING→BROKEN` lane rewrite 두 곳만 조정하고, `tests/test_pipeline_gui_backend.py`의 G5-quiescent skip 하나만 해제하라고 요구했습니다.
- seq 480 규칙은 lane state를 일괄 `BROKEN`으로 덮어써서, quiescent fixture가 기대하는 `lanes[0].state == "OFF"`를 깨고 pre-edit `:942` cell을 계속 skip 상태로 남겨두고 있었습니다.

## 핵심 변경
- `pipeline_gui/backend.py:128`, `pipeline_gui/backend.py:151`은 이제 둘 다 `lane.get("state") if str(lane.get("state") or "") == "OFF" else "BROKEN"`를 사용합니다. 그래서 input lane state가 `"OFF"`면 그대로 보존하고, 그 외에는 `"BROKEN"`으로 정규화합니다.
- 위 두 branch는 lane `state`만 조건부로 바꾸고, 다른 lane field(`attachable=False`, `pid=None`, `note="supervisor_missing"`)는 이전처럼 계속 무조건 rewrite합니다.
- pre-edit `tests/test_pipeline_gui_backend.py:942`의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")`는 제거됐고, `test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids`가 RUNNING→BROKEN 보정 후에도 `lanes[0].state == "OFF"`를 유지하면서 통과합니다.
- 남은 skip/deferred decorator의 post-edit line은 `tests/test_pipeline_gui_backend.py:1012`, `tests/test_pipeline_gui_backend.py:1195`, `tests/test_pipeline_gui_backend.py:1257`이고, 둘 다 count는 3건입니다.
- grep 기준으로 `pipeline_gui/backend.py`의 literal `"state": "BROKEN"` hit는 0건, 새 conditional hit는 2건, `"state": "OFF"` hit는 2건, `SNAPSHOT_STALE_THRESHOLD|parse_iso_utc` hit는 0건이었습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486 shipped surfaces는 이번 라운드에서도 lane-state refinement 외 추가 수정 없이 그대로 두었습니다. STOPPING branch, quiescent block, `supervisor_missing` helper, `read_runtime_status`의 다른 경로도 더 건드리지 않았습니다.

## 검증
- `rg -n '"state": "BROKEN"' pipeline_gui/backend.py`
  - 결과: 0건 hit
- `rg -n 'lane.get\("state"\) if str\(lane.get\("state"\)' pipeline_gui/backend.py`
  - 결과: 2건 hit
  - line: `128`, `151`
- `rg -n '"state": "OFF"' pipeline_gui/backend.py`
  - 결과: 2건 hit
  - line: `106`, `181`
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 3건 hit
  - line: `1012`, `1195`, `1257`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 3건 hit
- `rg -n 'SNAPSHOT_STALE_THRESHOLD|parse_iso_utc' pipeline_gui/backend.py`
  - 결과: 0건 hit
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.086s`, `OK (skipped=3)`
  - baseline transition: prior round `OK (skipped=4)` -> 이번 라운드 `OK (skipped=3)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids`
  - 결과: `Ran 1 test in 0.005s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 7 tests in 0.020s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.021s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.080s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.068s`, `OK`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- baseline transition과 handoff 지정 regression cell은 모두 green으로 유지됐습니다.

## 남은 리스크
- `tests/test_pipeline_gui_backend.py:1012`, `tests/test_pipeline_gui_backend.py:1195`, `tests/test_pipeline_gui_backend.py:1257`의 3개 DEGRADED-family skip은 여전히 남아 있습니다.
- supervisor-missing recent/undated ambiguity를 `DEGRADED`로 남겨야 하는 collision은 아직 unresolved입니다. 이번 라운드는 `OFF` lane preservation만 닫았고, DEGRADED branch ordering 자체는 바꾸지 않았습니다.
- `pipeline_gui/backend.py`의 supervisor-missing transition branch duplication은 여전히 3개 수준입니다.
- G3 / G6 / G7 / G8 / G9 / G10 / G11 family는 계속 deferred 상태입니다.
- `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 라운드 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다.
- dirty worktree의 기존 변경은 그대로 두었고, 이번 라운드에서도 target slice 외 파일은 건드리지 않았습니다.
