# 2026-04-18 fingerprint helper 남은 call contract 회귀 고정

## 변경 파일
- `tests/test_pipeline_runtime_schema.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-proc-fingerprint-parser-success-extraction.md`와 `verify/4/18/2026-04-18-proc-fingerprint-parser-success-extraction-verification.md`는 `_proc_starttime_fingerprint`의 success 추출 + 세 safe-degradation 분기를 회귀로 닫았습니다.
- 직전 라운드를 받은 첫 dispatch에는 stale `STATUS: implement_blocked / BLOCK_ID: 12f8313641be23662f0765cb667d93966d3f87d7` sentinel이 떠 있었지만, latest persistent truth(직전 `/work` + `/verify`)는 여전히 success 추출까지만 닫았고 이번 핸드오프가 지목한 두 call contract 단언을 회귀에 못 넣은 상태였습니다. 핸드오프 자체가 그 stale sentinel을 false-positive로 처리하고 같은 슬라이스를 다시 진행하라고 명시해, 이번 라운드는 그 지시를 그대로 따랐습니다.
- 같은 family의 남은 current-risk는 helper의 call contract 두 곳입니다.
  - `process_starttime_fingerprint(0)` / `(-1)`은 `""`를 돌리지만, primary/`fallback` 두 helper가 실제로 호출되지 않는다는 short-circuit contract는 회귀 표면에 빠져 있었습니다. 이 short-circuit이 무너지면 supervisor가 live watcher pid가 0인 상황에서도 `/proc` 또는 `ps`를 호출할 수 있게 됩니다.
  - `_ps_lstart_fingerprint` success 회귀는 argv 첫 토큰과 stripped stdout만 단언하고, 안전 경계를 결정하는 subprocess kwargs(`capture_output=True`, `text=True`, `timeout=2.0`)는 회귀가 보호하지 않았습니다. 그 중 하나라도 누락되면 timeout safe-degradation, stdout strip, capture 격리 가정이 동시에 흔들립니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 321`)는 새 분기나 third fallback 없이 두 단언을 같은 클래스에 한 라운드로 묶어 좁히라고 지목했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_schema.py`
  - `test_process_starttime_fingerprint_returns_empty_for_non_positive_pid`
    - `_proc_starttime_fingerprint`와 `_ps_lstart_fingerprint`를 둘 다 `mock.patch.object(schema_module, ...)`로 묶고 `process_starttime_fingerprint(0)` / `(-1)`을 호출합니다.
    - 단언:
      - 두 호출 모두 `""` 반환 (기존 단언 유지)
      - `proc_mock.assert_not_called()` / `ps_mock.assert_not_called()` (새 short-circuit 단언)
    - 새 호출 contract가 깨지면 회귀가 직접 잡히도록 inline comment를 짧게 하나 적어 두었습니다.
  - `test_ps_lstart_fingerprint_returns_stripped_stdout_on_success`
    - 기존 argv / stripped stdout 단언은 그대로 두고 그 뒤에 kwargs 단언을 붙였습니다.
    - 단언:
      - `run_mock.call_args.kwargs.get("capture_output") is True`
      - `run_mock.call_args.kwargs.get("text") is True`
      - `run_mock.call_args.kwargs.get("timeout") == 2.0`
    - 이 세 단언으로 `subprocess.run(..., capture_output=True, text=True, timeout=2.0)` contract가 한 자리에 못 박혀 timeout safe-degradation, stdout strip 정합성, stdout/stderr 격리가 한 회귀로 보호됩니다.
  - 평행한 새 테스트를 따로 만들지 않고 기존 두 회귀 본문을 좁힌 방식이라, `ProcessStarttimeFingerprintTest` 클래스 구조가 `non-positive short-circuit → primary success → primary safe-degradation → fallback success/fail/missing/timeout` 흐름을 그대로 유지합니다.
- `pipeline_runtime/schema.py`는 손대지 않았습니다. tightened 회귀들이 현재 helper 동작을 그대로 통과시켰고, mismatch는 발견되지 않았습니다.
- `.pipeline/README.md`도 손대지 않았습니다. fallback contract와 빈 fingerprint면 fresh `_make_run_id()`로 fall through 한다는 경계는 직전 라운드들에서 이미 한 줄로 적혀 있어, helper call contract 회귀 추가만으로 README 표면을 다시 좁힐 필요가 없었습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_for_non_positive_pid tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_stripped_stdout_on_success tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_empty_when_ps_times_out`
  - 결과: `Ran 4 tests`, `OK` (tightened non-positive short-circuit + primary 사용 경로 + tightened ps success kwargs + ps timeout 모두 통과)
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_schema` full module rerun과 supervisor/watcher writer/inheritance 회귀 재실행은 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 같은 클래스 안에 회귀 두 개의 단언만 좁힌 슬라이스이고, helper 본문은 직전 verified 라운드들과 동일하기 때문입니다. 핸드오프도 짝이 되는 4개 회귀만 재실행하라고 지정했고 그 4개가 모두 통과했습니다.

## 남은 리스크
- 새 단언은 `subprocess.run`이 `capture_output`/`text`/`timeout`을 keyword로 받는다는 standard library 계약에 의존합니다. 미래에 helper가 `Popen` 등 다른 인터페이스로 바뀌면 같은 의도를 같은 자리에서 새로 못 박아야 합니다.
- BusyBox 등 `ps -p <pid> -o lstart=` 자체를 지원하지 않는 minimal 환경에서는 helper가 여전히 `""`로 safe degradation 합니다. 더 portable한 third fallback(예: Python ctypes syscall, watcher가 owner identity를 따로 기록)은 여전히 별도 follow-up로 남습니다.
- 이번 closeout이 직접 편집한 파일은 `tests/test_pipeline_runtime_schema.py` 한 개입니다. `git status`에 보이는 다른 dirty 변경(runtime/controller/browser/docs)은 이번 라운드의 산출물이 아니므로, 다음 verify 라운드에서 이 파일 외 영역의 diff 책임을 이 closeout에 귀속하면 안 됩니다.
