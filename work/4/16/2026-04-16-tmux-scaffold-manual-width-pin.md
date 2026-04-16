# 2026-04-16 tmux scaffold manual width pin

## 변경 파일
- `pipeline_runtime/tmux_adapter.py`
- `tests/test_tmux_adapter.py`
- `work/4/16/2026-04-16-tmux-scaffold-manual-width-pin.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드(`work/4/16/2026-04-16-controller-log-modal-pane-width-fix.md`)에서 detached tmux session의 기본 크기를 240x72로 넓혔지만, 잔여 리스크로 "나중에 좁은 터미널 client가 attach하면 tmux가 다시 좁은 폭으로 재배치될 수 있다"는 점이 남아 있었습니다.
- tmux는 기본적으로 `window-size smallest` 모드이므로, 어떤 client가 attach하든 가장 작은 client의 크기에 맞춰 window가 줄어듭니다.
- 이번 슬라이스는 scaffold 생성 시 `window-size manual`을 설정하여 `-x/-y`로 명시한 baseline 크기가 client attach에 의해 줄어들지 않도록 고정합니다.

## 핵심 변경
- `pipeline_runtime/tmux_adapter.py`
  - `create_scaffold()`의 session options에 `["tmux", "set-option", "-t", self.session_name, "window-size", "manual"]`을 추가했습니다.
  - 이 옵션은 tmux가 attached client 크기에 따라 window를 자동 축소하지 않도록 합니다. 기존 `-x 240 -y 72` 인자와 결합하여 scaffold가 항상 의도한 baseline 폭을 유지합니다.
- `tests/test_tmux_adapter.py`
  - `test_create_scaffold_sets_window_size_manual`: scaffold 생성 과정에서 `window-size manual` set-option 호출이 정확히 한 번 발생하는지 검증하는 회귀 테스트를 추가했습니다.

## 검증
- `python3 -m unittest -v tests.test_tmux_adapter`
  - 결과: `Ran 2 tests in 0.001s`, `OK`
- `python3 -m py_compile pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py`
  - 결과: 출력 없음 (성공)
- `git diff --check -- pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `tmux list-panes -t aip-projectH:0 -F '#{pane_index} #{pane_width} #{pane_height} #{pane_id}'`
  - 결과: `0 79 72 %278`, `1 79 72 %279`, `2 80 72 %280`
  - 현재 live session의 pane 폭은 이전 라운드에서 설정한 240-col baseline을 유지하고 있습니다.
  - 다만 `window-size manual` 옵션은 코드에만 추가했으며 현재 live session에 적용하지는 않았습니다 (이번 변경은 다음 scaffold 생성 시점부터 적용됩니다).

## 남은 리스크
- `window-size manual`은 다음 `create_scaffold()` 호출, 즉 다음 session 생성 시점부터 적용됩니다. 현재 live session `aip-projectH`에는 수동으로 `tmux set-option -t aip-projectH window-size manual`을 실행해야 즉시 반영됩니다.
- `window-size manual` 모드에서는 attach한 client의 terminal이 window보다 좁더라도 tmux가 window를 줄이지 않으므로, 좁은 terminal에서는 오른쪽이 잘려 보일 수 있습니다. 이는 의도된 동작이며 scaffold의 capture-pane 로그 품질을 우선합니다.
