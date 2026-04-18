# 2026-04-18 _proc_starttime_fingerprint 파서 safe-degradation 회귀 고정

## 변경 파일
- `tests/test_pipeline_runtime_schema.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-ps-fallback-timeout-safe-degradation.md`와 `verify/4/18/2026-04-18-ps-fallback-timeout-safe-degradation-verification.md`는 fallback `_ps_lstart_fingerprint`의 timeout 분기까지 safe-degradation 회귀로 닫았습니다.
- 같은 family의 남은 current-risk는 primary source인 `_proc_starttime_fingerprint`였습니다. helper 본문은 이미 (a) `OSError`(`FileNotFoundError` 포함) catch, (b) `)` 미발견 시 `""`, (c) tail field < 20 시 `""`로 떨어지지만, 그 세 분기 어느 것도 dedicated 회귀로 못 박혀 있지 않았습니다. malformed `/proc/<pid>/stat` payload나 unreadable stat이 들어왔을 때 helper가 partial 값이나 예외를 흘려보내지 않는다는 계약이 회귀 표면에 빠져 있었습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 318`)는 새 third fallback이나 runtime 행동 변경 없이, primary parser의 세 safe-degradation 경계만 같은 회귀 클래스에 추가하라고 좁게 지목했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_schema.py`
  - `ProcessStarttimeFingerprintTest`에 세 회귀를 추가했습니다. 기존 `_ps_lstart_fingerprint_returns_stripped_stdout_on_success` 바로 앞에 묶어, primary parser → fallback success/fail 회귀들이 한 자리에서 family 전체를 비추도록 배치했습니다.
    - `test_proc_starttime_fingerprint_returns_empty_when_stat_read_raises_oserror`
      - `schema_module.Path`를 stub해서 `read_text`가 `FileNotFoundError`를 raise 하도록 만든 뒤, helper가 `""`를 돌리고 `Path("/proc/99999/stat")` 호출이 정확히 한 번 일어났는지 단언합니다. 이 회귀는 `FileNotFoundError ⊂ OSError` 계약 위에서 unreadable / non-existent stat 두 케이스를 같이 보호합니다.
    - `test_proc_starttime_fingerprint_returns_empty_when_stat_payload_has_no_closing_paren`
      - `read_text`를 `")` 없는 payload로 stub 한 뒤 helper가 `rfind(")") < 0` 분기에서 `""`를 돌리는지 단언합니다.
    - `test_proc_starttime_fingerprint_returns_empty_when_stat_tail_has_fewer_than_twenty_fields`
      - `read_text`를 `(cmd)` 뒤에 11개 필드만 있는 payload로 stub 한 뒤 helper가 `len(rest) < 20` 분기에서 `""`를 돌리는지(즉 `rest[19]` IndexError가 escape 하지 않는지) 단언합니다.
  - 회귀 모두 `mock.patch.object(schema_module, "Path", return_value=fake_path)` 패턴으로 `Path` 호출 자체를 stub seam으로 잡았습니다. helper 안에서 `Path(...)`가 한 번만 호출되므로 다른 schema helper의 `Path` 사용에 영향이 없습니다.
- `pipeline_runtime/schema.py`는 손대지 않았습니다. helper의 세 safe-degradation 분기는 모두 현재 구현이 그대로 통과시켰고, 이번 회귀는 그 동작을 좁게 못 박는 데 그쳤습니다.
- `.pipeline/README.md`도 손대지 않았습니다. fallback contract와 빈 fingerprint면 fresh `_make_run_id()`로 fall through 한다는 경계는 직전 라운드들에서 이미 한 줄로 적혀 있어, primary parser 분기 회귀 추가만으로 README 표면을 다시 좁힐 필요가 없었습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_proc_starttime_fingerprint_returns_empty_when_stat_read_raises_oserror tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_proc_starttime_fingerprint_returns_empty_when_stat_payload_has_no_closing_paren tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_proc_starttime_fingerprint_returns_empty_when_stat_tail_has_fewer_than_twenty_fields tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail`
  - 결과: `Ran 5 tests`, `OK` (primary 사용 경로 + 새 세 분기 + both-empty bookend 모두 통과)
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_schema` full module rerun, 그리고 supervisor/watcher writer/inheritance 회귀 재실행은 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 같은 클래스 안에 회귀 세 개를 추가한 좁은 슬라이스이고, helper 본문은 직전 verified 라운드들과 동일하기 때문입니다. 핸드오프도 primary parser 새 회귀와 같은 family bookend(`uses_proc_when_available`, `returns_empty_when_proc_and_ps_both_fail`)만 재실행하라고 지정했고 그 5개가 모두 통과했습니다.

## 남은 리스크
- 새 회귀는 `_proc_starttime_fingerprint`가 내부적으로 `Path(...)`를 한 번 호출하고 그 결과의 `read_text(encoding=...)`을 사용한다는 현재 구현 형태에 의존합니다. helper가 다른 IO 추상화로 바뀌면(예: `os.open` 직접 사용) stub seam을 같이 옮겨야 합니다. 다만 두 인터페이스 모두 같은 contract("`""`로 safe degradation")를 유지하면 회귀 의도는 유지됩니다.
- BusyBox 등 `ps -p <pid> -o lstart=` 자체를 지원하지 않는 minimal 환경에서는 helper가 여전히 `""`로 safe degradation 합니다. 더 portable한 third fallback(예: Python ctypes syscall, watcher가 owner identity를 따로 기록)은 여전히 별도 follow-up로 남습니다.
- 이번 closeout이 직접 편집한 파일은 `tests/test_pipeline_runtime_schema.py` 한 개입니다. `git status`에 보이는 다른 dirty 변경(runtime/controller/browser/docs)은 이번 라운드의 산출물이 아니므로, 다음 verify 라운드에서 이 파일 외 영역의 diff 책임을 이 closeout에 귀속하면 안 됩니다.
