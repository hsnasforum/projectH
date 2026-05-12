# 2026-05-12 Pipeline launcher duplicate handoff idle surface

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/12/2026-05-12-pipeline-launcher-duplicate-handoff-idle-surface.md`
- `verify/5/12/2026-05-12-pipeline-launcher-duplicate-handoff-idle-surface.md`

## 사용 skill

- `security-gate`: runtime control/status surface 변경이 로컬 런처 상태 표시에 한정되고 승인/저장/외부 게시 경계를 넓히지 않는지 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유

- `CONTROL_SEQ: 1619` implement handoff는 이미 `/work`와 `/verify`로 완료 truth가 생겼지만, live status가 `VERIFY_FOLLOWUP` + `progress.phase=next_control_pending`으로 남아 Codex pane이 또 멈춘 것처럼 보였습니다.
- 기존 supervisor는 duplicate handoff를 `control.active_control_status=none`과 lane `waiting_next_control`로는 표면화했지만, `turn_state`와 `progress`를 같은 truth로 정리하지 않았습니다.

## 핵심 변경

- `pipeline_runtime/supervisor.py`에 duplicate control 전용 turn-state 표면화 helper를 추가했습니다.
- duplicate handoff가 감지되면 public `turn_state`와 `compat.turn_state`를 `IDLE`로 내리고, `active_control_file`, `active_control_seq`, `active_role`, `active_lane`을 비웁니다.
- 이때 `progress`는 빈 객체가 되므로 controller/UI가 과거 `VERIFY_FOLLOWUP` 또는 `IMPLEMENT_ACTIVE` 진행 상태를 계속 표시하지 않습니다.
- 기존 duplicate handoff event, task hint `inactive_reason=duplicate_handoff`, raw `compat.control_slots` 표시는 유지했습니다.
- Codex implement + Codex verify 조합에서 stale verify-followup progress가 사라지는 회귀 테스트를 추가했습니다.

## 검증

- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_duplicate_handoff_verify_followup_progress tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_from_canonical_blocked_triage_event`
- PASS: `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- PASS: `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest` (154 tests)
- PASS: `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`
- PASS: `python3 -m pipeline_runtime.cli status --json /home/xpdlqj/code/projectH`
  - run_id `20260512T052650Z-p103233`
  - `runtime_state=RUNNING`
  - `control.active_control_status=none`
  - `turn_state.state=IDLE`
  - `turn_state.reason=handoff_already_completed`
  - `progress={}`
  - Codex lane `READY`, note `waiting_next_control`

## 남은 리스크

- browser/E2E는 실행하지 않았습니다. 이번 변경은 런처 status JSON 표면화와 supervisor 단위 회귀에 한정했습니다.
- `.pipeline/implement_handoff.md` 자체는 compatibility raw slot으로 남아 있습니다. public `control`과 `turn_state`는 완료된 handoff로 정리되지만, 다음 실제 slice는 새 control slot이 작성되어야 진행됩니다.
