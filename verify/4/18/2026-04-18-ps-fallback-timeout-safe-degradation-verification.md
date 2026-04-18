# 2026-04-18 ps fallback timeout safe-degradation verification

## 변경 파일
- `verify/4/18/2026-04-18-ps-fallback-timeout-safe-degradation-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-ps-fallback-timeout-safe-degradation.md`가 `_ps_lstart_fingerprint()`의 timeout safe-degradation 경계를 focused regression으로 고정했다고 주장하므로, 그 변화가 실제 코드 경계와 맞는지 다시 확인해야 했습니다.
- 같은 날 직전 `/verify`인 `verify/4/18/2026-04-18-current-run-pointer-positive-writer-host-portable-verification.md`가 다음 same-family current-risk로 정확히 `subprocess.TimeoutExpired` 경계를 지목했으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 트리와 일치했습니다.
  - `tests/test_pipeline_runtime_schema.py` 상단 import에 `subprocess`가 추가돼 있습니다.
  - `ProcessStarttimeFingerprintTest`에는 `test_ps_lstart_fingerprint_returns_empty_when_ps_times_out`가 추가돼 있습니다.
  - 이 회귀는 `schema_module.subprocess.run`이 `subprocess.TimeoutExpired(cmd=["ps"], timeout=2.0)`를 raise 하도록 stub 한 뒤 `_ps_lstart_fingerprint(99999)`가 `""`를 돌리는지 단언합니다.
  - 새 회귀는 기존 `test_ps_lstart_fingerprint_returns_empty_when_ps_fails`와 `test_ps_lstart_fingerprint_returns_empty_when_ps_binary_missing` 바로 뒤에 붙어 있어, `ps` fallback helper의 safe-degradation family가 returncode / missing / timeout 세 분기로 정리됐습니다.
- 런타임 동작 자체는 이번 라운드에서 바뀌지 않았습니다.
  - `pipeline_runtime/schema.py`의 `_ps_lstart_fingerprint()`는 현재도 `subprocess.run(..., timeout=2.0)` 뒤 `except (OSError, subprocess.SubprocessError): return ""`를 유지합니다.
  - `subprocess.TimeoutExpired`는 `subprocess.SubprocessError`의 서브클래스이므로, 이번 슬라이스는 helper 구현 수정이 아니라 existing contract를 회귀로 못 박는 test-only 정리에 머뭅니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `py_compile`은 `pipeline_runtime/schema.py`, `tests/test_pipeline_runtime_schema.py`에 대해 통과했습니다.
  - focused schema regressions 4개는 `Ran 4 tests`, `OK`였습니다.
  - `git diff --check`도 대상 파일 경계에서 통과했습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator tooling family로 두고 있어, 이번 변경은 shipped browser contract를 넓히지 않는 same-family helper regression 정리로 남아 있습니다.
- 다음 same-family current-risk는 primary `/proc` parser `_proc_starttime_fingerprint()`의 direct safe-degradation branches입니다.
  - 현재 suite는 `process_starttime_fingerprint()`의 non-positive pid / proc-success / ps-fallback / both-empty, 그리고 `_ps_lstart_fingerprint()`의 success / fail / missing / timeout을 고정합니다.
  - 반면 `_proc_starttime_fingerprint()` 자체의 unreadable file, malformed stat payload, truncated field-count 경계에는 dedicated regression이 없습니다.
  - 따라서 다음 기본값은 third fallback 확장보다, primary source parser가 malformed `/proc/<pid>/stat`에서 조용히 `""`로 safe degradation 하는 existing contract를 focused test bundle로 고정하는 편이 더 좁고 안전합니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_empty_when_ps_fails tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_empty_when_ps_binary_missing tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_empty_when_ps_times_out`
  - 결과: `Ran 4 tests`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_schema` full module, watcher/supervisor writer regressions, browser/e2e, live tmux replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 같은 test class 안에 regression 1개를 추가한 좁은 슬라이스였고, runtime behavior 자체는 직전 verified round와 동일했기 때문입니다.

## 남은 리스크
- `_proc_starttime_fingerprint()`의 unreadable / malformed / truncated `/proc` stat parsing branches는 코드상 safe degradation이지만 아직 dedicated regression이 없습니다. 다음 same-family current-risk reduction은 이 primary parser 경계를 focused bundle로 고정하는 편이 맞습니다.
- BusyBox처럼 `ps -p <pid> -o lstart=` 자체가 지원되지 않는 환경의 third fallback은 여전히 별도 follow-up입니다. 다만 이번 family의 다음 기본값은 behavior 확장보다 primary parser regression 고정 쪽이 더 좁고 reviewable합니다.
- 현재 worktree에는 runtime/controller/browser/docs와 과거 `/work`/`/verify` 쪽 unrelated dirty changes가 많습니다. 다음 Claude 라운드는 schema primary parser regression bundle만 다루고 다른 영역 diff는 건드리지 않는 편이 맞습니다.
