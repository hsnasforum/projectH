# 2026-04-18 current-run pointer positive writer host-portable verification

## 변경 파일
- `verify/4/18/2026-04-18-current-run-pointer-positive-writer-host-portable-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-current-run-pointer-positive-writer-host-portable.md`가 current-run pointer 양쪽 writer의 positive 회귀를 live host `/proc` 의존 없이 같은 shared helper seam 위로 옮겼다고 주장하므로, 그 변화가 실제 코드 경계와 맞는지 다시 확인해야 했습니다.
- 같은 날 직전 `/verify`인 `verify/4/18/2026-04-18-supervisor-current-run-pointer-empty-fingerprint-parity-verification.md`가 다음 same-family current-risk로 정확히 두 positive writer 회귀의 host portability를 지목했으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 트리와 일치했습니다.
  - `tests/test_watcher_core.py`의 `TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint`는 이제 `pipeline_runtime.schema._proc_starttime_fingerprint`를 `""`로, `_ps_lstart_fingerprint`를 stable non-empty string으로 stub 한 뒤 `WatcherCore._write_current_run_pointer()`를 호출하고 `watcher_pid`와 serialized `watcher_fingerprint`를 단언합니다.
  - `tests/test_pipeline_runtime_supervisor.py`의 `RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint`도 같은 패턴으로 stub 한 뒤 `RuntimeSupervisor._write_current_run_pointer()`가 same fallback fingerprint를 그대로 직렬화하는지 단언합니다.
  - 각 파일의 empty-path 회귀는 그대로 유지돼, watcher/supervisor 양쪽 writer가 non-empty / empty 두 경계를 같은 shared helper seam 위에서 짝으로 비추는 형태가 됐습니다.
- 런타임 동작 자체는 이번 라운드에서 바뀌지 않았습니다.
  - `watcher_core.py`의 `_write_current_run_pointer()`는 여전히 `process_starttime_fingerprint(os.getpid())` 결과를 `watcher_fingerprint`로 기록합니다.
  - `pipeline_runtime/supervisor.py`의 `_write_current_run_pointer()`도 여전히 live `experimental.pid`에서 얻은 pid와 `_watcher_process_fingerprint(...)` 결과를 `current_run.json`에 직렬화합니다.
  - 따라서 이번 슬라이스는 구현 변경이 아니라 positive 회귀의 host 가정을 제거한 test-only 정리에 머뭅니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `py_compile`은 `watcher_core.py`, `pipeline_runtime/supervisor.py`, `pipeline_runtime/schema.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_runtime_supervisor.py`에 대해 통과했습니다.
  - 두 writer의 non-empty/empty 4개 회귀는 `Ran 4 tests`, `OK`였습니다.
  - `git diff --check`도 대상 파일 경계에서 통과했습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator tooling family로 두고 있어, 이번 변경은 shipped browser contract를 넓히지 않는 same-family test portability 정리로 남아 있습니다.
- 다음 same-family current-risk는 `_ps_lstart_fingerprint()`의 timeout safe-degradation 회귀입니다.
  - `pipeline_runtime/schema.py`는 `subprocess.run(..., timeout=2.0)` 뒤 `except (OSError, subprocess.SubprocessError): return ""`를 이미 갖고 있습니다.
  - 하지만 `tests/test_pipeline_runtime_schema.py`는 현재 success / non-zero returncode / binary missing만 고정하고 있고, `subprocess.TimeoutExpired` 경계에는 dedicated regression이 없습니다.
  - 따라서 다음 기본값은 third fallback 확장보다, hung `ps`가 safe degradation으로 `""`를 돌려준다는 helper-level 회귀를 한 줄 더 고정하는 편이 더 좁고 안전합니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`
  - 결과: `Ran 4 tests`, `OK`
- `git diff --check -- watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- supervisor inheritance positive/negative pair, `tests.test_watcher_core` full module, `tests.test_pipeline_runtime_supervisor` full module, browser/e2e, live tmux replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 두 writer positive regression 본문만 same helper seam으로 rewiring 한 좁은 슬라이스였고, runtime behavior 자체는 직전 verified round와 동일했기 때문입니다.

## 남은 리스크
- `_ps_lstart_fingerprint()`의 timeout path는 코드상 safe degradation이지만 아직 dedicated regression이 없습니다. hung `ps` 경계는 다음 same-family current-risk reduction으로 바로 고정하는 편이 맞습니다.
- BusyBox처럼 `ps -p <pid> -o lstart=` 자체가 지원되지 않는 환경의 third fallback은 여전히 별도 follow-up입니다. 다만 이번 family의 다음 기본값은 behavior 확장보다 helper timeout 회귀 고정 쪽이 더 좁고 reviewable합니다.
- 현재 worktree에는 runtime/controller/browser/docs와 과거 `/work`/`/verify` 쪽 unrelated dirty changes가 많습니다. 다음 Claude 라운드는 schema helper timeout regression만 다루고 다른 영역 diff는 건드리지 않는 편이 맞습니다.
