# 2026-04-16 controller log modal pane width fix

## 변경 파일
- `pipeline_runtime/tmux_adapter.py`
- `controller/index.html`
- `tests/test_tmux_adapter.py`
- `tests/test_controller_server.py`
- `work/4/16/2026-04-16-controller-log-modal-pane-width-fix.md`

## 사용 skill
- 없음

## 변경 이유
- `controller/index.html`의 terminal log modal은 충분히 넓었지만, 실제 로그가 modal 안에서 좁게 꺾여 보였습니다.
- 확인 결과 원인은 modal 자체보다 detached `tmux` scaffold 기본 폭이 좁은 데 있었습니다. 현재 세션 `aip-projectH:0`의 pane 폭이 실제로 `26 26 24` 수준이었고, 이 상태에서 `capture-pane`으로 가져온 텍스트가 이미 좁은 열 기준으로 줄바꿈되어 modal 오른쪽 공간이 비어 보였습니다.

## 핵심 변경
- `pipeline_runtime/tmux_adapter.py`
  - detached session 생성 시 기본 크기를 명시하도록 `DEFAULT_SESSION_COLS = 240`, `DEFAULT_SESSION_ROWS = 72`를 추가했습니다.
  - `tmux new-session -d` 호출에 `-x/-y`를 넣어 3-lane 분할 후에도 각 pane이 약 80열을 확보하도록 했습니다.
- `controller/index.html`
  - log modal 폭을 `min(1100px, 96vw)`로 늘렸습니다.
  - log body에 `width: 100%; min-width: 0;`를 넣어 modal 내부 폭을 끝까지 쓰도록 했습니다.
- `tests/test_tmux_adapter.py`
  - scaffold 생성 시 detached tmux session이 explicit `-x/-y` 크기를 사용하는지 검증하는 회귀 테스트를 추가했습니다.
- `tests/test_controller_server.py`
  - controller HTML 정적 계약 테스트를 현재 canvas-office + log-modal 구조에 맞게 갱신했습니다.
- 현재 살아 있던 tmux 세션에도 즉시 적용되도록 아래 명령으로 런타임 pane 폭을 재조정했습니다.
  - `tmux resize-window -t aip-projectH:0 -x 240 -y 72`
  - `tmux select-layout -t aip-projectH:0 even-horizontal`

## 검증
- 기존 pane 폭 확인:
  - `tmux list-panes -t aip-projectH:0 -F '#{pane_index} #{pane_width} #{pane_height} #{pane_id}'`
  - 결과: `0 26 24`, `1 26 24`, `2 26 24`
- 코드 검증:
  - `python3 -m unittest -v tests.test_tmux_adapter`
  - `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - `python3 -m py_compile pipeline_runtime/tmux_adapter.py controller/server.py tests/test_tmux_adapter.py tests/test_controller_server.py`
  - `git diff --check -- pipeline_runtime/tmux_adapter.py controller/index.html tests/test_tmux_adapter.py tests/test_controller_server.py`
- 즉시 반영 확인:
  - `tmux resize-window -t aip-projectH:0 -x 240 -y 72 && tmux select-layout -t aip-projectH:0 even-horizontal && tmux list-panes -t aip-projectH:0 -F '#{pane_index} #{pane_width} #{pane_height} #{pane_id}'`
  - 결과: `0 79 72`, `1 79 72`, `2 80 72`

## 남은 리스크
- 현재 수정은 detached runtime 기본 폭을 넓히는 방식이라, 나중에 아주 작은 터미널 client가 attach되면 tmux가 다시 더 좁은 폭으로 재배치될 수 있습니다.
- log modal은 더 넓어졌지만, 이미 좁은 client에서 출력된 과거 기록은 자동으로 재flow되지 않으므로 해당 시점의 로그는 여전히 좁게 보일 수 있습니다.
