# 2026-04-18 process_starttime_fingerprint test host-portable verification

## 변경 파일
- `verify/4/18/2026-04-18-process-starttime-fingerprint-test-host-portable-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-process-starttime-fingerprint-test-host-portable.md`가 `/proc`-missing fallback 자체가 아니라 그 회귀의 host dependency를 정리했다고 주장하므로, 실제 변경이 test rewiring에만 머물렀는지와 그에 맞는 최소 검증이 그대로 통과하는지 다시 확인해야 했습니다.
- 같은 날 직전 `/verify`인 `verify/4/18/2026-04-18-process-starttime-fingerprint-proc-missing-fallback-verification.md`가 남긴 next same-family current-risk가 정확히 "fallback regression이 실제 `/proc` host를 가정한다"는 점이었으므로, 이번 라운드는 그 host-portable 정리가 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 트리와 일치했습니다.
  - `tests/test_pipeline_runtime_schema.py`의 `ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available`는 더 이상 실제 `process_starttime_fingerprint(os.getpid())` 결과나 `/proc/<pid>/stat` 가용성에 기대지 않습니다.
  - 현재 테스트는 `schema_module._proc_starttime_fingerprint`를 stable string으로 stub 하고, `schema_module._ps_lstart_fingerprint`는 mock으로 묶은 뒤 `process_starttime_fingerprint(12345)`가 primary 값을 그대로 반환하고 fallback은 호출하지 않는지만 단언합니다.
  - `pipeline_runtime/schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `.pipeline/README.md`는 이번 라운드의 핵심 동작 경계에서 변경 없이 직전 verified fallback contract와 일치합니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `py_compile`은 `pipeline_runtime/schema.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_pipeline_runtime_supervisor.py`에 대해 통과했습니다.
  - focused schema class는 `Ran 7 tests`, `OK`로 통과했습니다.
  - focused supervisor fallback inheritance regression은 `Ran 1 test`, `OK`로 통과했습니다.
  - `/work`가 함께 적은 module-level `tests.test_pipeline_runtime_schema` rerun도 `Ran 24 tests`, `OK`로 재현됐습니다.
  - `git diff --check`도 대상 파일 경계에서 통과했습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator family로 두고 있어, 이번 test-portability 정리는 shipped browser contract를 넓히지 않는 same-family current-risk reduction으로 남아 있습니다.
- 다만 next same-family current-risk도 이번 verify에서 더 좁아졌습니다.
  - helper-level로는 이미 `process_starttime_fingerprint`가 primary+fallback 모두 실패하면 `""`를 반환한다고 검증돼 있습니다.
  - 그러나 watcher exporter가 그 empty fingerprint를 실제 `current_run.json`에 기록하는 경로와, supervisor가 그 empty fingerprint 때문에 prior `run_id` inheritance를 거부하는 end-to-end 경로는 아직 명시적으로 고정돼 있지 않습니다.
  - 즉 현재 contract는 safe degradation 쪽으로 읽히지만, minimal host의 "두 source 모두 unavailable" 경계는 helper unit test 수준을 넘어선 pointer writer/reader 회귀가 아직 없습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest`
  - 결과: `Ran 7 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 24 tests`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_supervisor` full module, `tests.test_watcher_core`, live tmux replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 schema regression 한 메서드의 host-portable rewiring에만 좁게 한정됐고, runtime behavior 자체는 직전 verified fallback round와 동일했기 때문입니다.

## 남은 리스크
- BusyBox 같은 minimal 환경에서 `ps -p <pid> -o lstart=`까지 지원되지 않으면 helper는 여전히 `""`로 safe degradation 합니다. 이 자체는 현재 contract와 맞지만, watcher exporter와 supervisor inheritance가 이 empty fingerprint를 end-to-end로 어떻게 다루는지는 아직 focused regression으로 고정되지 않았습니다.
- 따라서 다음 same-family current-risk reduction은 third fallback을 더 붙이기보다, 먼저 "both sources fail -> watcher writes empty fingerprint -> supervisor refuses inheritance" 경계를 좁게 회귀로 고정하는 편이 더 안전합니다.
- current tree에는 unrelated dirty changes가 많으므로, 다음 Claude 라운드는 이 empty-fingerprint safe degradation family만 다루고 controller/browser/docs 변경은 건드리지 않는 편이 맞습니다.
