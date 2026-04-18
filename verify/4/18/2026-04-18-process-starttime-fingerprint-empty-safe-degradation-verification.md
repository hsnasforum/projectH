# 2026-04-18 process_starttime_fingerprint empty safe-degradation verification

## 변경 파일
- `verify/4/18/2026-04-18-process-starttime-fingerprint-empty-safe-degradation-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-process-starttime-fingerprint-empty-safe-degradation.md`가 minimal-host 경계의 safe-degradation 회귀를 watcher exporter와 supervisor inheritance까지 확장해 고정했다고 주장하므로, 그 두 회귀가 실제 코드 경계와 맞는지 다시 확인해야 했습니다.
- 같은 날 직전 `/verify`인 `verify/4/18/2026-04-18-process-starttime-fingerprint-test-host-portable-verification.md`가 지목한 next same-family current-risk가 정확히 "both sources empty -> watcher writes empty fingerprint -> supervisor refuses inheritance" 경계였으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 트리와 일치했습니다.
  - `tests/test_watcher_core.py`에는 `TransitionTurnTest.test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`가 추가돼 있습니다.
  - 이 회귀는 `pipeline_runtime.schema._proc_starttime_fingerprint`와 `_ps_lstart_fingerprint`를 모두 `""`로 stub 한 뒤, `WatcherCore._write_current_run_pointer()`가 `watcher_fingerprint` 필드를 빠뜨리지 않고 explicit `""`로 기록하는지 단언합니다.
  - `tests/test_pipeline_runtime_supervisor.py`에는 `RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher`가 추가돼 있습니다.
  - 이 회귀는 같은 both-empty stub 상태에서 watcher가 쓴 pointer의 `watcher_fingerprint == ""`를 확인하고, supervisor가 prior `run_id`를 이어받지 않고 fresh run id로 fall through 하는지 단언합니다.
  - `watcher_core.py`, `pipeline_runtime/supervisor.py`, `pipeline_runtime/schema.py`, `.pipeline/README.md`는 이번 라운드의 핵심 동작 경계에서 추가 변경 없이 직전 verified contract와 일치합니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `py_compile`은 watcher/schema/supervisor와 관련 test 3개에 대해 통과했습니다.
  - helper empty-path 회귀 1개는 `Ran 1 test`, `OK`였습니다.
  - watcher pointer 회귀 2개는 `Ran 2 tests`, `OK`였습니다.
  - supervisor inheritance 회귀 2개는 `Ran 2 tests`, `OK`였습니다.
  - `git diff --check`도 대상 파일 경계에서 통과했습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator family로 두고 있어, 이번 empty safe-degradation 회귀 고정은 shipped browser contract를 넓히지 않는 same-family current-risk reduction으로 남아 있습니다.
- 다만 next same-family current-risk도 이번 verify에서 한 단계 더 좁아졌습니다.
  - watcher exporter의 empty-fingerprint write와 supervisor inheritance refusal은 이제 focused regression으로 고정됐습니다.
  - 그러나 supervisor가 직접 `_write_current_run_pointer()`를 호출하는 경로는 아직 non-empty fingerprint 회귀만 있고, same minimal-host both-empty 조건에서 `watcher_fingerprint`를 explicit `""`로 직렬화하는지에 대한 dedicated regression은 없습니다.
  - 현재 코드상으로는 그렇게 동작하지만, supervisor가 current-run pointer의 직접 writer이기도 하므로 writer parity를 별도 회귀로 못 박는 편이 더 안전합니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/schema.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_fingerprint_helper_returns_empty_for_live_watcher`
  - 결과: `Ran 2 tests`, `OK`
- `git diff --check -- watcher_core.py pipeline_runtime/schema.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_supervisor` full module, `tests.test_watcher_core` full module, live tmux replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 watcher/supervisor regression 한 개씩을 추가한 좁은 slice였고, runtime behavior 자체는 직전 verified round와 동일했기 때문입니다.

## 남은 리스크
- BusyBox 같은 minimal 환경에서 `ps -p <pid> -o lstart=` 자체가 지원되지 않으면 helper는 여전히 `""`로 safe degradation 합니다. 이번 회귀로 watcher exporter와 inheritance refusal은 고정됐지만, supervisor direct pointer writer의 explicit empty-fingerprint serialization parity는 아직 dedicated regression이 없습니다.
- 따라서 다음 same-family current-risk reduction은 third fallback을 더 붙이기보다, `RuntimeSupervisor._write_current_run_pointer()`가 same both-empty 조건에서 `watcher_fingerprint: ""`를 explicit field로 기록하는지 focused regression으로 고정하는 편이 더 안전합니다.
- current tree에는 unrelated dirty changes가 많으므로, 다음 Claude 라운드는 supervisor direct pointer writer parity만 다루고 controller/browser/docs 변경은 건드리지 않는 편이 맞습니다.
