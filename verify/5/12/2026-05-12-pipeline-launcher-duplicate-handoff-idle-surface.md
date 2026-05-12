STATUS: verified

# 2026-05-12 Pipeline launcher duplicate handoff idle surface 검증

## 대상

- `work/5/12/2026-05-12-pipeline-launcher-duplicate-handoff-idle-surface.md`

## 변경 파일

- 없음

## 결론

- 통과입니다. duplicate handoff 완료 truth가 있는 상태에서 supervisor public status가 stale `VERIFY_FOLLOWUP` progress를 유지하지 않고 `IDLE`로 내려가는 것을 단위 테스트와 live runtime 재시작 후 status로 확인했습니다.

## 확인한 사실

- duplicate handoff marker는 기존처럼 `handoff_already_completed`를 유지합니다.
- public `control`은 `active_control_status=none`으로 유지됩니다.
- public `turn_state`와 `compat.turn_state`는 `IDLE`로 표면화됩니다.
- `progress`는 빈 객체가 되어 Codex lane에 `next_control_pending` progress가 붙지 않습니다.
- raw compatibility control slot에는 기존 `implement_handoff.md`가 남지만, 이는 raw slot 표시이며 active public control로 취급되지 않습니다.

## 실행한 검증

- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_duplicate_handoff_verify_followup_progress tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_from_canonical_blocked_triage_event`
- PASS: `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- PASS: `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- PASS: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest` (154 tests)
- PASS: `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`
- PASS: `python3 -m pipeline_runtime.cli status --json /home/xpdlqj/code/projectH`

## 실행하지 않은 검증

- browser/E2E
- 장시간 live soak

## 남은 리스크

- 다음 작업을 자동으로 이어가려면 새 `.pipeline/implement_handoff.md` 또는 다른 canonical control slot이 작성되어야 합니다.
- 이번 검증은 런처/supervisor 상태 표면화에 한정되며, 브라우저 controller 화면은 status JSON 계약을 통해 간접 확인했습니다.
