# 2026-04-20 pipeline_gui G5 DEGRADED age machinery verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-g5-degraded-age-machinery-verification.md` (본 파일)

## 사용 skill
- `round-handoff`: seq 495 `.pipeline/claude_handoff.md`(G5-unskip-DEGRADED_WITH_AGE-MACHINERY, Gemini 494 advice) 구현 주장을 `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + `:1012` 직접 unskip 확인 + `:1062` aged regression counterpart + 7개 다른 prior unskip + `git diff`를 직접 재실행했습니다.

## 변경 이유
- seq 495 `.pipeline/claude_handoff.md`(Gemini 494 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-g5-degraded-age-machinery.md`가 제출되었습니다.
- 목표는 `parse_iso_utc` 기반 age discriminator를 `normalize_runtime_status`에 도입해 `:1012` recent DEGRADED 셀 1개만 unskip하고, seq 492가 일으킨 `:1062 aged_ambiguous` regression이 이번에는 재발하지 않는지 확인.

## 핵심 변경
- `pipeline_gui/backend.py:13` import 확장 확인: `from pipeline_runtime.schema import parse_iso_utc, read_jsonl_tail`. 같은 import group 유지.
- `pipeline_gui/backend.py:35` module constant `SNAPSHOT_STALE_THRESHOLD = 15.0` 추가 확인. `_VERIFY_ACTIVITY_LABELS` dict 뒤, 첫 함수 정의(`_read_log_lines`) 앞.
- `pipeline_gui/backend.py:92-95` `normalize_runtime_status` 안에서:
  - `:92` `supervisor_missing = project is not None and not supervisor_alive(project)[0]`
  - `:93` `updated_at_raw = str(status.get("updated_at") or "")`
  - `:94` `snapshot_ts = parse_iso_utc(updated_at_raw)`
  - `:95` `snapshot_age = (time.time() - snapshot_ts) if snapshot_ts > 0 else None`
  - `parse_iso_utc("")`가 `0.0`을 반환(공식 `pipeline_runtime/schema.py:224-231`), `try/except` wrapper 도입 없음.
- `pipeline_gui/backend.py:141-152` 새 narrow DEGRADED branch 확인:
  ```python
  if (
      supervisor_missing
      and runtime_state == "RUNNING"
      and not watcher.get("alive")
      and any(str(lane.get("state") or "") != "OFF" for lane in lanes)
      and snapshot_age is not None
      and snapshot_age <= SNAPSHOT_STALE_THRESHOLD
  ):
      status["runtime_state"] = "DEGRADED"
      status["degraded_reason"] = "supervisor_missing_recent_ambiguous"
      status["degraded_reasons"] = ["supervisor_missing_recent_ambiguous"]
      return status
  ```
  - seq 477 BROKEN branch 종료(`:140 return status`)와 seq 480 RUNNING→BROKEN branch guard(`:153 if supervisor_missing and runtime_state == "RUNNING":`) 사이 정확히 삽입.
  - body가 `runtime_state`, `degraded_reason`, `degraded_reasons` 3개만 rewrite — `lanes` / `control` / `active_round` / `watcher` 유지. `:1012` test가 `lanes[0].state == "READY"`만 assert하므로 lane 보존이 올바르게 작동.
  - `has_active_surface` helper 도입 없음, lane `pid=None/attachable=False` rewrite 없음 — advice 491 over-scope는 계속 거부.
- 다른 branch 비변경 확인: STOPPING `:96-118`, BROKEN `:119-140`, RUNNING→BROKEN `:153-175`, quiescent `:176+` 모두 seq 489 shape 그대로. `supervisor_alive` helper, `read_runtime_status` wiring, `_supervisor_pid`/`_pid_is_alive` helper 전부 미편집.
- `tests/test_pipeline_gui_backend.py:1012` 앞 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 한 줄 삭제 확인. `def test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous`가 이제 live. 남은 2개 decorator는 `:1194`, `:1256`에 존재.
- grep 검증:
  - `rg -n 'parse_iso_utc' pipeline_gui/backend.py` → 2 hits (`:13` import, `:94` 호출)
  - `rg -n 'SNAPSHOT_STALE_THRESHOLD' pipeline_gui/backend.py` → 2 hits (`:35` 정의, `:147` guard)
  - `rg -n 'supervisor_missing_recent_ambiguous' pipeline_gui/backend.py` → 2 hits (`:150`, `:151`)
  - `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py` → 2 hits (`:1194`, `:1256`)
  - `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py` → 2 hits
  - `rg -n 'if supervisor_missing and runtime_state' pipeline_gui/backend.py` → 3 hits (STOPPING `:96`, BROKEN `:119`, RUNNING→BROKEN `:153`). 새 DEGRADED branch는 multi-line `if (\n    supervisor_missing\n    ...\n):` form이라 이 one-line regex에 잡히지 않음 — 의도대로.
  - `rg -n 'snapshot_age' pipeline_gui/backend.py` → 3 hits (`:95` 계산, `:146` `is not None`, `:147` `<=` threshold)
  - `rg -n 'has_active_surface' pipeline_gui/backend.py` → 0 hits
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `495` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 496.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `493` — seq 494 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `494` — seq 495 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.060s`, `OK (skipped=2)`. baseline transition seq 493 revert 이후 `OK (skipped=3)` → seq 495 post-edit `OK (skipped=2)`. failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken`
  - 결과: `Ran 2 tests in 0.007s`, `OK`.
  - `:1012` recent DEGRADED unskip 즉시 green. `:1062` aged BROKEN counterpart도 계속 green — seq 492 regression은 age guard 덕분에 이번에는 재발하지 않았습니다.
- `/work` 노트가 별도 나열한 7개 다른 previously-unskipped cell 재실행은 `/work`에 기록된 `Ran 7 tests in 0.029s, OK` 결과를 신뢰하고 생략. 이번 slice가 건드린 guard가 그 셀들의 trigger 경로를 변경시키지 않는 것을 코드 대조로 확인 (stale/STOPPING/stopping/BROKEN payload/from_current_run_pointer/supervisor_alive branches 모두 새 DEGRADED branch 전이나 무관한 branch에서 fire).
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → `/work`의 `출력 없음, 통과` 신뢰.
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → `/work`의 `출력 없음, 통과` 신뢰.
- `tests.test_smoke -k progress_summary/coverage/claims/reinvestigation`는 `/work`가 각 `11/27/7/6 OK` 기록, 이번 slice가 `tests/test_smoke.py`/`core/`/`app/`/`storage/`를 건드리지 않아 baseline 유지 안전. verify 재실행 생략.
- `tests.test_web_app`, Playwright, `make e2e-test`는 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **2 DEGRADED cells 여전히 deferred**:
  - `:1194` `undated_ambiguous_snapshot_degraded` — fixture에 `updated_at` 없음 → `snapshot_age is None`라 이번 branch 제외. 다음 슬라이스는 `snapshot_age is None AND watcher.alive == True` (fixture가 `watcher.alive=True`) 같은 다른 distinguishing signal을 써야 함.
  - `:1256` `watcher_only_alive_without_pid_degraded_ambiguous` — fixture `watcher.alive=True AND watcher.pid in {None, ""}` → 이번 branch의 `not watcher.get("alive")` guard가 제외. 다음 슬라이스는 `watcher.alive==True AND watcher.pid is None` 방향.
- **normalize_runtime_status 분기 수 증가**: 이제 STOPPING + BROKEN + new DEGRADED + RUNNING→BROKEN + quiescent 5-branch. 남은 2개 DEGRADED variant가 추가되면 7-branch가 되며, G12 `_apply_shutdown_shape` refactor leverage가 다시 한 단계 올라갑니다. 다음 DEGRADED 슬라이스 전에 refactor를 먼저 하거나, 2개 DEGRADED variant를 landing한 뒤 refactor 하나로 묶는 선택지가 양쪽 다 defensible.
- **다음 슬라이스 ambiguity**:
  - A) `G5-unskip-DEGRADED_UNDATED` (`:1194`) — `snapshot_age is None` 중심 guard
  - B) `G5-unskip-DEGRADED_WATCHER_ONLY` (`:1256`) — `watcher.alive=True AND pid absent` guard
  - C) `G12 _apply_shutdown_shape` refactor 먼저
  - D) G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11 중 하나
  - 세 후보(A/B/C)가 모두 bounded single-file slice로 실행 가능하고 dominant current-risk reduction이 뚜렷하지 않아 `.pipeline/gemini_request.md`로 arbitration open하는 편이 `/verify` README 규칙과 일치.
- **seq 492 lesson 재확인**: narrow trigger 제안 전에는 `supervisor_missing + RUNNING` branch를 공유하는 모든 currently-green cell의 fixture shape 비교표를 먼저 만들어야 함. 이번 라운드의 age guard가 `:1062 aged`를 올바르게 제외한 것도 비교표 덕분.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 targeted 2 files만 추가 수정.
