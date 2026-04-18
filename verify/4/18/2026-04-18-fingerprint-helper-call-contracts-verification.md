# 2026-04-18 fingerprint helper call contract verification

## 변경 파일
- `verify/4/18/2026-04-18-fingerprint-helper-call-contracts-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-fingerprint-helper-call-contracts.md`가 `process_starttime_fingerprint()` short-circuit과 `_ps_lstart_fingerprint()` success 호출 계약의 남은 공백 두 곳을 focused regression으로 닫았다고 주장하므로, 그 변화가 현재 트리와 실제 재실행 결과에 맞는지 다시 확인해야 했습니다.
- 같은 날 최신 `/verify`였던 `verify/4/18/2026-04-18-proc-fingerprint-parser-success-extraction-verification.md`가 다음 same-family current-risk로 정확히 이 두 call contract 단언을 지목했으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 코드와 일치했습니다.
  - `tests/test_pipeline_runtime_schema.py`의 `test_process_starttime_fingerprint_returns_empty_for_non_positive_pid`는 이제 `_proc_starttime_fingerprint`와 `_ps_lstart_fingerprint`를 둘 다 patch 한 뒤 `process_starttime_fingerprint(0)` / `(-1)`이 `""`를 돌리고 두 helper가 모두 uncalled인지를 직접 단언합니다.
  - 같은 파일의 `test_ps_lstart_fingerprint_returns_stripped_stdout_on_success`는 기존 stripped stdout / argv 단언 뒤에 `capture_output=True`, `text=True`, `timeout=2.0` kwargs를 직접 고정합니다.
  - `pipeline_runtime/schema.py`의 helper 구현은 이번 라운드에서 바뀌지 않았고, 현재 코드도 여전히 latest `/work`가 전제한 두-source contract(`/proc/<pid>/stat` -> `ps -p <pid> -o lstart=` -> `""`)와 일치합니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`는 통과했습니다.
  - targeted unittest 4개는 `Ran 4 tests`, `OK`였습니다.
  - `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`도 통과했습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 계속 internal/operator tooling family로 두고 있어, 이번 변경은 shipped browser contract를 넓히지 않는 same-family regression tightening으로 남아 있습니다.
- 다만 다음 same-family 기본값은 바로 Claude implement로 고정하지 않았습니다.
  - 현재 `process_starttime_fingerprint()`의 shipped behavior는 `/proc`과 `ps -o lstart=` 두 source만 쓰고, 둘 다 비면 `""`로 safe degradation 하는 것입니다.
  - 오늘 같은 family의 verify 흐름을 따라오면 남은 개선축은 결국 BusyBox/minimal host에서의 third fallback인데, 이 지점은 단순 assertion 추가가 아니라 "shared helper에 다른 process-start source를 붙일지"와 "owner identity seam을 다른 방식으로 넓힐지" 사이의 설계 갈림길에 가깝습니다.
  - 그래서 이번 seq 322는 약한 implement handoff를 강제로 쓰기보다, exact next slice를 다시 한 번 좁히는 Gemini arbitration으로 넘기는 편이 더 정직합니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_returns_empty_for_non_positive_pid tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_stripped_stdout_on_success tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_ps_lstart_fingerprint_returns_empty_when_ps_times_out`
  - 결과: `Ran 4 tests`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_schema` full module, watcher/supervisor integration regressions, browser/e2e, live tmux replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 `/work` 변경이 기존 test class 안의 assertion 두 곳만 좁힌 슬라이스였고, runtime helper 본문과 상위 caller 동작 자체는 직전 verified 상태와 동일했기 때문입니다.

## 남은 리스크
- BusyBox처럼 `/proc/<pid>/stat`도 없고 `ps -p <pid> -o lstart=`도 기대대로 동작하지 않는 minimal host에서는 `process_starttime_fingerprint()`가 여전히 `""`로 safe degradation 하므로, watcher/supervisor restart inheritance는 그 환경에서 fresh `run_id`로만 떨어집니다.
- 그 다음 same-family 개선은 여전히 third fallback 계열이지만, 구현 후보가 둘 이상이라 이번 라운드에서는 exact slice를 자동 확정하지 않고 `.pipeline/gemini_request.md`로 arbitration을 열었습니다.
- 현재 worktree에는 runtime/controller/browser/docs와 과거 `/work`/`/verify` 쪽 unrelated dirty changes가 계속 남아 있습니다. 다음 round는 이 verify가 다룬 fingerprint family 판단만 이어가고 unrelated diff는 건드리지 않는 편이 맞습니다.
