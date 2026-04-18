# 2026-04-18 _ps_lstart_fingerprint timeout safe-degradation 회귀 고정

## 변경 파일
- `tests/test_pipeline_runtime_schema.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-current-run-pointer-positive-writer-host-portable.md`와 `verify/4/18/2026-04-18-current-run-pointer-positive-writer-host-portable-verification.md`는 두 current_run pointer writer의 positive/empty 회귀를 host-portable하게 정렬했습니다.
- shared fingerprint helper의 fallback 경로(`_ps_lstart_fingerprint`)는 이미 `timeout=2.0`을 넘기고 `subprocess.SubprocessError`를 잡지만, 그 contract 안의 `subprocess.TimeoutExpired` 분기 자체는 dedicated 회귀로 못 박혀 있지 않았습니다. 회귀 표면에는 `returncode != 0`, `FileNotFoundError`, `OSError` 케이스만 이미 잡혀 있었습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 317`)는 새 third fallback이나 runtime 행동 변경 없이, helper boundary에서 timeout safe-degradation 한 경계만 좁게 회귀로 추가하라고 지목했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_schema.py`
  - 모듈 상단 import에 `subprocess`를 추가했습니다 (`subprocess.TimeoutExpired`를 직접 raise side_effect로 쓰기 위함).
  - `ProcessStarttimeFingerprintTest`에 `test_ps_lstart_fingerprint_returns_empty_when_ps_times_out`을 추가했습니다.
    - `subprocess.TimeoutExpired(cmd=["ps"], timeout=2.0)`을 `schema_module.subprocess.run`의 `side_effect`로 stub 합니다.
    - `schema_module._ps_lstart_fingerprint(99999)`가 예외를 캐치해 `""`를 그대로 돌리는지 단언합니다.
    - 기존 `_ps_lstart_fingerprint_returns_empty_when_ps_fails`(returncode != 0)와 `_ps_lstart_fingerprint_returns_empty_when_ps_binary_missing`(FileNotFoundError) 회귀 바로 뒤에 두어 같은 safe-degradation family가 한 자리에서 returncode/missing/timeout 세 분기를 짝으로 비추도록 했습니다.
- `pipeline_runtime/schema.py`는 손대지 않았습니다. 기존 `_ps_lstart_fingerprint`가 이미 `(OSError, subprocess.SubprocessError)`를 catch 하고 `subprocess.TimeoutExpired`는 `subprocess.SubprocessError`의 서브클래스이므로 새 회귀는 현재 helper 동작을 그대로 검증합니다. 회귀가 mismatch를 드러내면 helper를 손볼 예정이었으나, 그런 mismatch는 발견되지 않았습니다.
- `.pipeline/README.md`도 손대지 않았습니다. fallback contract 문장은 이미 `/proc`이 없을 때 `ps -p <pid> -o lstart=`를 보조 fingerprint로 쓰고 두 source가 모두 비어 있을 때만 fresh `_make_run_id()`로 fall through 한다고 적혀 있어, 이번 timeout 경계 고정만으로 README 표면을 다시 좁힐 필요가 없었습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_empty_when_ps_fails tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_empty_when_ps_binary_missing tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_empty_when_ps_times_out`
  - 결과: `Ran 4 tests`, `OK` (both-empty + returncode/missing/timeout 세 분기 모두 통과)
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_schema` full module rerun, 그리고 supervisor/watcher writer/inheritance 회귀 재실행은 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 같은 클래스 안에 회귀 한 개를 추가한 좁은 슬라이스이고, helper의 catch 경로 자체는 직전 verified 라운드들과 동일하기 때문입니다. 핸드오프도 timeout 회귀와 같은 safe-degradation family의 기존 회귀 3개만 재실행하라고 지정했고 그 4개가 모두 통과했습니다.

## 남은 리스크
- BusyBox 등 `ps -p <pid> -o lstart=` 자체를 지원하지 않는 minimal 환경에서는 helper가 여전히 `""`로 safe degradation 합니다. 더 portable한 third fallback(예: Python ctypes syscall, watcher가 owner identity를 따로 기록)은 여전히 별도 follow-up로 남습니다.
- 이번 closeout이 직접 편집한 파일은 `tests/test_pipeline_runtime_schema.py` 한 개입니다. `git status`에 보이는 다른 dirty 변경(runtime/controller/browser/docs)은 이번 라운드의 산출물이 아니므로, 다음 verify 라운드에서 이 파일 외 영역의 diff 책임을 이 closeout에 귀속하면 안 됩니다.
- timeout 회귀는 `subprocess.TimeoutExpired`가 `subprocess.SubprocessError`의 서브클래스라는 표준 라이브러리 계약에 의존합니다. 그 관계가 깨지면 helper의 catch 절도 같이 좁아져야 하므로, 다음 같은 family 라운드에서 helper와 회귀를 함께 점검하는 편이 안전합니다.
