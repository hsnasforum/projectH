# 2026-04-18 proc fingerprint parser success extraction verification

## 변경 파일
- `verify/4/18/2026-04-18-proc-fingerprint-parser-success-extraction-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-proc-fingerprint-parser-success-extraction.md`가 `_proc_starttime_fingerprint()`의 direct success extraction 경계를 focused regression으로 고정했다고 주장하므로, 그 변화가 실제 코드 경계와 맞는지 다시 확인해야 했습니다.
- 같은 날 직전 `/verify`인 `verify/4/18/2026-04-18-proc-fingerprint-parser-safe-degradation-verification.md`가 다음 same-family current-risk로 정확히 primary `/proc` parser의 success extraction을 지목했으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 트리와 일치했습니다.
  - `tests/test_pipeline_runtime_schema.py`의 `ProcessStarttimeFingerprintTest`에는 `test_proc_starttime_fingerprint_extracts_starttime_field_from_well_formed_stat`가 실제로 추가돼 있습니다.
  - 이 회귀는 comm 안에 공백과 inner `)`가 들어간 well-formed `/proc/<pid>/stat` fixture를 사용해 `schema_module._proc_starttime_fingerprint(99999)`가 intended starttime token `"9876543210"`을 돌리는지 단언합니다.
  - 같은 회귀는 `schema_module.Path`를 stub 해 `Path("/proc/99999/stat")` 호출도 함께 고정하므로, parser가 `rfind(")")` 기준으로 outer closing paren 뒤 tail을 split 한다는 현재 contract를 직접 보호합니다.
  - 새 success 회귀는 기존 safe-degradation 회귀들 바로 앞에 배치돼 있어, primary parser family가 success → safe-degradation 순서로 한 자리에서 정리됐습니다.
- 런타임 동작 자체는 이번 라운드에서 바뀌지 않았습니다.
  - `pipeline_runtime/schema.py`의 `_proc_starttime_fingerprint()`는 현재도 `Path(...).read_text(...)`, `rfind(")")`, `len(rest) < 20`, `rest[19]` 구조를 유지합니다.
  - 이번 슬라이스는 helper 구현 수정이 아니라 existing success contract를 direct regression으로 못 박는 test-only 정리에 머뭅니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `py_compile`은 `pipeline_runtime/schema.py`, `tests/test_pipeline_runtime_schema.py`에 대해 통과했습니다.
  - focused schema regressions 4개는 `Ran 4 tests`, `OK`였습니다.
  - `git diff --check`도 대상 파일 경계에서 통과했습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator tooling family로 두고 있어, 이번 변경은 shipped browser contract를 넓히지 않는 same-family parser regression 정리로 남아 있습니다.
- 다음 same-family current-risk는 helper call contract의 남은 공백입니다.
  - `test_process_starttime_fingerprint_returns_empty_for_non_positive_pid`는 return value만 고정하고 `_proc_starttime_fingerprint` / `_ps_lstart_fingerprint`가 실제로 uncalled인지는 단언하지 않습니다.
  - `test_ps_lstart_fingerprint_returns_stripped_stdout_on_success`는 argv와 strip 결과는 고정하지만 `timeout=2.0`, `capture_output=True`, `text=True` 같은 subprocess 호출 계약은 아직 direct regression으로 못 박지 않았습니다.
  - 같은 family를 더 쪼개지 않고 helper call contract 두 군데를 한 번에 닫는 bounded test bundle이 지금 단계의 가장 작은 current-risk reduction입니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_proc_starttime_fingerprint_extracts_starttime_field_from_well_formed_stat tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_proc_starttime_fingerprint_returns_empty_when_stat_read_raises_oserror tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail`
  - 결과: `Ran 4 tests`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_schema` full module, watcher/supervisor writer/inheritance regressions, browser/e2e, live tmux replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 같은 test class 안에 regression 1개를 추가한 좁은 슬라이스였고, runtime behavior 자체는 직전 verified round와 동일했기 때문입니다.

## 남은 리스크
- `process_starttime_fingerprint()` non-positive pid short-circuit과 `_ps_lstart_fingerprint()` subprocess call kwargs 계약은 아직 dedicated regression이 없습니다. 다음 same-family current-risk reduction은 이 둘을 한 번에 닫는 helper call contract bundle로 잡는 편이 맞습니다.
- BusyBox처럼 `ps -p <pid> -o lstart=` 자체가 지원되지 않는 환경의 third fallback은 여전히 별도 follow-up입니다. 다만 이번 family의 다음 기본값은 behavior 확장보다 helper call contract 고정 쪽이 더 좁고 reviewable합니다.
- 현재 worktree에는 runtime/controller/browser/docs와 과거 `/work`/`/verify` 쪽 unrelated dirty changes가 많습니다. 다음 Claude 라운드는 schema helper call contract bundle만 다루고 다른 영역 diff는 건드리지 않는 편이 맞습니다.
