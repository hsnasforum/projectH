# 2026-05-20 advisory disabled waiting next control retriage guard

## 변경 파일

- `tests/test_pipeline_runtime_automation_health.py`
  - `waiting_next_control` + `internal_only` + `next_slice_selection` +
    advisory disabled + no active control surface가 `needs_operator`가 아니라
    `attention` / `verify_followup`으로 남는 회귀 테스트를 추가했습니다.
- `work/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md`
  - 이번 implement 라운드 closeout입니다.

## 사용 skill

- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어
  `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1995`가 advisory-disabled
  `waiting_next_control` retriage 경로의 focused local guard를 요구했습니다.
- 이전 `.pipeline/operator_request.md#1994`는 `internal_only` next-control
  선택 대기였고, 실제 publication, merge, credential, destructive, safety
  operator-only 경계가 아니었습니다.
- handoff는 regression이 이미 통과하면 source fix를 강제하지 말라고
  지시했으므로, runtime 소스 변경 없이 exact status surface를 테스트로
  고정했습니다.

## 핵심 변경

- `tests/test_pipeline_runtime_automation_health.py`에
  `test_waiting_next_control_retriage_surface_is_not_operator_wait`를 추가했습니다.
- 테스트 입력은 현재 dispatch surface와 같은 형태인 `runtime_state=RUNNING`,
  `advisory_enabled=false`, `control.active_control_status=none`,
  `autonomy.mode=triage`, `reason_code=waiting_next_control`,
  `operator_policy=internal_only`, `decision_class=next_slice_selection`,
  `operator_eligible=false`, `turn_state=VERIFY_FOLLOWUP`입니다.
- 기대값은 `automation_health=attention`,
  `automation_reason_code=waiting_next_control`,
  `automation_next_action=verify_followup`입니다.
- 새 테스트가 소스 수정 없이 통과해 현재 implementation이 handoff guard를
  이미 만족함을 확인했습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge,
  release, external publication은 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지
  않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA
    `87c3e08fb2711cf05a4c160618d56148bd9cfe5efb3a89452d86b752b8b581f2`와
    일치했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.AutomationHealthTest tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_waiting_next_control_retriage_surface_is_not_operator_wait`
  - 결과: PASS. `Ran 8 tests in 0.001s`, `OK`.
- `python3 -m py_compile tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_waiting_next_control_internal_only_to_triage tests.test_watcher_core.TurnResolutionTest.test_waiting_next_control_next_slice_selection_routes_to_verify_followup`
  - 결과: PASS. `Ran 2 tests in 0.015s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health`
  - 결과: PASS. `Ran 39 tests in 0.002s`, `OK`.
- `git diff --check -- tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS, 출력 없음.
- `git diff --check -- tests/test_pipeline_runtime_automation_health.py work/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- 이번 라운드는 focused regression과 closeout만 수행했습니다. broad
  `tests.test_pipeline_runtime_supervisor`, full `tests.test_watcher_core`,
  controller startup, Playwright, `make e2e-test`, long soak는 실행하지
  않았습니다.
- `tests/test_pipeline_runtime_automation_health.py`에는 이번 라운드 이전부터
  존재하던 미커밋 변경이 섞여 있습니다. 이번 라운드에서는 새
  `waiting_next_control` exact-surface 테스트만 추가했고, 기존 변경은
  되돌리지 않았습니다.
- runtime 소스 변경은 없으므로 실제 watcher live redispatch soak까지
  보장하지는 않습니다. 다만 현재 helper-level 계약은 unit guard로
  고정했습니다.
