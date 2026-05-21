# 2026-05-20 stale turn-state control surface guard

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-stale-turn-state-control-surface-guard.md`

## 사용 skill

- `work-log-closeout`: handoff 완료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- operator stop 해제 및 control slot archive 이후 `.pipeline/state/turn_state.json`에 남은 오래된 `OPERATOR_WAIT` mirror가 첫 post-restart status에 `operator_request.md#2031` active control처럼 비칠 수 있었습니다.
- 실제 `.pipeline` control slot이 비어 있으면 상태 표면도 active control 없음으로 보여야 하며, stale turn state만으로 `operator_boundary` progress를 만들면 안 됩니다.

## 핵심 변경

- `_write_status()`가 active control slot이 없을 때 `turn_state.json`의 `active_control_file` / `active_control_seq`를 active control snapshot fallback으로 쓰지 않게 했습니다.
- 실제 control slot이 하나도 없고 `OPERATOR_WAIT` / `NEEDS_OPERATOR` turn state가 사라진 control 파일을 가리키면 status용 turn state를 `IDLE`과 빈 active control로 정규화하는 helper를 추가했습니다.
- 실제 control slot이 존재하는 operator wait 흐름은 기존처럼 유지되도록, control slot이 active 또는 stale로 파싱되는 경우에는 정규화를 적용하지 않았습니다.
- no-control-slot + stale `operator_request.md#2031` mirror 조건을 직접 재현하는 supervisor 회귀 테스트를 추가했습니다.

## 검증

- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_ignores_missing_operator_control_from_stale_turn_state`
  - 결과: PASS. 새 회귀 테스트가 control empty, `compat.control_slots.active is None`, progress empty를 확인했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_codex_task_hint_during_operator_wait`
  - 결과: PASS. 실제 `operator_request.md`가 있는 기존 operator wait 표면은 유지됨을 확인했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.

## 남은 리스크

- handoff 지시에 따라 Playwright, e2e, 전체 unittest, long soak, socket-bound smoke는 실행하지 않았습니다.
- 작업 트리에는 이번 변경 전부터 같은 파일과 다른 파일에 많은 local dirty/untracked 변경이 남아 있습니다. 이번 라운드는 지정된 supervisor status 표면과 회귀 테스트만 좁게 수정했습니다.
