# 2026-04-18 state-dir 공용 파일 owner boundary 정리

## 변경 파일
- `pipeline_runtime/schema.py`
- `watcher_core.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`

## 사용 skill
- `superpowers:systematic-debugging`: incident family(무엇이 stale state mixing/verify close break/lease release delay/artifact reselection/active lane drift/startup recovery 중 핵심 owner인지)를 먼저 정리하고 root cause 전에 patch를 쌓지 않도록 쓰기 위해 사용했습니다.
- `work-log-closeout`: `/work` closeout 형식과 실제 사실 항목을 current repo 규칙에 맞춰 정리하기 위해 사용했습니다.

## 변경 이유
- `.pipeline/state/` 디렉터리에는 watcher가 쓰는 job state JSON 이외에 watcher/supervisor가 공유하는 `turn_state.json`과 `autonomy_state.json`이 같이 있습니다. 이 두 파일은 JobState schema를 갖지 않습니다.
- 지금까지 state-dir을 스캔하는 코드가 여러 곳에 복제되어 있었고, 그 필터가 서로 달랐습니다. `watcher_core.py`는 `_SHARED_STATE_SPECIAL_FILES = {"turn_state.json", "autonomy_state.json"}`로 두 파일을 모두 제외했지만, `pipeline_runtime/schema.py::load_job_states`는 `turn_state.json`만 걸렀습니다.
- 그 결과 supervisor `_build_active_round`, `_dispatch_stall_marker`, `_completion_stall_marker`가 `autonomy_state.json`까지 job state처럼 iterate했고, current run에 실제 job state가 아직 없는 순간 `job_id=""`/`round=0`/`state="IDLE"`인 bogus active_round가 만들어져 lane/turn/round surface에서 current truth를 흐릴 수 있었습니다.
- 이 drift는 watcher/supervisor가 같은 `.pipeline/state/` 디렉터리를 각자의 local 규칙으로 해석하는 owner boundary 문제였고, 증상만 가리기보다 state-dir scan의 single source를 잡는 편이 맞았습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`에 `STATE_DIR_SHARED_FILES: frozenset[str] = frozenset({"turn_state.json", "autonomy_state.json"})` 상수를 canonical로 추가하고 그 의도(“JobState가 아닌 공용 상태 파일이므로 job iteration에 섞이면 안 된다”)를 주석으로 적었습니다.
- `load_job_states(...)`가 기존 하드코드 `"turn_state.json"` 한 파일 비교 대신 이 `STATE_DIR_SHARED_FILES` 집합을 통과 조건으로 쓰도록 바꿨습니다. 이제 autonomy pseudo-entry는 supervisor 쪽 scan에서도 빠집니다.
- `watcher_core.py`는 local `_SHARED_STATE_SPECIAL_FILES` 상수를 제거하고 `from pipeline_runtime.schema import STATE_DIR_SHARED_FILES`를 import한 뒤, state-dir scan 세 경로(`_archive_stale_job_states`, `_verified_work_paths`, `_get_current_run_jobs`)에서 공용 상수를 사용하도록 정리했습니다. 이 중 `_verified_work_paths`에는 기존에 `turn_state.json` 단일 비교만 남아 있었는데, 이것도 같은 집합으로 수렴해 current `VERIFY_DONE` 판정에 autonomy pseudo-entry가 섞이지 못하게 했습니다.
- `tests/test_pipeline_runtime_schema.py`에 `LoadJobStatesSharedFilesTest`를 추가해 (1) `STATE_DIR_SHARED_FILES`가 `turn_state.json`과 `autonomy_state.json`을 모두 포함하는지, (2) 같은 state_dir에 autonomy/turn/실제 job state가 섞여 있을 때 `load_job_states`가 실제 job 하나만 반환하는지, (3) 실제 job이 없고 공용 파일만 있을 때 `load_job_states`가 빈 리스트를 반환하는지를 고정했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 `test_build_active_round_skips_autonomy_state_pseudo_job`를 추가해, current run에 실제 job state가 없고 `autonomy_state.json`만 있을 때 supervisor `_build_active_round`가 bogus job_id=""/round=0 active_round를 만들지 않고 `None`을 반환하는지 직접 확인하도록 했습니다.
- `.pipeline/README.md`에 state-dir scan의 소유권이 `pipeline_runtime/schema.py`의 `STATE_DIR_SHARED_FILES`와 `load_job_states(...)` helper에 있고, watcher_core와 state archive flow도 같은 집합을 써야 한다는 규약을 추가해 현재 구현과 운영 규칙을 맞췄습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py watcher_core.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest tests.test_pipeline_runtime_schema -v`
  - 결과: `Ran 6 tests`, `OK` (새로 추가한 3개 포함 전체 통과)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_skips_autonomy_state_pseudo_job -v`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.ClaudeHandoffDispatchTest tests.test_watcher_core.VerifyCompletionContractTest`
  - 결과: `Ran 17 tests`, `OK` (2026-04-18 이전 라운드의 현재 run verify 우선 regression들을 그대로 보존 확인)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` 전체도 한 번 돌렸는데, baseline(main) 상태에서도 동일하게 실패하던 6개 failure + 1개 error(`test_manifest_mismatch_blocks_receipt_and_marks_degraded` 외 degraded/stop runtime 계열)가 그대로 재현됐습니다. 이번 라운드 변경과 무관한 기존 failure이므로 수정 범위에서 제외했습니다.
- `git diff --check -- pipeline_runtime/schema.py watcher_core.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과

## 남은 리스크
- 이번 라운드는 "autonomy/turn state 파일이 job iteration에 섞이지 않도록 owner boundary를 잡는" 수정입니다. `.pipeline/state/` 아래에 앞으로 새 공용 파일(예: 다른 shared autonomy/turn mini-state)이 들어오면 `STATE_DIR_SHARED_FILES`도 같이 갱신해야 하고, 그 규율은 이 파일 주석과 `.pipeline/README.md` 규약에만 남아 있습니다.
- 실제 tmux live runtime에서 autonomy pseudo-entry로 인한 active_round drift가 체감됐는지 별도 세션 replay까지는 이번 라운드에 포함하지 못했습니다. launcher live stability gate를 돌릴 기회가 생기면 active_round 중 `job_id=""`가 0회인지 한 번 더 확인하는 편이 맞습니다.
- `tests/test_pipeline_runtime_supervisor`의 pre-existing 6 failure + 1 error는 이번 수정과 별개이며, 다음 라운드에서 runtime DEGRADED/STOPPING 계약을 직접 건드릴 때 함께 조사할 대상으로 남겨 둡니다.
