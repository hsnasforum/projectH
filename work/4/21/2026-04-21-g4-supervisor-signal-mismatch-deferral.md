## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral.md`

## 사용 skill
- `onboard-lite`: handoff, 관련 `/work`/`/verify`, supervisor/test 진입점을 최소 범위로 확인했습니다.
- `finalize-lite`: 지정된 3개 검증만 다시 실행하고 `/work` closeout 정합성을 확인했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 593은 AXIS-G4 second widening으로, supervisor가 implement-owner lane의 tmux tail `WORKING`만 보고 lane을 `WORKING`으로 승격하지 않도록 좁은 production guard 1개를 요구했습니다.
- 목표는 wrapper 쪽 `DISPATCH_SEEN` / `TASK_ACCEPTED` corroboration이 없는 current control에서 supervisor가 `lane_working`으로 오인 표면화하지 않게 하되, 기존 implement-owner follow-on surface는 깨지지 않게 유지하는 것이었습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py`의 `_build_lane_statuses` target `elif` 블록만 수정해, implement-owner lane에서 `tail_surface == "WORKING"`일 때 current `active_control_seq`가 있으면 `seen_task.control_seq` / `accepted_task.control_seq` 또는 같은 lane의 `*_activity_detected` turn-state reason으로 corroboration을 확인하도록 바꿨습니다.
- current `active_control_seq`가 있고 corroboration이 없으면 `state`를 `WORKING`으로 올리지 않고 `READY`로 되돌리며 `note = "signal_mismatch"`를 남기게 했습니다. current control seq가 없는 기존 implement surface는 유지했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 `test_build_lane_statuses_defers_working_on_signal_mismatch` 1건만 추가해, implement owner를 `Codex`로 바꾼 상태에서 busy tail은 보이지만 wrapper corroboration이 없는 current control에서는 `WORKING` 대신 `READY` + `signal_mismatch`가 반환되는지 고정했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py`
  ```text
  출력 없음 (rc=0)
  ```
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  ```text
  ..........................................................2026-04-21T01:11:38 [INFO] watcher_core: manifest schema loaded: /home/xpdlqj/code/projectH/schemas/agent_manifest.schema.json  jsonschema=True
  .2026-04-21T01:11:38 [INFO] watcher_core: manifest schema loaded: /home/xpdlqj/code/projectH/schemas/agent_manifest.schema.json  jsonschema=True
  .2026-04-21T01:11:38 [INFO] watcher_core: manifest schema loaded: /home/xpdlqj/code/projectH/schemas/agent_manifest.schema.json  jsonschema=True
  ...2026-04-21T01:11:38 [INFO] watcher_core: manifest schema loaded: /home/xpdlqj/code/projectH/schemas/agent_manifest.schema.json  jsonschema=True
  .......................................

  ----------------------------------------------------------------------
  Ran 102 tests in 0.956s

  OK
  ```
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  ```text
  출력 없음 (rc=0)
  ```

## 남은 리스크
- 이번 guard는 `active_control_seq`가 있는 implement-owner `WORKING` tail mismatch만 좁게 막습니다. wrapper가 current control seq를 남기지 않는 더 이른 경로나 watcher emit 경계 문제는 여전히 out of scope입니다.
- production 범위는 supervisor-only라서 `watcher_dispatch.py`, `watcher_core.py`, wrapper emitter 쪽의 corroboration 생성 방식은 이번 라운드에서 바꾸지 않았습니다.
- handoff 지시대로 `tests.test_pipeline_runtime_supervisor`만 rerun했고, 다른 runtime/browser suite는 이번 slice 범위 밖으로 남겼습니다.
