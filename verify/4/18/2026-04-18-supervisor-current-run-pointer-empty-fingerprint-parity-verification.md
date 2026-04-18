# 2026-04-18 supervisor current_run pointer empty-fingerprint parity verification

## 변경 파일
- `verify/4/18/2026-04-18-supervisor-current-run-pointer-empty-fingerprint-parity-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-supervisor-current-run-pointer-empty-fingerprint-parity.md`가 supervisor direct writer도 minimal-host both-empty 조건에서 `watcher_fingerprint: ""`를 explicit field로 기록한다고 주장하므로, 그 회귀가 실제 코드 경계와 맞는지 다시 확인해야 했습니다.
- 같은 날 직전 `/verify`인 `verify/4/18/2026-04-18-process-starttime-fingerprint-empty-safe-degradation-verification.md`가 다음 same-family current-risk로 정확히 supervisor direct writer parity를 지목했으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 트리와 일치했습니다.
  - `tests/test_pipeline_runtime_supervisor.py`에는 `RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`가 추가돼 있습니다.
  - 이 회귀는 `pipeline_runtime.schema._proc_starttime_fingerprint`와 `_ps_lstart_fingerprint`를 모두 `""`로 stub 한 뒤 `RuntimeSupervisor._write_current_run_pointer()`를 직접 호출하고, `run_id`, live `watcher_pid`, explicit `watcher_fingerprint == ""`를 함께 단언합니다.
  - `pipeline_runtime/supervisor.py`의 `_write_current_run_pointer()`는 현재도 `watcher_fingerprint`를 dict literal에 항상 포함해 직렬화하므로, 이번 라운드는 런타임 동작 변경 없이 existing contract를 focused regression으로 못 박는 좁은 슬라이스에 머물렀습니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `py_compile`은 `pipeline_runtime/supervisor.py`, `pipeline_runtime/schema.py`, `tests/test_pipeline_runtime_supervisor.py`에 대해 통과했습니다.
  - supervisor direct writer의 non-empty/empty 쌍 회귀는 `Ran 2 tests`, `OK`였습니다.
  - `git diff --check`도 대상 파일 경계에서 통과했습니다.
- latest `/work`가 inheritance positive/negative pair를 다시 돌리지 않은 판단도 현재 범위에서는 납득 가능합니다.
  - 이번 라운드는 기존 shared helper를 사용하는 새 dedicated regression 1개 추가에 한정됐고, inheritance 쌍이 의존하는 runtime code나 shared stubbing setup 자체를 바꾸지 않았기 때문입니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator tooling family로 두고 있어, 이번 회귀 고정은 shipped browser contract를 넓히지 않는 same-family current-risk reduction으로 남아 있습니다.
- 다음 same-family current-risk는 current-run pointer positive writer regressions의 host portability입니다.
  - `tests/test_watcher_core.py::TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint`
  - `tests/test_pipeline_runtime_supervisor.py::RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint`
  - 두 회귀 모두 live host의 non-empty fingerprint를 직접 기대하고 있어 minimal-host/portable test 관점의 환경 의존성이 남아 있습니다. 같은 shared helper seam을 stub 하는 bounded test-only slice로 두 writer를 함께 host-portable하게 만드는 편이, 지금 단계에서는 third fallback 추가나 broader rerun보다 더 작은 current-risk reduction입니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`
  - 결과: `Ran 2 tests`, `OK`
- `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_supervisor` full module, `tests.test_watcher_core` full module, live tmux replay, browser/e2e는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 supervisor test 1개 추가에 한정된 좁은 슬라이스였고, browser-visible contract나 runtime behavior 자체는 직전 verified round와 동일했기 때문입니다.

## 남은 리스크
- current-run pointer positive writer regressions는 여전히 live host fingerprint availability에 기대고 있습니다. 다음 라운드는 same helper seam을 stub 해서 watcher/supervisor positive writer 회귀 둘 다 host-portable하게 고정하는 편이 안전합니다.
- BusyBox처럼 `ps -p <pid> -o lstart=` 자체가 지원되지 않는 환경의 third fallback은 여전히 별도 follow-up입니다. 다만 이번 family의 다음 기본값은 behavior 확장보다 test portability 정리 쪽이 더 좁고 안전합니다.
- 현재 worktree에는 runtime/controller/browser/docs와 과거 `/work`/`/verify` 쪽 unrelated dirty changes가 많습니다. 다음 Claude 라운드는 writer positive regression portability만 다루고 다른 영역 diff는 건드리지 않는 편이 맞습니다.
