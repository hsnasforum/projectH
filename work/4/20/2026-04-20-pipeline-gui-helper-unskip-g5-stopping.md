# 2026-04-20 pipeline gui helper unskip G5-stopping

## 변경 파일
- pipeline_gui/backend.py
- tests/test_pipeline_gui_backend.py

## 사용 skill
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 474 handoff는 `STOPPING` 상태에서 supervisor PID가 없으면 `read_runtime_status`가 raw status.json을 그대로 노출하지 말고, shutdown shape로 정규화한 뒤 `test_read_runtime_status_converts_stopping_without_supervisor_into_stopped`를 unskip하라고 요구했습니다.
- 이번 라운드는 G5-unskip-thin-reader 다음 same-family slice로, `read_runtime_status` 계약을 "raw thin reader"에서 "supervisor reality를 반영한 normalize reader"로 바꾸는 첫 state-transition rule 구현입니다.

## 핵심 변경
- `pipeline_gui/backend.py:71`의 `normalize_runtime_status`는 이제 `project: Path | None = None`을 받습니다. `project is not None`이고 `runtime_state == "STOPPING"`이며 `_supervisor_pid(project) is None`일 때만 full shutdown normalization을 적용하도록 `:90-113`에 새 분기를 추가했습니다. 이 분기는 `runtime_state`, `degraded_reason`, `degraded_reasons`, `control`, `active_round`, `watcher`, `lanes`를 모두 STOPPED shape로 바꾸고, lane마다 `"note": "stopped"`를 설정한 뒤 즉시 return 합니다.
- 기존 quiescent block은 그대로 유지했습니다. `pipeline_gui/backend.py:114-141`의 기존 STOPPED normalization은 수정하지 않았고, `"note": "stopped"` rewrite는 새 supervisor-missing STOPPING branch에만 있습니다.
- `pipeline_gui/backend.py:551-569`의 `read_runtime_status`는 이제 status JSON을 읽은 뒤 `normalize_runtime_status(data, project=project)`를 거쳐 반환합니다. status 파일이 없거나 invalid면 기존처럼 `None`을 그대로 유지합니다. 이로써 `read_runtime_status` 계약은 "raw JSON reader"에서 "supervisor reality를 반영해 normalize한 reader"로 바뀌었습니다.
- step 3 call-site convention cleanup은 **건너뛰었습니다**. `runtime_state` / `runtime_active`는 이미 `read_runtime_status(project)` 결과를 다시 `normalize_runtime_status(...)`에 넘기고 있고, 이번 slice의 correctness는 `read_runtime_status` wiring만으로 충족됩니다. 추가 `project=project` 전달은 convention-only diff라 이번 라운드에서는 scope를 늘리지 않았습니다.
- `tests/test_pipeline_gui_backend.py:718`(pre-edit)의 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")`를 제거했습니다. 남은 8개 skip decorator의 실제 post-edit line은 `:643`, `:792`, `:867`, `:945`, `:1016`, `:1065`, `:1200`, `:1262`입니다.
- `test_read_runtime_status_from_current_run_pointer`(seq 471 unskip)와 `test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`(seq 468 unskip)는 이번 wiring 이후에도 모두 green을 유지했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471 shipped surfaces는 의도적으로 더 수정하지 않았습니다. `storage/*`, `core/*`, `app/*`, `tests/test_web_app.py`, `tests/test_smoke.py`, `e2e/tests/*`, `docs/*.md`와 dirty worktree의 다른 파일도 이번 라운드에서 건드리지 않았습니다.

## 검증
- `rg -n 'normalize_runtime_status' pipeline_gui/backend.py`
  - 결과: 5건 hit
  - line: `71` definition, `291` `confirm_pipeline_start`, `569` `read_runtime_status` 내부 normalize call, `630` `runtime_state`, `637` `runtime_active`
  - handoff 예상 4건보다 1건 많아진 이유는 이번 slice에서 `read_runtime_status` 내부에 normalize call이 새로 추가됐기 때문입니다.
- `rg -n 'read_runtime_status' pipeline_gui/`
  - 결과: 6건 hit
  - `pipeline_gui/home_controller.py:12` import, `pipeline_gui/home_controller.py:177` normalize wrapper call, `pipeline_gui/backend.py:291` normalize wrapper call, `pipeline_gui/backend.py:551` definition, `pipeline_gui/backend.py:630` normalize wrapper call, `pipeline_gui/backend.py:637` normalize wrapper call
  - `pipeline_gui/` 내부의 실제 caller는 모두 `normalize_runtime_status(...)` wrapper를 거치므로 post-wiring도 idempotent입니다. fragile caller는 확인되지 않았습니다.
- `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
  - 결과: 8건 hit
  - line: `643`, `792`, `867`, `945`, `1016`, `1065`, `1200`, `1262`
- `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
  - 결과: 8건 hit
- `rg -n '"note": "stopped"' pipeline_gui/backend.py`
  - 결과: 1건 hit (`:109`)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.047s`, `OK (skipped=8)`
  - baseline `OK (skipped=9)` -> post-edit `OK (skipped=8)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped`
  - 결과: `Ran 1 test in 0.005s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer`
  - 결과: `Ran 1 test in 0.003s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 1 test in 0.004s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.021s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.078s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.074s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `TestRuntimeStatusRead`의 8개 cell은 여전히 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 상태입니다. future G5-unskip-* sub-family(RUNNING→BROKEN, RUNNING→DEGRADED, aged ambiguous, degraded_reason vocabulary, watcher-only-alive, recent_field_quiescent, stale_running_status_broken_when_supervisor_is_missing)는 계속 deferred입니다.
- `read_runtime_status`의 계약은 이제 "raw thin reader"가 아니라 "supervisor reality를 반영해 normalize하는 reader"입니다. raw JSON pass-through를 기대하던 caller가 있다면 이제 normalized output을 보게 됩니다. seq 471 `/work`가 `read_runtime_status`를 thin reader로 설명한 부분은 이제 stale이므로 로컬 mental model을 업데이트해야 합니다.
- lane의 `"note": "stopped"`는 새 supervisor-missing STOPPING branch에서만 설정됩니다. 기존 quiescent block에는 여전히 note rewrite가 없습니다. future test가 quiescent-but-not-supervisor-missing case에도 `"note": "stopped"`를 기대하면 별도 확장이 필요합니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 10개 `LocalOnlyHTTPServer` PermissionError cell도 그대로 열려 있습니다.
- 오늘(2026-04-20) docs-only round count는 0으로 유지됩니다.
- dirty worktree 파일들은 그대로 남아 있으며, 이번 라운드에서도 targeted file 외 다른 변경은 추가하지 않았습니다.
