## 요약
- Claude lane이 실제로는 이전 라운드를 끝내고 prompt/feedback 대기 상태였는데, supervisor 종료 후 stale `status.json`이 계속 읽히면서 `READY/WORKING` 표면이 truth처럼 남는 문제가 있었습니다.
- 이번 라운드에서는 runtime read path에 stale supervisor guard를 추가해, supervisor pid가 사라지고 `updated_at`이 일정 시간 이상 멈춘 상태를 `BROKEN(supervisor_missing)`으로 강등하도록 보강했습니다.

## 변경 파일
- `pipeline_gui/backend.py`
- `tests/test_pipeline_gui_backend.py`

## 원인
- lane wrapper와 tmux pane은 살아 있어도 supervisor 단일 writer가 종료되면 `status.json` 갱신이 멈춥니다.
- 기존 `read_runtime_status()`는 run-scoped `status.json`을 그대로 반환해서, 오래된 `READY` 상태가 controller/launcher에 그대로 노출되었습니다.

## 핵심 변경
- `read_runtime_status()`에 stale runtime guard 추가
  - `updated_at`이 15초 이상 멈춤
  - `runtime_state`가 아직 `STOPPED/BROKEN`이 아님
  - `.pipeline/supervisor.pid` 기준 live supervisor가 없음
- 위 조건이면 read-model에서 `runtime_state=BROKEN`, `degraded_reason=supervisor_missing`으로 정규화
- lane 표면도 `BROKEN/supervisor_missing`으로 내려 false `READY/WORKING` 노출을 막음
- recent status는 그대로 유지하도록 회귀 테스트 추가

## 검증
- `python3 -m py_compile pipeline_gui/backend.py pipeline-launcher.py controller/server.py tests/test_pipeline_gui_backend.py`
- `python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_controller_server tests.test_pipeline_launcher`
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`

## 메모
- 이번 수정은 read-model guard입니다. 근본 원인인 supervisor 조기 종료 자체는 별도 추적이 여전히 필요합니다.
- 다만 이번 보강으로 supervisor가 죽은 뒤에도 controller/launcher가 stale `READY`를 계속 보여주는 문제는 막습니다.
