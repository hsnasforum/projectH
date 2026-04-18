# 2026-04-18 proc fingerprint parser safe-degradation verification

## 변경 파일
- `verify/4/18/2026-04-18-proc-fingerprint-parser-safe-degradation-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-proc-fingerprint-parser-safe-degradation.md`가 `_proc_starttime_fingerprint()`의 safe-degradation 분기를 focused regression으로 고정했다고 주장하므로, 그 변화가 실제 코드 경계와 맞는지 다시 확인해야 했습니다.
- 같은 날 직전 `/verify`인 `verify/4/18/2026-04-18-ps-fallback-timeout-safe-degradation-verification.md`가 다음 same-family current-risk로 정확히 primary `/proc` parser의 unreadable / malformed / truncated 경계를 지목했으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 트리와 일치했습니다.
  - `tests/test_pipeline_runtime_schema.py`의 `ProcessStarttimeFingerprintTest`에 `_proc_starttime_fingerprint()` 전용 safe-degradation 회귀 3개가 실제로 추가돼 있습니다.
  - `test_proc_starttime_fingerprint_returns_empty_when_stat_read_raises_oserror`는 `schema_module.Path(...).read_text()`가 `FileNotFoundError`를 raise 하도록 stub 한 뒤 `""`를 단언합니다.
  - `test_proc_starttime_fingerprint_returns_empty_when_stat_payload_has_no_closing_paren`는 closing `)`가 없는 malformed payload에서 `""`를 단언합니다.
  - `test_proc_starttime_fingerprint_returns_empty_when_stat_tail_has_fewer_than_twenty_fields`는 truncated tail에서 `""`를 단언합니다.
  - 새 회귀들은 `test_process_starttime_fingerprint_uses_proc_when_available`와 `test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail` 사이에 붙어 있어, primary parser family가 success bookend와 safe-degradation branches 사이에서 한 자리로 정리됐습니다.
- 런타임 동작 자체는 이번 라운드에서 바뀌지 않았습니다.
  - `pipeline_runtime/schema.py`의 `_proc_starttime_fingerprint()`는 현재도 `Path(...).read_text(...)`, `rfind(")")`, `len(rest) < 20`, `rest[19]` 구조를 유지합니다.
  - 이번 슬라이스는 helper 구현 수정이 아니라 existing safe-degradation contract를 direct regression으로 못 박는 test-only 정리에 머뭅니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `py_compile`은 `pipeline_runtime/schema.py`, `tests/test_pipeline_runtime_schema.py`에 대해 통과했습니다.
  - focused schema regressions 5개는 `Ran 5 tests`, `OK`였습니다.
  - `git diff --check`도 대상 파일 경계에서 통과했습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator tooling family로 두고 있어, 이번 변경은 shipped browser contract를 넓히지 않는 same-family parser regression 정리로 남아 있습니다.
- 다음 same-family current-risk는 `_proc_starttime_fingerprint()`의 direct success extraction regression입니다.
  - 현재 suite는 `process_starttime_fingerprint_uses_proc_when_available`를 통해 proc-success selection은 고정하지만, `_proc_starttime_fingerprint()` 자체가 well-formed `/proc/<pid>/stat` payload에서 `rest[19]`를 정확히 뽑는 direct regression은 없습니다.
  - 특히 현재 parser가 `rfind(")")` 뒤를 split 하는 구조인 만큼, command name에 공백이 들어간 정상 payload에서도 intended field를 그대로 뽑는지 direct fixture로 고정하는 편이 더 좁고 안전합니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_proc_starttime_fingerprint_returns_empty_when_stat_read_raises_oserror tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_proc_starttime_fingerprint_returns_empty_when_stat_payload_has_no_closing_paren tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_proc_starttime_fingerprint_returns_empty_when_stat_tail_has_fewer_than_twenty_fields tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_when_proc_and_ps_both_fail`
  - 결과: `Ran 5 tests`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_schema` full module, watcher/supervisor writer/inheritance regressions, browser/e2e, live tmux replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경이 같은 test class 안에 regression 3개를 추가한 좁은 슬라이스였고, runtime behavior 자체는 직전 verified round와 동일했기 때문입니다.

## 남은 리스크
- `_proc_starttime_fingerprint()`의 direct success extraction은 아직 dedicated regression이 없습니다. 다음 same-family current-risk reduction은 well-formed `/proc/<pid>/stat` fixture에서 intended starttime field를 정확히 뽑는지 focused regression으로 고정하는 편이 맞습니다.
- BusyBox처럼 `ps -p <pid> -o lstart=` 자체가 지원되지 않는 환경의 third fallback은 여전히 별도 follow-up입니다. 다만 이번 family의 다음 기본값은 behavior 확장보다 primary parser success regression 고정 쪽이 더 좁고 reviewable합니다.
- 현재 worktree에는 runtime/controller/browser/docs와 과거 `/work`/`/verify` 쪽 unrelated dirty changes가 많습니다. 다음 Claude 라운드는 schema primary parser success regression만 다루고 다른 영역 diff는 건드리지 않는 편이 맞습니다.
