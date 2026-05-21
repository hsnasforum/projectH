# 2026-05-20 idle active verify round status surface guard

## 변경 파일

- `pipeline_runtime/automation_health.py`
  - `turn_state=IDLE`인 동안 `active_round.state`가 `VERIFY_PENDING` 또는
    `VERIFYING`이면 `ok/continue`로 떨어지지 않고 `recovering` /
    `dispatch_stall` / `retrying`으로 표면화하는 guard를 추가했습니다.
- `tests/test_pipeline_runtime_automation_health.py`
  - `IDLE + VERIFY_PENDING`, `IDLE + VERIFYING` active round 회귀 테스트를
    추가했습니다.
  - 기존 current-work verify round 테스트의 기대값을 `ok/continue`에서
    `recovering/retrying`으로 갱신했습니다.
- `work/5/20/2026-05-20-idle-active-verify-round-status-surface-guard.md`
  - 이번 implement 라운드 closeout입니다.

## 사용 skill

- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어
  `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1996`이 public status에서
  `turn_state=IDLE`인데 `active_round`가 `VERIFY_PENDING` 또는 `VERIFYING`인
  상태를 `automation_health=ok`, `automation_next_action=continue`로 숨기지
  않는 focused runtime status-surface guard를 요구했습니다.
- 이전 verify 기록에서 dispatcher surface와 follow-up status 모두
  IDLE turn과 active verify round가 같이 보이는 잔여 리스크를 확인했습니다.
- 이는 publication, merge, credential/auth, destructive action,
  approval/truth-sync repair, immediate safety stop이 아니라 local status
  truth-surface 보강입니다.

## 핵심 변경

- `ACTIVE_VERIFY_ROUND_STATES = {"VERIFY_PENDING", "VERIFYING"}`와
  `_active_verify_round_state()` helper를 추가했습니다.
- `derive_automation_health()`에서 non-degraded runtime, `turn_state=IDLE`,
  active verify round 조합을 `recovering` / `dispatch_stall` / `retrying`으로
  반환하게 했습니다.
- degraded reason, real operator boundary, existing dispatch wait stage,
  verify follow-up, publication/PR/merge boundary 처리는 기존 우선순위를
  유지했습니다.
- helper-level regression이 exported automation health 계산을 직접 덮으므로
  별도 supervisor 테스트는 추가하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge,
  release, external publication은 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지
  않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA
    `81d7b89fb9822aee2649a25dcc6f89fc3c3f5c8f9304a9d19a5bc0e63cfc7cf8`와
    일치했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verify_pending_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verifying_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_current_work_verify_round_is_not_misread_as_idle_release`
  - 결과: FAIL. source fix 전 세 테스트 모두 `ok`가 반환되어 실패했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verify_pending_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verifying_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_current_work_verify_round_is_not_misread_as_idle_release tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_non_degraded_verify_pending_dispatch_wait_is_recovering tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_real_risk_operator_stop_stays_needs_operator tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_codex_verify_dispatch_failure_loop_requires_operator`
  - 결과: PASS. `Ran 6 tests in 0.000s`, `OK`.
- `python3 -m py_compile pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health`
  - 결과: PASS. `Ran 41 tests in 0.002s`, `OK`.
- `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS, 출력 없음.
- `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/20/2026-05-20-idle-active-verify-round-status-surface-guard.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- 이번 라운드는 helper-level automation health guard와 단위 테스트에 한정했습니다.
  full `tests.test_pipeline_runtime_supervisor`, full `tests.test_watcher_core`,
  controller startup, Playwright, `make e2e-test`, long soak는 실행하지
  않았습니다.
- `pipeline_runtime/automation_health.py`와
  `tests/test_pipeline_runtime_automation_health.py`에는 이번 라운드 이전부터
  존재하던 미커밋 변경도 섞여 있습니다. 이번 라운드에서는 active verify
  round status-surface guard와 관련 테스트만 추가/갱신했고, 기존 변경은
  되돌리지 않았습니다.
- `.pipeline/README.md` 등 runtime 문서에는 이번 라운드에서 새 문구를
  추가하지 않았습니다. 기존 no-silent-stall 원칙 안의 helper-level 보강으로
  처리했으며, 문서 세부 예시 확장이 필요하면 별도 docs sync가 필요합니다.
