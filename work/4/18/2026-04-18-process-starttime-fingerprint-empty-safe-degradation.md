# 2026-04-18 process_starttime_fingerprint empty safe-degradation 회귀 고정

## 변경 파일
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-process-starttime-fingerprint-test-host-portable.md`와 `verify/4/18/2026-04-18-process-starttime-fingerprint-test-host-portable-verification.md`는 schema 회귀의 host portability를 닫았지만, `/proc`과 `ps -p <pid> -o lstart=` 두 source가 모두 실패하는 minimal-host 경계가 helper unit test 수준에서만 고정돼 있었습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 314`)는 같은 family의 마지막 unpinned safe-degradation 경계를 고정하라고 좁게 지목했습니다. helper-level 빈 fingerprint, watcher exporter가 그 빈 fingerprint를 explicit 필드로 기록하는 경로, supervisor inheritance가 그 빈 fingerprint를 보고 inheritance를 거부하는 경로 세 가지를 한 family 안에서 같이 묶어야 minimal-host 경계가 truthful해집니다.
- 새 third fallback이나 BusyBox 보강은 이번 scope에서 제외돼 있어, 구현 변경 없이 회귀 두 개만 추가하는 가장 좁은 슬라이스로 닫았습니다.

## 핵심 변경
- `tests/test_watcher_core.py`
  - `TransitionTurnTest`에 `test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`을 추가했습니다.
  - `pipeline_runtime.schema._proc_starttime_fingerprint`와 `_ps_lstart_fingerprint`를 모두 `""`로 stub 한 뒤, `WatcherCore._write_current_run_pointer()`가 기록한 `current_run.json`이
    - `run_id`/`watcher_pid`는 살아 있는 값을 그대로 갖고
    - `watcher_fingerprint` 필드를 빠뜨리지 않고 explicit `""` 값으로 직렬화하는지
    한 회귀로 같이 단언합니다. 이렇게 해야 supervisor 쪽이 "fingerprint 필드 자체가 없는 legacy pointer"와 "fingerprint가 explicit 빈 문자열인 minimal-host pointer"를 같은 safe-degradation 경계로 일관되게 다룰 수 있습니다.
  - 기존 `test_write_current_run_pointer_records_watcher_pid_and_fingerprint`(non-empty fingerprint 경로)는 그대로 두어, 두 회귀가 같은 클래스 안에서 non-empty/empty 두 경계를 짝으로 비추도록 했습니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - `RuntimeSupervisorTest`에 `test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher`를 추가했습니다.
  - 기존 positive `test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback` 바로 뒤에 두어, fallback이 살아있을 때(inherit)와 fallback도 비어 있을 때(refuse) 두 분기가 한 자리에서 대비됩니다.
  - 새 회귀는 두 helper를 모두 `""`로 stub 한 상태에서 watcher가 pointer를 쓰고(이때 `watcher_fingerprint`는 `""`), supervisor는 같은 process를 live owner로 보지만 자기 fingerprint 계산도 `""`로 떨어져 inheritance를 거부하는지 확인합니다.
  - 단언:
    - `current_run["watcher_fingerprint"] == ""`로 minimal-host pointer 모양을 직접 고정
    - `supervisor.run_id != watcher_owned_run_id`로 inheritance 거부와 fresh `_make_run_id()` fall-through를 직접 고정
    - watcher run_id는 `PIPELINE_RUNTIME_RUN_ID` 환경 변수로 명시해 fresh 비교가 우연한 timestamp/pid 충돌로 흔들리지 않게 했습니다.
- `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `watcher_core.py`는 손대지 않았습니다. shared helper, exporter pointer 작성 경로, supervisor inheritance 게이트는 이미 빈 fingerprint를 safe하게 다루도록 되어 있어, 이번 라운드는 그 실제 동작을 회귀로 좁게 못 박는 데 그쳤습니다.
- `.pipeline/README.md`도 손대지 않았습니다. 직전 라운드가 추가한 fallback contract 문장이 빈 fingerprint면 fresh `_make_run_id()`로 fall through 한다는 경계를 이미 한 줄로 적어 둔 상태라, 이번 회귀 고정만으로 README 표면을 다시 좁힐 필요가 없었습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/schema.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail`
  - 결과: `Ran 1 test`, `OK` (helper-level both-empty 경계 재확인)
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`
  - 결과: `Ran 2 tests`, `OK` (watcher pointer non-empty + 새 empty 경계)
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher`
  - 결과: `Ran 2 tests`, `OK` (positive ps fallback inheritance + 새 empty refusal)
- `git diff --check -- watcher_core.py pipeline_runtime/schema.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_schema`, `tests.test_pipeline_runtime_supervisor`, `tests.test_watcher_core` full module rerun과 broader e2e/live tmux replay는 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 두 test 파일에 회귀 한 개씩만 추가한 좁은 슬라이스이고, 런타임/exporter/inheritance 동작 자체는 직전 verified 라운드와 동일했기 때문입니다.

## 남은 리스크
- BusyBox 등 `ps -p <pid> -o lstart=` 자체를 지원하지 않는 minimal 환경에서는 helper가 여전히 `""`로 safe degradation 합니다. 이번 회귀로 그 경계의 end-to-end 동작(빈 fingerprint pointer + inheritance 거부)이 고정됐지만, 더 portable한 third fallback(예: Python ctypes syscall, 또는 watcher가 owner identity를 따로 기록)은 여전히 별도 follow-up로 남습니다.
- 이번 closeout이 직접 편집한 파일은 `tests/test_watcher_core.py`와 `tests/test_pipeline_runtime_supervisor.py` 두 개입니다. `git status`에 보이는 다른 dirty 변경(runtime/controller/browser/docs)은 이번 라운드의 산출물이 아니므로, 다음 verify 라운드에서 이 두 파일 외 영역의 diff 책임을 이 closeout에 귀속하면 안 됩니다.
- `tests.test_pipeline_runtime_supervisor` full module과 `tests.test_watcher_core` full module rerun은 이번 라운드에서 생략했습니다. 다음 라운드에서 같은 family를 닫거나 broader contract를 건드릴 때 한 번 같이 돌리는 편이 안전합니다.
