# 2026-04-16 controller stale runtime status badge fix

## 변경 파일
- `controller/index.html`
- `pipeline_gui/backend.py`
- `tests/test_controller_server.py`
- `tests/test_pipeline_gui_backend.py`
- `work/4/16/2026-04-16-controller-stale-runtime-status-badge-fix.md`

## 사용 skill
- 없음

## 변경 이유
- runtime 프로세스는 이미 종료됐는데 controller UI가 stale status를 `Running`으로 계속 표시하고, stale payload 안의 `watcher.alive`도 그대로 보여 주는 문제가 있었습니다.
- 원인은 두 가지였습니다.
  - `controller/index.html` toolbar가 `runtime_state != STOPPED`면 모두 초록 `Running`으로 표시
  - `pipeline_gui.backend.read_runtime_status()`의 stale 보정이 lane은 `BROKEN`으로 바꾸면서 watcher는 dead로 내리지 않음

## 핵심 변경
- `pipeline_gui/backend.py`
  - `_mark_runtime_status_stale()`에서 stale runtime을 `BROKEN/supervisor_missing`으로 보정할 때 `watcher.alive = false`, `watcher.pid = null`도 함께 강제하도록 수정했습니다.
- `controller/index.html`
  - toolbar 상태 표시를 `RUNNING / STARTING / STOPPING / DEGRADED / BROKEN / STOPPED`로 분리했습니다.
  - `BROKEN`과 `STOPPED`에서는 tail cache를 비우도록 정리했습니다.
- `tests/test_pipeline_gui_backend.py`
  - stale runtime 보정 테스트에 watcher dead/null 보정을 추가 검증했습니다.
- `tests/test_controller_server.py`
  - controller HTML이 더 이상 `runtime_state != STOPPED` 식 단순 분기를 쓰지 않고, `Broken` / `Stopping` 상태 텍스트를 포함하는지 확인하도록 보강했습니다.
- controller server는 수정 반영을 위해 sandbox 밖에서 `CONTROLLER_HOST=127.0.0.1 python3 -m controller.server`로 재기동했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_gui_backend`
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
- `python3 -m py_compile pipeline_gui/backend.py controller/server.py`
- `python3 -c 'from pathlib import Path; from pipeline_gui.backend import read_runtime_status; import json; print(json.dumps(read_runtime_status(Path("/home/xpdlqj/code/projectH")), ensure_ascii=False, indent=2))'`
- `git diff --check -- controller/index.html pipeline_gui/backend.py tests/test_controller_server.py tests/test_pipeline_gui_backend.py`
- sandbox 밖 controller 재기동:
  - `CONTROLLER_HOST=127.0.0.1 nohup python3 -m controller.server > /tmp/projecth-controller.log 2>&1 &`
  - `ss -ltnp | rg ':8780 '`

## 남은 리스크
- stale run pointer(`.pipeline/current_run.json`)와 old run `status.json` 자체는 그대로 남아 있으므로, controller는 이제 truthful하게 `BROKEN / watcher dead`로 보여 주지만 active control / latest artifact 문자열은 마지막 persisted run 기준으로 계속 보입니다.
- 브라우저에 이전 JS/UI 상태가 남아 있으면 새 controller에 재연결한 뒤에도 한 번 새로고침이 필요할 수 있습니다.
