# 2026-04-18 process_starttime_fingerprint /proc-missing fallback

## 변경 파일
- `pipeline_runtime/schema.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`

## 사용 skill
- `doc-sync`: shared fingerprint helper의 `/proc`-missing fallback 경계를 `.pipeline/README.md`에 현재 구현 truth로 맞추기 위해 사용했습니다.
- `work-log-closeout`: 이번 라운드 closeout을 repo 규칙 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- 직전 라운드 `work/4/18/2026-04-18-watcher-exporter-current-run-owner-metadata.md`와 `verify/4/18/2026-04-18-watcher-exporter-current-run-owner-metadata-verification.md`는 watcher exporter와 supervisor가 같은 owner contract를 공유하도록 `pipeline_runtime/schema.process_starttime_fingerprint`를 한 helper로 모았지만, 그 helper는 여전히 `/proc/<pid>/stat` 한 source에만 의존했습니다.
- 핸드오프(`STATUS: implement`, `CONTROL_SEQ: 312`)가 지목한 same-family current-risk는 명확합니다. `/proc`이 없는 환경에서는 fingerprint가 빈 문자열이 되어 supervisor inheritance가 항상 fresh `_make_run_id()`로 fall through 합니다. 이 경우 stale STOPPED snapshot 문제는 그대로 살아 있습니다.
- 그래서 이번 슬라이스에서는 helper에 POSIX `ps -p <pid> -o lstart=` 기반 보조 source를 한 단계 더 붙여, `/proc`을 못 읽는 환경에서도 supervisor와 watcher가 같은 fingerprint로 owner-match 게이트를 통과할 수 있게 했습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`
  - `subprocess`를 import에 추가했습니다.
  - 기존 `process_starttime_fingerprint`를 두 helper로 분해했습니다.
    - `_proc_starttime_fingerprint(pid)`: 기존 `/proc/<pid>/stat` field 22(starttime) 추출 로직을 그대로 담은 primary source.
    - `_ps_lstart_fingerprint(pid)`: POSIX `ps -p <pid> -o lstart=` 출력을 그대로 fingerprint로 쓰는 보조 source. 2초 타임아웃을 두고, `OSError` / `SubprocessError` / `returncode != 0` / 빈 출력은 모두 빈 문자열을 돌려 caller가 "inheritance 불가"로 처리하게 했습니다.
  - public `process_starttime_fingerprint(pid)`는 (a) pid가 양수일 때만 실행하고, (b) 먼저 `_proc_starttime_fingerprint(pid)`를 시도해 비어 있지 않으면 그대로 돌리고, (c) 비어 있으면 `_ps_lstart_fingerprint(pid)`로 fall through 한 결과를 그대로 돌립니다. 두 source가 모두 비어 있으면 그때만 빈 문자열이 돌아가므로 잘못된 inherit는 절대 만들어지지 않습니다.
  - watcher_core / supervisor caller는 변경 없이 같은 entry point를 그대로 호출합니다. owner-match 정의가 다시 두 writer 사이에서 drift 하지 않도록 helper 한 곳에 머물러 있습니다.
- `tests/test_pipeline_runtime_schema.py`
  - `mock`, `pipeline_runtime.schema as schema_module`, `process_starttime_fingerprint`를 import에 추가했습니다.
  - 신규 `ProcessStarttimeFingerprintTest` 클래스를 추가해 fallback 경계를 직접 잡았습니다.
    - non-positive pid는 두 source를 호출하지 않고 빈 문자열을 돌리는지
    - `/proc`이 살아 있을 때는 fallback을 호출하지 않고 primary 결과를 돌리는지(같은 호출을 반복해도 결과가 동일한지로 확인)
    - `/proc` source가 빈 문자열을 돌릴 때는 fallback이 호출되고 그 결과를 그대로 돌리는지
    - `/proc`/fallback 모두 빈 문자열을 돌릴 때는 helper도 빈 문자열을 돌리는지
    - `_ps_lstart_fingerprint`가 `subprocess.run`의 stdout을 strip 해서 돌리는지, returncode 실패면 빈 문자열을 돌리는지, `ps` 바이너리가 없어 `FileNotFoundError`가 나도 안전하게 빈 문자열을 돌리는지
- `tests/test_pipeline_runtime_supervisor.py`
  - `test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback`을 추가해 end-to-end 경계를 다시 잡았습니다. `_proc_starttime_fingerprint`를 빈 문자열로, `_ps_lstart_fingerprint`를 stable string으로 stub 한 뒤, watcher exporter가 기록한 `current_run.json`이 그 fallback string을 `watcher_fingerprint`로 가지고 있고, 새 `RuntimeSupervisor`도 같은 fallback fingerprint를 통해 watcher run_id를 그대로 이어받는지 확인합니다. `PIPELINE_RUNTIME_RUN_ID` 환경 변수로 watcher run_id를 명시해 supervisor의 fresh `_make_run_id()`가 우연히 같아져 발생할 수 있는 flaky match도 배제했습니다.
- `.pipeline/README.md`
  - shared fingerprint helper 항목 뒤에 한 문장을 추가해, `/proc`을 못 읽을 때 POSIX `ps -p <pid> -o lstart=` 출력을 보조 fingerprint로 쓰고, 두 source가 모두 비어 있을 때만 빈 문자열을 돌려 fresh `_make_run_id()`로 fall through 한다는 계약을 적었습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback`
  - 결과: `Ran 8 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: 전체 통과 (기존 schema 회귀 + 신규 fingerprint fallback 회귀 포함)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: 전체 통과 (기존 supervisor inheritance 회귀 + 신규 fallback end-to-end 회귀 포함)
- `python3 -m unittest tests.test_watcher_core.TransitionTurnTest`
  - 결과: 전체 통과 (watcher exporter pointer/transition 경로)
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 126 tests`, `OK`
- `git diff --check -- watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart/replay에서 fallback 경로가 실제로 분기됐는지는 이번 라운드에서 다시 돌리지 않았습니다. 이유는 이번 변경이 helper 내부 분기와 supervisor/watcher pointer 경계에 한정되고, schema 신규 7개 + supervisor 신규 1개 + 기존 supervisor·watcher full 회귀로 fallback path가 직접 고정됐기 때문입니다.

## 남은 리스크
- fallback이 `ps` 바이너리에 의존하므로, BusyBox 같이 `ps -o lstart=` 옵션을 지원하지 않는 minimal 환경에서는 fallback도 빈 문자열을 돌립니다. 이 경우 inheritance는 여전히 fresh `_make_run_id()`로 fall through 하는 safe degradation이 됩니다. 더 portable한 fingerprint(예: Python ctypes 기반 syscall, 또는 watcher가 `current_run.json`에 owner identity를 직접 기록)는 별도 follow-up로 다룰 수 있습니다.
- `ps` 출력 포맷은 시스템 locale에 따라 약간 달라질 수 있지만, supervisor와 watcher가 같은 시스템에서 같은 시점에 같은 pid에 대해 호출하므로 owner-match 비교는 그대로 성립합니다. 다른 시스템 사이의 fingerprint 비교가 의미를 갖는 흐름은 현재 contract 안에 없습니다.
- 2초 timeout과 `subprocess.run` 호출은 한 번의 pointer write/inheritance check마다 발생하지만, `/proc`이 살아 있는 표준 Linux 경로에서는 primary `/proc` 추출이 먼저 성공해 fallback이 절대 호출되지 않으므로 production 비용 변화는 없습니다.
