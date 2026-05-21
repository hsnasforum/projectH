# 2026-05-19 Codex verify dispatch failure loop guard

## 변경 파일

- `verify_fsm.py`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_control_writers.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `verify/5/19/2026-05-19-reviewed-memory-transition-apply-result-fingerprint-doc-sync.md`
- `verify/5/19/2026-05-19-codex-verify-dispatch-failure-loop-guard.md`
- `.pipeline/operator_request.md` (gitignored runtime control artifact)

## 사용 skill

- `security-gate`: runtime control/dispatch 상태와 operator boundary 표면을 바꾸는 변경이라 local-first, 승인/운영 경계, 로그/문서 범위를 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- launcher/controller에서 `cleared_failed_dispatch_prompt` 계열 Codex verify prompt가 반복 주입되고, `dispatch_fail_count`가 14까지 누적된 상태가 확인되었습니다.
- 즉시 루프를 끊기 위해 matching `/verify` note를 작성하고 `.pipeline/operator_request.md#1978`을 `codex_verify_dispatch_failure_loop` stop으로 갱신했습니다.
- 재발 방지를 위해 verify prompt submit 자체가 retry budget을 소진하면 더 이상 자동 재주입하지 않고 operator-required 상태로 수렴해야 했습니다.

## 핵심 변경

- `verify_fsm.py`에 `codex_verify_dispatch_failure_loop`과 `dispatch_failed_submit` reason/stage를 추가했습니다.
- `send_keys` 실패가 `retry_budget`을 소진하면 job을 degraded로 고정하고, lease를 해제한 뒤 이후 `_handle_verify_pending`에서 같은 job을 재디스패치하지 않게 했습니다.
- launcher health가 해당 degraded reason을 `needs_operator + operator_required`로 해석하고, incident family는 기존 `dispatch_stall` 계열로 묶도록 했습니다.
- operator control writer/autonomy validator가 `REASON_CODE: codex_verify_dispatch_failure_loop`, `DECISION_CLASS: runtime_dispatch_gate`를 유효한 structured stop으로 받아들이게 했습니다.
- supervisor dispatch stall marker는 이 reason도 `action=degraded`로 표면화하도록 조정했습니다.
- `.pipeline/README.md`와 pipeline runtime 기술설계/운영 런북에 retry-budget 소진 시 자동 재주입 중단과 operator-required surface를 문서화했습니다.

## 검증

- `python3 -m py_compile verify_fsm.py pipeline_runtime/automation_health.py pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_control_writers.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_codex_verify_dispatch_failure_loop_requires_operator tests.test_pipeline_runtime_control_writers.ControlWritersTest.test_runtime_dispatch_gate_operator_request_is_supported`
  - 통과: 2 tests OK.
- `python3 -m unittest -v tests.test_watcher_core.VerifyPendingBackoffTest.test_failed_dispatch_exhausts_retry_budget_marks_operator_degraded`
  - 통과: 1 test OK.
- `python3 -m unittest -v tests.test_watcher_core.VerifyPendingBackoffTest`
  - 통과: 8 tests OK.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health`
  - 통과: 38 tests OK.
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers`
  - 통과: 8 tests OK.
- `rg -n "codex_verify_dispatch_failure_loop|dispatch_failed_submit|runtime_dispatch_gate" verify_fsm.py pipeline_runtime tests .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 통과: code/test/docs 반영 위치를 확인했습니다.
- `git diff --check -- verify_fsm.py pipeline_runtime/automation_health.py pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_control_writers.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 통과: 출력 없음.
- `git diff --check -- work/5/19/2026-05-19-codex-verify-dispatch-failure-loop-guard.md verify/5/19/2026-05-19-reviewed-memory-transition-apply-result-fingerprint-doc-sync.md .pipeline/operator_request.md`
  - 통과: 출력 없음.
- `git diff --check -- verify/5/19/2026-05-19-codex-verify-dispatch-failure-loop-guard.md`
  - 통과: 출력 없음.

## 남은 리스크

- 현재 operator stop은 `.pipeline/operator_request.md#1978`로 의도적으로 유지했습니다. 자동화 재개 여부는 운영자 결정 영역입니다.
- live runtime restart/stop/start, tmux 실제 lane repair, controller 브라우저 확인, Playwright, 전체 unittest, long soak는 실행하지 않았습니다.
- 작업 트리는 기존 dirty state가 많은 상태였고, 관련 없는 기존 변경은 되돌리지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.
