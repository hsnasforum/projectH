# 2026-04-20 pipeline gui helper unskip G5-degraded-reason

## 변경 파일
- pipeline_gui/backend.py
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 477 handoff는 seq 474의 STOPPING normalization 패턴 바로 뒤에 BROKEN 전용 supervisor-missing branch를 추가하고, `test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing` 한 셀만 unskip하라고 요구했습니다.
- 이번 라운드는 same-family G5-unskip 진행으로, raw BROKEN payload의 진단 필드가 supervisor 부재 상황을 더 정직하게 반영하도록 normalize하는 smallest slice입니다.

## 핵심 변경
- `pipeline_gui/backend.py`의 `normalize_runtime_status`에는 STOPPING branch 직후 BROKEN branch가 새로 들어갔습니다. 새 분기는 `:114-135`에 있고, `supervisor_missing AND runtime_state == "BROKEN"`일 때만 실행됩니다. 여기서는 `runtime_state`는 그대로 `"BROKEN"`으로 두고, `degraded_reason`, `degraded_reasons`, `control`, `active_round`, `watcher`, `lanes`를 재작성하며 lane마다 `state="BROKEN"`, `attachable=False`, `pid=None`, `note="supervisor_missing"`를 강제한 뒤 early-return 합니다.
- 기존 STOPPING branch(`:91-113`)와 quiescent block(`:136-163`)은 그대로 유지했습니다. `"note": "stopped"`는 seq 474 STOPPING branch에만 남아 있고, `"note": "supervisor_missing"`는 이번 BROKEN branch에만 추가되었습니다.
- `tests/test_pipeline_gui_backend.py:792`(post-edit method line)은 이제 `test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing` 본문만 남고 skip decorator가 제거됐습니다. 남은 7개 skip decorator의 실제 post-edit line은 `:643`, `:866`, `:944`, `:1015`, `:1064`, `:1199`, `:1261`입니다.
- seq 468 / 471 / 474에서 unskip된 셀(`test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`, `test_read_runtime_status_from_current_run_pointer`, `test_read_runtime_status_converts_stopping_without_supervisor_into_stopped`)은 이번 BROKEN branch 추가 이후에도 모두 green을 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474 shipped surfaces는 의도적으로 더 수정하지 않았습니다. `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, `e2e/tests/*`, `docs/*.md`와 dirty worktree의 다른 파일도 이번 라운드에서 건드리지 않았습니다.

## 검증
- `rg -n '"note": "supervisor_missing"' pipeline_gui/backend.py`
  - 결과: 1건 hit (`:131`)
- `rg -n '"note": "stopped"' pipeline_gui/backend.py`
  - 결과: 1건 hit (`:109`)
- `rg -n 'supervisor_missing' pipeline_gui/backend.py`
  - 결과: 6건 hit
  - line: `90`, `91`, `114`, `115`, `116`, `131`
  - handoff의 대략 예상치(`~4`)보다 많이 나온 이유는 `supervisor_missing` 식별자가 assignment와 두 개의 branch condition에도 반복되기 때문입니다.
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 7건 hit
  - line: `643`, `866`, `944`, `1015`, `1064`, `1199`, `1261`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 7건 hit
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.045s`, `OK (skipped=7)`
  - baseline `OK (skipped=8)` -> post-edit `OK (skipped=7)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing`
  - 결과: `Ran 1 test in 0.004s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 3 tests in 0.010s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.017s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.070s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.058s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `TestRuntimeStatusRead`의 7개 cell은 여전히 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 상태입니다. future G5-unskip-* sub-family로는 stale_RUNNING_BROKEN(`:643`), aged_ambiguous → BROKEN(`:944`), recent_field_quiescent_running → BROKEN(`:1015`), recent_active_lane → DEGRADED(`:1064`), undated_ambiguous → DEGRADED(`:1199`), watcher_only_alive → DEGRADED(`:1261`), 그 외 remaining BROKEN variants(`:866`)가 남아 있습니다. 일부는 snapshot age 계산 같은 별도 trigger가 필요합니다.
- `note: "supervisor_missing"`(이번 BROKEN branch)와 `note: "stopped"`(seq 474 STOPPING branch)는 의도적으로 비대칭입니다. 현재 테스트 기대값과 맞지만, 서로 다른 post-normalization lane intent가 문서화된 상태라는 점을 계속 염두에 둬야 합니다.
- `normalize_runtime_status` 안의 STOPPING + BROKEN + quiescent branch는 중복 rewrite block이 점점 늘고 있습니다. G5-unskip-*가 더 진행돼 같은 패턴의 세 번째 유사 분기가 명확해지면 `_apply_shutdown_shape(status, lanes, *, runtime_state_override, lane_state, lane_note)` 같은 shared helper를 검토할 수 있지만, 지금 라운드에서는 도입하지 않았습니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 10개 `LocalOnlyHTTPServer` PermissionError cell도 그대로 열려 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다.
- dirty worktree 파일들은 그대로 남아 있으며, 이번 라운드에서도 targeted file 외 다른 변경은 추가하지 않았습니다.
