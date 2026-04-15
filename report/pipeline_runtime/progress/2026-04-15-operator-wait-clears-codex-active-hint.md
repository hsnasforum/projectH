## 변경 파일
- pipeline_runtime/supervisor.py
- tests/test_pipeline_runtime_supervisor.py

## 사용 skill
- 없음

## 변경 이유
- Codex가 `/verify`와 `.pipeline/operator_request.md` 작성을 마치고 프롬프트로 돌아온 뒤에도 controller/launcher에 `WORKING`으로 남는 케이스가 있었습니다.
- 원인은 `turn_state=OPERATOR_WAIT`, `control=needs_operator`인데도 supervisor가 `active_round=VERIFYING` fallback으로 Codex를 계속 active lane으로 취급해 task hint를 유지한 데 있었습니다.

## 핵심 변경
- `RuntimeSupervisor._active_lane_for_runtime()`에서 `OPERATOR_WAIT`는 verify fallback보다 우선해 active lane을 비우도록 조정했습니다.
- 그 결과 operator stop이 열린 순간 `task-hints/codex.json`이 inactive로 내려가고, 다음 wrapper heartbeat에서 `TASK_DONE/READY` 정리가 가능해집니다.
- 회귀 테스트를 추가해:
  - `OPERATOR_WAIT`에서는 verify fallback이 Codex active lane으로 이어지지 않음
  - `needs_operator` 상태에서 `status` 작성 시 Codex task hint가 inactive로 기록됨
  을 고정했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --session aip-projectH --no-attach`
- live 확인:
  - run `20260415T102350Z-p2872254`
  - control: `.pipeline/operator_request.md`, `needs_operator`, `seq 142`
  - Codex lane: `READY`, note `prompt_visible`
  - `task-hints/codex.json`: `active: false`

## 남은 리스크
- watcher job state는 여전히 `VERIFY_RUNNING`으로 남아 있을 수 있으므로, 이번 수정은 active lane/task-hint/surface truth를 우선 바로잡는 조치입니다.
- 장기적으로는 watcher job close와 operator stop 전이의 의미 관계도 더 명확히 접으면 runtime 상태 해석이 더 단순해질 수 있습니다.
