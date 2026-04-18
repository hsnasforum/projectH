# 2026-04-18 supervisor current_run pointer empty-fingerprint writer parity 회귀 고정

## 변경 파일
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-process-starttime-fingerprint-empty-safe-degradation.md`와 `verify/4/18/2026-04-18-process-starttime-fingerprint-empty-safe-degradation-verification.md`는 helper 빈 fingerprint, watcher exporter empty pointer write, supervisor inheritance refusal 세 경계를 같은 family 안에서 회귀로 고정했습니다.
- 하지만 같은 ownership seam에는 writer가 두 명 있습니다. `WatcherCore._write_current_run_pointer()`와 `RuntimeSupervisor._write_current_run_pointer()`가 같은 `current_run.json`을 기록하고, supervisor 쪽 writer는 minimal-host의 두 source 모두 빈 fingerprint 경로를 아직 dedicated 회귀로 고정하지 않은 상태였습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 315`)가 정확히 이 writer parity 한 곳만 좁게 닫으라고 지목했습니다. 새 third fallback이나 inheritance 정책 재해석은 모두 scope에서 빠져 있어, 구현 변경 없이 supervisor writer 회귀 한 개만 추가하는 가장 작은 슬라이스로 닫았습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_supervisor.py`
  - `RuntimeSupervisorTest`에 `test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`을 추가했습니다.
  - 기존 positive 회귀 `test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint` 바로 뒤에 두어, supervisor 쪽 writer도 fingerprint가 살아있을 때(non-empty) / 두 source 모두 실패할 때(explicit `""`) 두 경계를 한 자리에서 짝으로 비춥니다.
  - `pipeline_runtime.schema._proc_starttime_fingerprint`와 `_ps_lstart_fingerprint`를 모두 `""`로 stub 한 뒤 `RuntimeSupervisor._write_current_run_pointer()`를 직접 호출합니다.
  - 단언:
    - `current_run["run_id"]`는 supervisor에 명시한 `"20260418T010203Z-p333"` 그대로 (writer가 빈 fingerprint라고 run_id를 떨어뜨리지 않는지)
    - `current_run["watcher_pid"]`는 live `os.getpid()` 그대로 (live watcher pid 추출 경로가 빈 fingerprint와 무관하게 살아있는지)
    - `"watcher_fingerprint" in current_run` 와 `current_run["watcher_fingerprint"] == ""` (필드가 빠지지 않고 explicit 빈 문자열로 직렬화되는지)
  - 이렇게 해야 watcher exporter가 minimal-host에서 쓴 `watcher_fingerprint: ""` pointer와 supervisor가 쓴 pointer가 같은 모양을 갖고, 후속 supervisor 재시작 inheritance 게이트가 두 writer의 safe-degradation pointer를 같은 경로로 일관되게 다룰 수 있습니다.
- `pipeline_runtime/supervisor.py`, `pipeline_runtime/schema.py`는 손대지 않았습니다. supervisor `_write_current_run_pointer()`는 이미 `watcher_fingerprint`를 dict literal에 항상 포함시켜 직렬화하므로, 이번 라운드는 그 실제 동작을 좁은 회귀로 못 박는 데 그쳤습니다.
- `.pipeline/README.md`도 손대지 않았습니다. fallback contract와 빈 fingerprint면 fresh `_make_run_id()`로 fall through 한다는 경계는 직전 라운드들에서 이미 한 줄로 적혀 있어, writer parity 고정만으로 README 표면을 다시 좁힐 필요가 없었습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`
  - 결과: `Ran 2 tests`, `OK` (supervisor writer non-empty + 새 empty 경계)
- `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- supervisor inheritance positive/negative pair full rerun은 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 새 회귀 한 개 추가에 한정됐고, inheritance 회귀들이 공유하는 stubbing setup(같은 두 helper를 `""`로 mock 하는 패턴)을 그대로 따라 썼을 뿐 기존 setup 자체를 바꾸지 않았기 때문입니다. 핸드오프의 conditional 검증("shared stubbing setup이 materially 바뀌었을 때만") 트리거가 되지 않았습니다.
- `tests.test_pipeline_runtime_supervisor` full module rerun, `tests.test_watcher_core` full module rerun, broader e2e/live tmux replay도 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 한 클래스 안에 회귀 한 개를 추가한 좁은 슬라이스이고, 런타임/exporter/supervisor writer 동작 자체는 직전 verified 라운드와 동일하기 때문입니다.

## 남은 리스크
- BusyBox 등 `ps -p <pid> -o lstart=` 자체를 지원하지 않는 minimal 환경에서는 두 writer 모두 여전히 `watcher_fingerprint: ""`로 safe degradation 합니다. 이번 회귀로 supervisor writer 쪽까지 그 경계가 직접 고정됐지만, 더 portable한 third fallback(예: Python ctypes syscall, watcher가 owner identity를 따로 기록)은 여전히 별도 follow-up로 남습니다.
- 이번 closeout이 직접 편집한 파일은 `tests/test_pipeline_runtime_supervisor.py` 한 개입니다. `git status`에 보이는 다른 dirty 변경(runtime/controller/browser/docs)은 이번 라운드의 산출물이 아니므로, 다음 verify 라운드에서 이 파일 외 영역의 diff 책임을 이 closeout에 귀속하면 안 됩니다.
- 같은 클래스의 기존 `test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint`는 여전히 host의 `/proc/<pid>/stat` 가용성을 가정합니다. 이번 라운드 scope는 새 empty-path 회귀 추가에 한정돼 있어 그 host portability는 건드리지 않았고, 다음 라운드가 같은 family를 더 좁힐 때 schema 회귀처럼 stub-rewiring으로 host-portable하게 정리하는 편이 안전합니다.
