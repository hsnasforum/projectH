# 2026-04-18 process_starttime_fingerprint 회귀 host-portable 정리

## 변경 파일
- `tests/test_pipeline_runtime_schema.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-process-starttime-fingerprint-proc-missing-fallback.md`와 `verify/4/18/2026-04-18-process-starttime-fingerprint-proc-missing-fallback-verification.md`가 닫은 fallback 구현은 truthful이지만, 같은 verify가 마지막에 지목한 next same-family current-risk가 명확했습니다.
- `tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available`는 `process_starttime_fingerprint(os.getpid())`를 실제로 호출해서 결과가 비어 있지 않다고 단언한 뒤 `_ps_lstart_fingerprint`가 호출되지 않는지 확인했습니다. 이 단언은 host에 readable `/proc/<pid>/stat`가 있다는 전제를 회귀 안에 박아 놓은 셈이라, 정작 보호하려는 `/proc`-missing 환경에서는 fallback path를 검증하기 전에 test 자체가 흔들립니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 313`)는 helper 분기를 더 늘리지 말고 test rewiring으로 "prefer `/proc` when available" 계약만 host-portable하게 다시 잡으라고 좁게 지목했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_schema.py`
  - `ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available`를 다시 썼습니다.
    - `schema_module._proc_starttime_fingerprint`를 `"proc-source-fingerprint"`라는 stable string으로 stub 했습니다.
    - 같은 컨텍스트에서 `schema_module._ps_lstart_fingerprint`도 mock으로 묶어 두었습니다.
    - public `process_starttime_fingerprint(12345)`를 호출한 결과가 그대로 `"proc-source-fingerprint"`인지, primary helper가 그 pid로 정확히 한 번 호출됐는지, fallback helper는 한 번도 호출되지 않았는지를 한 번에 단언합니다.
  - 이 변경으로 회귀가 더 이상 실제 `/proc/<pid>/stat`이나 `os.getpid()` 결과에 의존하지 않으므로, `/proc`을 노출하지 않는 non-Linux POSIX / restricted container 호스트에서도 같은 contract("primary가 비어 있지 않으면 fallback을 호출하지 않는다")가 직접 검증됩니다.
  - 같은 클래스의 다른 6개 회귀(non-positive pid 단락, fallback 호출 경로, primary+fallback 모두 빈 문자열, `_ps_lstart_fingerprint` stdout strip / returncode 실패 / `FileNotFoundError`)는 이미 `/proc` 비의존이라 그대로 두었습니다.
- `pipeline_runtime/schema.py`는 손대지 않았습니다. shared helper의 fallback 분기는 직전 라운드에서 이미 truthful하게 닫혔고, 이번 라운드는 testability 경계만 좁혔습니다.
- `tests/test_pipeline_runtime_supervisor.py`도 손대지 않았습니다. supervisor inheritance end-to-end 회귀(`test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback`)는 이미 두 helper를 모두 stub하므로 host에 무관하게 fallback path를 직접 검증합니다.
- `.pipeline/README.md`도 손대지 않았습니다. 직전 라운드가 추가한 fallback 계약 문장이 현재 구현과 맞고, testability 경계는 docs 표면을 다시 좁힐 만한 변화가 아닙니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest`
  - 결과: `Ran 7 tests`, `OK` (재작성한 `test_process_starttime_fingerprint_uses_proc_when_available` 포함)
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 24 tests`, `OK` (focused 클래스 shape이 바뀌었으므로 핸드오프가 요구한 module-level rerun까지 같이 돌렸습니다)
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- 핸드오프 범위를 벗어나는 watcher/supervisor full module rerun, broader e2e, live tmux replay는 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 schema regression 한 클래스 안에서 한 메서드 본문을 host-portable하게 stub-rewiring한 것뿐이고, 런타임 contract와 supervisor inheritance 경계는 모두 그대로이기 때문입니다.

## 남은 리스크
- `ps -p <pid> -o lstart=` 옵션 자체를 지원하지 않는 BusyBox 같은 minimal 환경에서는 helper가 여전히 `""`로 safe degradation 하고, supervisor는 fresh `_make_run_id()`로 fall through 합니다. 이번 라운드는 그 경계를 회귀로만 확인했고, 더 portable한 third fallback(예: Python ctypes syscall, 또는 watcher가 `current_run.json`에 owner identity를 직접 기록)은 별도 follow-up로 남습니다.
- 이번 closeout이 직접 편집한 파일은 `tests/test_pipeline_runtime_schema.py` 한 개입니다. 현재 worktree에는 runtime/controller/browser/docs 쪽으로 `git status`가 이미 dirty인 다른 변경이 다수 보이지만, 이 라운드의 산출물에는 포함되지 않습니다.
- `tests.test_pipeline_runtime_supervisor` full module rerun과 `tests.test_watcher_core` 같은 broader 회귀는 이번 라운드에서 돌리지 않았으므로, 다음 라운드에서 같은 family를 한 단계 더 닫을 때 한 번 같이 돌리는 편이 안전합니다.
