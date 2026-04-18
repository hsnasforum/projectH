# 2026-04-18 current_run pointer 양쪽 writer positive 회귀 host-portable 정리

## 변경 파일
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-supervisor-current-run-pointer-empty-fingerprint-parity.md`와 `verify/4/18/2026-04-18-supervisor-current-run-pointer-empty-fingerprint-parity-verification.md`는 `RuntimeSupervisor._write_current_run_pointer()`의 빈 fingerprint 직렬화를 회귀로 고정해 두 writer의 minimal-host 안전 경로를 정렬했습니다.
- 같은 ownership seam에 남은 환경 의존은 두 writer의 positive 회귀 두 개였습니다. 둘 다 실제 호스트의 `/proc/<pid>/stat`이 살아 있어야만 non-empty fingerprint 단언이 통과하는 형태로 남아 있어, `/proc`을 노출하지 않는 minimal 환경에서는 fallback path를 검증하기 전에 positive 회귀 자체가 흔들릴 수 있습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 316`)는 새 third fallback이나 runtime 행동 변경 없이, 이미 존재하는 stub seam(`pipeline_runtime.schema._proc_starttime_fingerprint` / `_ps_lstart_fingerprint`)을 그대로 써서 두 positive 회귀를 host-portable하게 다시 잡으라고 좁게 지목했습니다.

## 핵심 변경
- `tests/test_watcher_core.py`
  - `TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint`를 다시 썼습니다.
    - `pipeline_runtime.schema._proc_starttime_fingerprint`를 `""`로, `_ps_lstart_fingerprint`를 stable string `"Mon Apr 18 12:34:56 2026"`로 stub 한 뒤 `WatcherCore._write_current_run_pointer()`를 호출합니다.
    - 단언:
      - `data["run_id"] == core.run_id`
      - `data["watcher_pid"] == os.getpid()` (live pid 추출 경로는 helper와 무관하게 살아 있는지)
      - `data.get("watcher_fingerprint", "") == "Mon Apr 18 12:34:56 2026"` (직렬화된 값이 stub fallback 그대로인지)
  - 같은 클래스의 `test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`은 그대로 두어, non-empty / empty 두 경계가 동일한 stub seam 위에서 짝으로 비추도록 했습니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - `RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint`를 다시 썼습니다.
    - 같은 두 helper를 같은 패턴으로 stub 한 뒤 `RuntimeSupervisor._write_current_run_pointer()`를 호출합니다.
    - 단언:
      - `current_run["watcher_pid"] == os.getpid()` (live experimental.pid 경로 유지)
      - `current_run["watcher_fingerprint"] == "Mon Apr 18 12:34:56 2026"` (direct writer가 같은 fallback 값을 그대로 직렬화하는지)
    - 기존 `_read_proc_starttime_fingerprint(os.getpid())` 비교 단언은 더 이상 사용하지 않습니다. `_read_proc_starttime_fingerprint` helper 자체는 같은 파일의 inheritance 회귀들이 여전히 사용하므로 그대로 두었습니다.
  - 같은 클래스의 `test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`은 그대로 두어, supervisor 쪽도 non-empty / empty 두 writer 경계가 한 자리에서 짝으로 비춥니다.
- `pipeline_runtime/schema.py`, `watcher_core.py`, `pipeline_runtime/supervisor.py`는 손대지 않았습니다. 두 writer가 helper로부터 받은 fingerprint를 그대로 직렬화하는 경로는 이미 contract와 맞고, 이번 라운드는 그 동작을 호스트 가정 없이 검증할 수 있도록 회귀의 stub seam만 좁혔습니다.
- `.pipeline/README.md`도 손대지 않았습니다. fallback 계약과 빈 fingerprint면 fresh `_make_run_id()`로 fall through 한다는 경계는 직전 라운드들에서 이미 한 줄로 적혀 있어, writer 회귀 host-portable 정리만으로 README 표면을 다시 좁힐 필요가 없었습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`
  - 결과: `Ran 4 tests`, `OK` (두 writer × non-empty/empty 4경계 모두 통과)
- `git diff --check -- watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- supervisor inheritance positive/negative pair 재실행은 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 두 writer 회귀의 단언 형태만 stub seam 위로 옮긴 것이고, inheritance 회귀들이 공유하는 stubbing setup 자체를 바꾸지 않았기 때문입니다. 핸드오프의 conditional 트리거("shared stubbing setup이 materially 바뀌었을 때만") 조건이 발동되지 않았습니다.
- `tests.test_pipeline_runtime_supervisor`, `tests.test_watcher_core` full module rerun과 broader e2e/live tmux replay도 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 두 회귀 메서드 본문만 stub-rewiring 한 좁은 슬라이스이고, 런타임/exporter/supervisor writer 동작 자체는 직전 verified 라운드들과 동일하기 때문입니다.

## 남은 리스크
- 두 writer 회귀가 모두 같은 stub seam 위에 올라왔으므로, `pipeline_runtime.schema` 안의 두 helper 이름이 바뀌면 두 회귀가 함께 흔들립니다. 다만 이 두 helper는 이번 family 내내 owner-match 정의를 한 곳에 모으는 역할이므로 이름 변경 자체가 같은 family의 다른 회귀와 같이 옮겨가야 할 변화에 가깝습니다.
- BusyBox 등 `ps -p <pid> -o lstart=` 자체를 지원하지 않는 minimal 환경에서는 두 writer가 여전히 `watcher_fingerprint: ""`로 safe degradation 합니다. 더 portable한 third fallback(예: Python ctypes syscall, watcher가 owner identity를 따로 기록)은 여전히 별도 follow-up로 남습니다.
- 이번 closeout이 직접 편집한 파일은 `tests/test_watcher_core.py`와 `tests/test_pipeline_runtime_supervisor.py` 두 개입니다. `git status`에 보이는 다른 dirty 변경(runtime/controller/browser/docs)은 이번 라운드의 산출물이 아니므로, 다음 verify 라운드에서 이 두 파일 외 영역의 diff 책임을 이 closeout에 귀속하면 안 됩니다.
