# 2026-05-12 Pipeline launcher idle next-control health

## 변경 파일

- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/12/2026-05-12-pipeline-launcher-idle-next-control-health.md`

## 사용 skill

- `security-gate`: runtime control/status health 표면화 변경이 로컬 상태 판단에만 머물고 승인, 저장, 외부 게시, 파괴적 실행 경계를 넓히지 않는지 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 실행한 검증, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유

- 직전 duplicate handoff idle surface 수정으로 public `control.active_control_status=none`, `turn_state.state=IDLE`, `progress={}`는 정리됐지만, `derive_automation_health()`가 같은 상태를 `ok/continue`로 끝낼 수 있었습니다.
- 완료된 중복 handoff가 더 이상 실행할 active control은 아니더라도, 다음 제어를 써야 하는 verify-followup 상태라는 신호는 runtime health에 남아야 합니다.

## 핵심 변경

- `derive_automation_health()`가 `turn_state.reason=handoff_already_completed` 또는 `duplicate_handoff`인 idle 상태를 `automation_health=attention`, `automation_reason_code=duplicate_handoff`, `automation_next_action=verify_followup`으로 분류하도록 했습니다.
- lane note `waiting_next_control`도 기존 verify-followup reason 계열로 취급하도록 `automation_health.py`의 lane-note 판단을 확장했습니다.
- `autonomy.mode=hibernate`이더라도 reason이 `waiting_next_control` 같은 verify-followup 계열이면 plain `ok/continue`로 떨어지지 않게 했습니다.
- duplicate handoff idle 상태에 대한 `derive_automation_health()` 단위 회귀를 추가했습니다.
- 기존 duplicate handoff supervisor 회귀 테스트에 `automation_health`, `automation_reason_code`, `automation_next_action` 기대값을 추가했습니다.
- security-gate 메모: 이번 변경은 read-only status JSON 판단과 event health surface에 한정되며, 파일 쓰기/승인/외부 네트워크/게시/merge 권한을 새로 열지 않습니다. 기존 local log/event 기록 경계는 유지되고, 롤백은 `automation_health.py` 분기와 테스트 기대값 제거로 가능합니다.

## 검증

- FAIL(초기): `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_duplicate_handoff_verify_followup_progress tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_from_canonical_blocked_triage_event`
  - supervisor duplicate handoff status가 먼저 `waiting_next_control`로 분류되어 기대값과 달랐고, duplicate handoff idle 분기를 `STOPPED`/`STOPPING`/`BROKEN` 제외 조건으로 우선 적용하도록 조정한 뒤 재실행했습니다.
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_duplicate_handoff_verify_followup_progress tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_from_canonical_blocked_triage_event`
- PASS: `python3 -m py_compile pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
- PASS: `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py .pipeline/implement_handoff.md`
- PASS: `git diff --check -- pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py .pipeline/implement_handoff.md work/5/12/2026-05-12-pipeline-launcher-idle-next-control-health.md`

## 남은 리스크

- browser/E2E는 실행하지 않았습니다. 이번 변경은 런처 health 파생 로직과 supervisor status 단위 회귀에 한정했습니다.
- 작업 시작 전부터 worktree에 여러 미커밋 변경이 있었고, `tests/test_pipeline_runtime_supervisor.py`에도 직전 duplicate handoff idle surface 변경이 이미 섞여 있었습니다. 이번 라운드는 그 파일의 health 기대값 보강에 한정했습니다.
