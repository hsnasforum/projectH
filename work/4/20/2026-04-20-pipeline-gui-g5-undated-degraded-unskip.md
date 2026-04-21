# 2026-04-20 pipeline gui G5 undated degraded unskip

## 변경 파일
- `pipeline_gui/backend.py`
- `tests/test_pipeline_gui_backend.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 검증, doc-sync 필요 여부, `/work` closeout readiness만 묶어 구현 라운드를 마감했습니다.

## 변경 이유
- seq 498까지 `:1012` recent_active_lane와 `:1256` watcher_only_alive_without_pid는 같은 DEGRADED branch에서 green이었지만, `tests/test_pipeline_gui_backend.py:1194` undated fixture만 `updated_at` 부재 때문에 `snapshot_age is None` 경로에서 RUNNING→BROKEN으로 떨어져 마지막 `@unittest.skip`로 남아 있었습니다.
- 이번 슬라이스는 새 branch를 추가하지 않고 기존 DEGRADED branch를 넓혀, undated ambiguous snapshot도 같은 5-branch dispatch 안에서 처리하면서 `degraded_reason`만 조건부로 갈라 마지막 skipped cell을 닫는 것이 목적이었습니다.

## 핵심 변경
- `pipeline_gui/backend.py:141-158`의 기존 DEGRADED guard에서 age conjunct를 `(snapshot_age is None or snapshot_age <= SNAPSHOT_STALE_THRESHOLD)`로 교체했습니다. 같은 branch가 recent ambiguous payload뿐 아니라 undated payload도 받도록 broaden했고, inner OR-disjunct shape는 그대로 유지했습니다.
- `pipeline_gui/backend.py:159-167` body를 local `reason` ternary로 바꿨습니다. `snapshot_age is None`이면 `"supervisor_missing_snapshot_undated"`, 아니면 `"supervisor_missing_recent_ambiguous"`를 써서 `:1194`는 새 undated literal로, `:1012`와 `:1256`은 기존 recent-ambiguous literal로 남도록 했습니다.
- NO new branch was added. `normalize_runtime_status` dispatch count는 계속 5-branch(STOPPING + BROKEN + broadened DEGRADED + RUNNING→BROKEN + quiescent)입니다.
- `tests/test_pipeline_gui_backend.py:1194`에서 pre-edit `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 한 줄만 제거했습니다. post-edit 기준 `:1194`는 바로 `def test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded(self) -> None:`이며, file 전체에 `@unittest.skip`가 남아 있지 않습니다.
- doc-sync triage 결과 없음: 이번 변경은 `pipeline_gui` 내부 runtime normalization과 해당 unit test만 건드렸고, 현재 root docs/README/agent-rule surfaces가 이 내부 DEGRADED reason literal이나 skip decorator 존재를 계약으로 서술하지 않아 같은 라운드 docs 갱신 대상은 없었습니다.

## 검증
- grep 확인
  - `rg -n 'supervisor_missing_recent_ambiguous' pipeline_gui/backend.py`
    - 결과: 1건 (`:162`)
  - `rg -n 'supervisor_missing_snapshot_undated' pipeline_gui/backend.py`
    - 결과: 1건 (`:160`)
  - `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py`
    - 결과: 0건
  - `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py`
    - 결과: 0건
  - `rg -n 'if supervisor_missing and runtime_state' pipeline_gui/backend.py`
    - 결과: 3건 (`:96`, `:119`, `:168`)
  - `rg -n 'watcher.get\("pid"\)' pipeline_gui/backend.py`
    - 결과: 2건 (`:155`, `:195`)
  - `rg -n 'snapshot_age is None' pipeline_gui/backend.py`
    - 결과: 2건 (`:145`, `:161`)
  - `rg -n 'snapshot_age' pipeline_gui/backend.py`
    - 결과: 4건 (`:95`, `:145`, `:146`, `:161`)
  - `rg -n 'SNAPSHOT_STALE_THRESHOLD' pipeline_gui/backend.py`
    - 결과: 2건 (`:35`, `:146`)
  - `rg -n 'has_active_surface' pipeline_gui/backend.py`
    - 결과: 0건
  - `rg -n 'def _degraded_reason' pipeline_gui/backend.py`
    - 결과: 0건
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.159s`, `OK`
  - baseline transition: `OK (skipped=1) -> OK (skipped=0)`
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded`
  - 결과: `Ran 1 test in 0.011s`, `OK`
  - `:1194`는 이제 DEGRADED로 읽히고 `degraded_reason=="supervisor_missing_snapshot_undated"`를 만족합니다. `control.active_control_status=="implement"`와 `watcher.alive==True`도 그대로 보존됩니다.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor`
  - 결과: `Ran 4 tests in 0.034s`, `OK`
  - `:1256` seq 498은 second disjunct match + `snapshot_age` not None 상태로 계속 DEGRADED이며, recent-ambiguous literal `"supervisor_missing_recent_ambiguous"`를 그대로 유지했습니다.
  - `:1012` seq 495는 first disjunct로 계속 DEGRADED이며, recent-ambiguous literal을 유지했습니다.
  - `:1062` aged fixture는 `snapshot_age is None = False`, `20 <= 15 = False`라 broadened age disjunct 전체가 False여서 계속 BROKEN입니다.
  - `:865` seq 483 counterpart는 `watcher.alive=True AND pid=4242`라 `not watcher.pid`가 계속 False여서 새 path에 들어가지 않고 BROKEN으로 유지됐습니다.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_normalize_runtime_status_drops_non_mapping_payload tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_normalize_runtime_status_converts_inactive_degraded_snapshot_to_stopped`
  - 결과: `Ran 8 tests in 0.029s`, `OK`
  - 6개의 다른 previously-unskipped cell과 direct-normalize 2개 테스트가 모두 green으로 유지됐습니다.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusNormalize`
  - 결과: 현재 test module에는 해당 class가 없어 `AttributeError`로 실패했습니다.
  - 대응: 동등 범위의 direct-normalize 테스트가 `tests/test_pipeline_gui_backend.py:1307-1355`에서 `TestRuntimeStatusRead` 메서드로 정의되어 있어, 위 8-test rerun에 그 2개를 포함해 재검증했습니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.028s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.098s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.099s`, `OK`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498 shipped surfaces는 의도적으로 더 수정하지 않았습니다.

## 남은 리스크
- All `TestRuntimeStatusRead` DEGRADED-family cells are now green; `tests/test_pipeline_gui_backend.py`에 `@unittest.skip`가 남아 있지 않습니다. `G5-unskip-DEGRADED` family는 이번 라운드로 닫혔습니다.
- `normalize_runtime_status`는 계속 5-branch(STOPPING + BROKEN + broadened DEGRADED + RUNNING→BROKEN + quiescent)입니다. 다만 DEGRADED body 안에 두 literal을 고르는 reason-switch가 들어가서 `G12 _apply_shutdown_shape` refactor leverage는 더 커졌고, verify/handoff owner가 다음 후보로 보기 자연스러운 상태입니다.
- future DEGRADED slices는 dated fixture와 undated fixture를 모두 포함한 현재 green cell 전체와 먼저 비교해야 합니다. seq 492에서 이미 그 교훈이 있었고, 이번 broadened guard도 그 전제 위에서만 안전합니다.
- G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11은 계속 deferred입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 구현 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree의 다른 파일은 건드리지 않았고, 이번 라운드의 추가 수정은 두 target file의 지정 위치에만 한정했습니다.
