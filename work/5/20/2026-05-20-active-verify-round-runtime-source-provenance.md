# 2026-05-20 active verify round runtime source provenance

## 변경 파일

- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-active-verify-round-runtime-source-provenance.md`

## 사용 skill

- `work-log-closeout`: handoff 실행 결과, provenance 동작, 실제 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2003`이 반복되는 active verify round dispatcher mismatch를 stale loaded watcher code, dispatch-time stale status, current source gap 중 어디에 가까운지 구분할 수 있는 runtime/source freshness provenance surface를 요구했습니다.
- 직전 `/work`는 current source가 `VERIFYING + IDLE` fixture를 `recovering/dispatch_stall/retrying`으로 계산함을 확인했지만, verify dispatch surface는 다시 `IDLE + active VERIFY_PENDING + ok/continue`를 보고했습니다.
- 이번 라운드는 재샘플링 반복이 아니라 status payload 안에 cheap deterministic provenance를 남기는 범위였습니다.

## 핵심 변경

- `pipeline_runtime/automation_health.py`에 `AUTOMATION_HEALTH_RULESET_VERSION`과 `AUTOMATION_HEALTH_DERIVED_BY`를 추가했습니다.
- `derive_automation_health`가 반환하는 payload에 top-level `automation_health_source` dict를 추가했습니다.
- `automation_health_source`는 `ruleset_version`, `derived_by`, `runtime_state`, `active_round_state`, `turn_state`, `reason_code`, `next_action`을 담습니다.
- provenance는 입력 status와 이미 계산된 payload만 사용합니다. watcher loop에서 파일 hash나 추가 disk IO를 하지 않습니다.
- active verify round 관련 unit test가 `automation_health != ok`뿐 아니라 provenance의 active round state, turn state, reason/action도 확인하도록 갱신했습니다.
- supervisor status write regression에서도 `status["automation_health_source"]`가 surfaced active round state와 decision metadata를 담는지 확인했습니다.
- `pipeline_runtime/supervisor.py`는 이번 라운드에서 수정하지 않았습니다. 해당 파일은 handoff 시작 전부터 작업트리에 `M` 상태였습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 작성하지 않았고, watcher/runtime 재시작, commit, push, branch/PR publication, merge, release, external publication도 수행하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `c812c593cdee6092eea82cb9f1c50702b16e03a1ea1c980402fa0a661005af88`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verify_pending_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verifying_round_is_not_ok_continue tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_idle_active_verify_round_as_recovering`
  - 결과: FAIL. 새 assertion에서 `VERIFY_PENDING` fixture에 `VERIFYING`을 기대하도록 잘못 넣어 1개 실패했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_non_degraded_verify_pending_dispatch_wait_is_recovering tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verify_pending_round_is_not_ok_continue tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_idle_verifying_round_is_not_ok_continue tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_idle_active_verify_round_as_recovering`
  - 결과: PASS. `Ran 4 tests in 0.020s`, `OK`.
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 출력 없음.
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py work/5/20/2026-05-20-active-verify-round-runtime-source-provenance.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-active-verify-round-runtime-source-provenance.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.
- `python3 - <<'PY' ... derive_automation_health(active_round=VERIFYING, turn_state=IDLE) ... PY`
  - 결과: PASS. `automation_health_source`가 `ruleset_version=2026-05-20.active_verify_round_status_v1`, `derived_by=pipeline_runtime.automation_health.derive_automation_health`, `active_round_state=VERIFYING`, `turn_state=IDLE`, `reason_code=dispatch_stall`, `next_action=retrying`을 포함함을 확인했습니다.

## 남은 리스크

- 이번 라운드는 automation health status provenance와 exact regression만 다뤘습니다. controller Playwright/webServer/full-smoke, broad unit, long soak는 실행하지 않았습니다.
- `pipeline_runtime/supervisor.py`는 이번 라운드에서 수정하지 않았지만 기존 dirty state로 남아 있습니다.
- running watcher를 재시작하지 않았으므로, 현재 실행 중인 watcher가 새 `automation_health_source`를 즉시 status에 쓰는지는 이번 라운드에서 확인하지 않았습니다.
- 이후 dispatcher surface가 다시 `ok/continue`를 보고하더라도, 새 payload가 배포된 watcher에서는 `automation_health_source.ruleset_version`과 `derived_by`로 stale loaded watcher 여부를 더 좁게 확인할 수 있습니다.
