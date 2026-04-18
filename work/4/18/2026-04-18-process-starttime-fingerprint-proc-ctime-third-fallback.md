# 2026-04-18 process_starttime_fingerprint `/proc/<pid>` ctime third fallback

## 변경 파일
- `pipeline_runtime/schema.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`

## 사용 skill
- 없음

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-fingerprint-helper-call-contracts.md`와 `verify/4/18/2026-04-18-fingerprint-helper-call-contracts-verification.md`는 shared helper의 non-positive short-circuit 계약과 `_ps_lstart_fingerprint` subprocess kwargs 계약을 회귀에 고정했습니다.
- 같은 family의 다음 current-risk는 `/proc/<pid>/stat` 파싱/읽기가 실패하고 `ps -p <pid> -o lstart=`도 사용 가능한 fingerprint를 내지 못하지만 `/proc/<pid>` 자체는 stat 가능한 좁은 호스트 상황입니다. 기존 두 source만 쓰면 그런 호스트에서는 fingerprint가 `""`로 내려앉아 supervisor restart가 fresh `_make_run_id()`로 falls through하고, watcher가 살아 있는데도 같은 라인의 `run_id` 상속이 깨집니다.
- 새 identity 파일이나 `current_run.json` 필드, watcher/supervisor matching rule을 건드리지 않고, shared helper 안에 세 번째 narrow fallback을 더하는 방식으로 inheritance 능력만 좁게 넓혔습니다.
- handoff (`STATUS: implement`, `CONTROL_SEQ: 324`)가 같은 shared owner-match 계약을 유지한 채 `os.stat(f"/proc/{pid}")` ctime fallback을 한 helper에 묶어 달라고 지정했습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`
  - `import os`를 추가하고 새 helper `_proc_ctime_fingerprint(pid)`를 정의했습니다. `os.stat(f"/proc/{pid}")`의 `st_ctime_ns`를 문자열로 직렬화하고, `OSError`가 나면 `""`로 safe-degrade합니다.
  - `process_starttime_fingerprint(pid)`의 fallback chain을 `proc/<pid>/stat` → `ps -p <pid> -o lstart=` → `os.stat(f"/proc/{pid}")` ctime 순으로 확장했습니다. non-positive pid short-circuit과, 세 source가 모두 비어 있을 때만 `""`를 돌리는 경계는 그대로 유지됩니다.
  - 같은 helper의 docstring을 새 fallback 순서와 "`/proc` 자체가 없는 호스트의 portability는 넓혀 주지 않는다"는 범위 경계까지 갱신했습니다.
- `tests/test_pipeline_runtime_schema.py`
  - 기존 `ProcessStarttimeFingerprintTest`의 short-circuit / primary success / ps fallback 회귀에 `_proc_ctime_fingerprint` mock을 함께 물려 새 helper가 뚫고 내려가지 않는 step을 동일 클래스 안에서 증명했습니다.
  - 기존 `test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail`를 `test_process_starttime_fingerprint_returns_empty_when_all_sources_fail`로 확장해 세 source가 모두 `""`일 때만 `""`가 나오는 계약을 회귀에 못 박았습니다.
  - 새 `test_process_starttime_fingerprint_falls_back_to_proc_ctime_when_proc_and_ps_both_fail`로 두 primary source가 모두 `""`일 때 `_proc_ctime_fingerprint`가 호출되고 그 반환값이 그대로 전파되는 경로를 고정했습니다.
  - 새 `test_proc_ctime_fingerprint_returns_stringified_ctime_ns_on_success` / `test_proc_ctime_fingerprint_returns_empty_when_stat_raises_oserror`로 새 helper 자체의 success 추출 + safe-degradation 계약을 좁게 회귀했습니다. success 경로는 `mock.patch.object(schema_module.os, "stat", ...)`로 `st_ctime_ns`만 돌려받고, 호출 경로가 `/proc/<pid>` 디렉터리(끝에 `/stat`가 붙지 않음)라는 점도 `stat_mock.assert_called_once_with("/proc/99999")`로 함께 못 박았습니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - 새 `test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_proc_ctime_fallback`를 추가했습니다. `_proc_starttime_fingerprint` / `_ps_lstart_fingerprint`를 `""`로, `_proc_ctime_fingerprint`를 stable 문자열로 묶은 상태에서 watcher exporter가 pointer를 쓰고 supervisor restart가 `run_id`를 상속하는 end-to-end 경로를 증명합니다.
  - 기존 `test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher`를 `_proc_ctime_fingerprint` mock까지 포함하도록 좁혀, "세 source가 모두 비면 inheritance 거부"라는 safe-degradation 계약을 그대로 지켰습니다.
  - 같이 `test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`의 stub 묶음에도 ctime fallback을 명시적으로 `""`로 붙여, Linux 호스트의 real `/proc/<pid>` ctime이 test 의도를 깨지 않도록 했습니다.
- `tests/test_watcher_core.py`
  - `test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`도 같은 이유로 `_proc_ctime_fingerprint` return_value `""`를 같이 물려 empty-path 회귀가 세 source 모두 비어야 성립한다는 계약과 일치하게 맞췄습니다.
- `.pipeline/README.md`
  - helper fallback 설명 한 줄을 세 단계(`/proc/<pid>/stat` → `ps -p <pid> -o lstart=` → `os.stat(f"/proc/{pid}")` ctime)와 scope limit(`/proc`가 마운트되지 않은 호스트는 여전히 safe-degrade)으로 넓혔습니다. 다른 운영 원칙 블록은 건드리지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest`
  - 결과: `Ran 15 tests`, `OK` (non-positive short-circuit + primary success + ps fallback + 새 ctime fallback + all-sources-fail + helper 단위 회귀 포함)
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_proc_ctime_fallback tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint`
  - 결과: `Ran 2 tests`, `OK` (shared helper 변경이 기존 watcher exporter 회귀를 깨지 않는지 같이 확인)
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- broader full-module rerun과 Playwright/smoke는 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 변경은 shared helper 안의 좁은 third fallback 추가 + 그 fallback을 mock-통과시키는 회귀뿐이고, 기존 supervisor/watcher matching rule이나 controller/browser contract는 손대지 않았습니다. handoff도 지정된 4개 test를 좁게 재실행하라고 명시했고 모두 통과했습니다.

## 남은 리스크
- 세 번째 fallback은 `/proc/<pid>` 디렉터리 자체의 `st_ctime_ns`에 의존합니다. 같은 pid 아래 디렉터리 ctime이 프로세스 재생성 없이 갱신되는 custom `/proc` implementation에서는 fingerprint가 바뀌어 inheritance가 불필요하게 깨질 수 있습니다. 현재 Linux `/proc` 구현에서는 pid 디렉터리 ctime이 process 생성 시점에 고정되므로 MVP 운영 환경에서는 문제 없습니다.
- `/proc` 자체가 마운트되지 않은 호스트(BusyBox minimal, 일부 container) portability는 이번 슬라이스가 넓혀 주지 않습니다. 그런 환경은 여전히 세 source 모두 `""`로 안전하게 degrade되고, supervisor는 fresh `_make_run_id()`로 fall through합니다. 더 portable한 identity는 watcher가 owner identity를 별도 파일로 기록하는 follow-up로 남습니다.
- 이번 closeout이 직접 편집한 파일은 `pipeline_runtime/schema.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `tests/test_watcher_core.py`, `.pipeline/README.md`입니다. `git status`에 보이는 다른 dirty 변경(runtime/controller/browser/docs plus 이전 `/work`·`/verify` notes)은 이번 라운드의 산출물이 아니므로, 다음 verify 라운드에서 이 파일 외 영역의 diff 책임을 이 closeout에 귀속하면 안 됩니다.
