# 2026-04-18 process_starttime_fingerprint `/proc/<pid>` ctime third fallback verification

## 변경 파일
- `verify/4/18/2026-04-18-process-starttime-fingerprint-proc-ctime-third-fallback-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-process-starttime-fingerprint-proc-ctime-third-fallback.md`가 `process_starttime_fingerprint()`에 `/proc/<pid>` directory ctime 기반 third fallback을 추가하고, 그 경계를 schema/supervisor/watcher 회귀로 좁게 고정했다고 주장하므로 현재 코드와 재실행 결과가 실제로 맞는지 다시 확인해야 했습니다.
- 같은 날 기존 `/verify`였던 `verify/4/18/2026-04-18-fingerprint-helper-call-contracts-verification.md`는 next same-family move를 third fallback 계열로만 좁혀 둔 상태였으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 트리와 일치했습니다.
  - `pipeline_runtime/schema.py`는 `process_starttime_fingerprint(pid)`의 fallback order를 `/proc/<pid>/stat` → `ps -p <pid> -o lstart=` → `os.stat(f"/proc/{pid}")` ctime 순으로 확장했고, 새 helper `_proc_ctime_fingerprint(pid)`는 `st_ctime_ns`를 문자열로 직렬화하며 `OSError`에서는 `""`로 safe-degrade 합니다.
  - docstring도 같은 순서와 "`/proc` 자체가 없는 호스트의 portability는 넓히지 않는다"는 범위 경계를 현재 구현 truth에 맞게 갱신돼 있습니다.
  - `tests/test_pipeline_runtime_schema.py`의 `ProcessStarttimeFingerprintTest`에는 새 ctime fallback success/all-sources-fail/helper-unit regressions가 실제로 들어가 있고, 기존 short-circuit / proc success / ps fallback 경계도 third fallback을 의식한 call contract로 같이 좁혀졌습니다.
  - `tests/test_pipeline_runtime_supervisor.py`에는 `test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_proc_ctime_fallback`가 추가돼 watcher exporter와 supervisor inheritance가 같은 shared helper 결과를 end-to-end로 공유하는지 직접 고정합니다.
  - `tests/test_watcher_core.py`의 empty-fingerprint pointer writer regression도 `_proc_ctime_fingerprint`까지 `""`로 묶어, 세 source가 모두 실패할 때만 empty pointer가 나오는 현재 계약과 맞게 정리돼 있습니다.
  - `.pipeline/README.md`도 helper fallback 설명이 세 단계 순서와 scope limit까지 반영하도록 실제로 갱신돼 있습니다.
- 이번 verify 라운드에서 다시 실행한 최소 검증은 모두 통과했습니다.
  - `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`는 통과했습니다.
  - `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest`는 `Ran 15 tests`, `OK`였습니다.
  - supervisor focused inheritance 3개는 `Ran 3 tests`, `OK`였습니다.
  - watcher pointer writer focused 2개는 `Ran 2 tests`, `OK`였습니다.
  - `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md`도 통과했습니다.
- latest `/work`의 verification prose도 현재 truth와 대체로 맞았습니다.
  - 다만 `git diff --check`와 `py_compile`는 latest `/work`보다 한 파일 더 넓게(`tests/test_watcher_core.py`) 재실행했습니다. latest `/work`가 실제로 그 파일도 바꿨기 때문에, verify에서는 changed file 전체를 포함하는 편이 더 정직했습니다.
  - 이 broadened rerun에서도 mismatch는 발견되지 않았습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator tooling family로 두고 있어, 이번 변경은 shipped browser contract를 넓히지 않는 same-family current-risk reduction으로 남아 있습니다.
- 다만 다음 same-family 기본값은 이번 라운드에서 바로 Claude implement로 고정하지 않았습니다.
  - 이제 current helper family는 `/proc/<pid>/stat`, `ps -p <pid> -o lstart=`, `/proc/<pid>` ctime까지 모두 regression으로 고정됐습니다.
  - 남은 portability gap은 `/proc` 자체가 없는 호스트인데, 이 지점은 더 이상 helper source 하나를 더 붙이는 문제라기보다 watcher-owned identity를 별도 file/contract로 둘지, 현재 safe-degradation을 유지하고 다른 family로 pivot할지의 설계 선택에 가깝습니다.
  - 따라서 seq 325는 weak implement handoff를 억지로 쓰기보다, post-ctime 다음 exact slice를 다시 좁히는 Gemini arbitration으로 넘기는 편이 더 정직합니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest`
  - 결과: `Ran 15 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_proc_ctime_fallback tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint`
  - 결과: `Ran 2 tests`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과
- broader full-module rerun, browser/e2e, live tmux replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 shared helper third fallback + 그 경계를 고정하는 focused regression과 runtime note sync에 한정됐고, controller/browser contract나 broader runtime control family는 직접 건드리지 않았기 때문입니다.

## 남은 리스크
- `/proc` 자체가 마운트되지 않은 호스트에서는 세 source가 여전히 모두 비어 `process_starttime_fingerprint()`가 `""`로 safe-degrade 하므로, supervisor restart inheritance는 그 환경에서 fresh `_make_run_id()`로만 떨어집니다.
- 그 다음 개선은 watcher-owned identity를 별도 file/contract로 둘지, 아니면 이 family를 여기서 닫고 다른 risk family로 넘어갈지의 우선순위 판단이 남아 있어, 이번 라운드에서는 exact slice를 자동 확정하지 않고 `.pipeline/gemini_request.md`를 다시 열었습니다.
- 현재 worktree에는 runtime/controller/browser/docs와 과거 `/work`/`/verify` 쪽 unrelated dirty changes가 계속 남아 있습니다. 다음 round는 이 verify가 다룬 fingerprint portability family 판단만 이어가고 unrelated diff는 건드리지 않는 편이 맞습니다.
