# 2026-04-15 legacy debug helper isolation

## 요약
- `pipeline_gui/backend.py`, `pipeline_gui/agents.py`에 남아 있던 legacy `tmux/log/pane` 관측 구현을 별도 `legacy_*` 모듈로 격리했습니다.
- 기존 import surface는 유지하면서, active/runtime 중심 파일에는 compat wrapper만 남기도록 정리했습니다.
- `pipeline_gui`의 실제 활성 경로는 계속 runtime status/event만 사용하고, legacy helper는 debug/compat surface로만 남습니다.

## 변경 파일
- `pipeline_gui/backend.py`
- `pipeline_gui/agents.py`
- `pipeline_gui/legacy_backend_debug.py`
- `pipeline_gui/legacy_agent_observers.py`

## 핵심 변경
- `pipeline_gui/backend.py`
  - `tmux_alive`, `watcher_alive`, `latest_md`, `watcher_log_snapshot`, `watcher_start_observed` 구현을 `legacy_backend_debug.py`로 이동했습니다.
  - `backend.py`에는 기존 함수명 그대로 얇은 compat wrapper만 남겼습니다.
  - wrapper는 `IS_WINDOWS`, `_run`, `_wsl_path_str`, `_read_log_lines` 같은 기존 dependency seam을 그대로 전달하므로 test patch point를 깨지 않았습니다.
- `pipeline_gui/agents.py`
  - `detect_agent_status`, `capture_agent_panes`, `rejoin_wrapped_pane_lines`, `format_focus_output`, `watcher_runtime_hints*` 구현을 `legacy_agent_observers.py`로 이동했습니다.
  - `agents.py`는 active UI가 실제로 쓰는 `STATUS_COLORS`, `_parse_elapsed`, `format_elapsed`와 compat wrapper 중심 파일로 정리했습니다.
- active path 확인
  - `pipeline_gui/home_controller.py`, `pipeline_gui/home_presenter.py`, `pipeline_gui/app.py`는 여전히 legacy helper를 직접 부르지 않습니다.
  - legacy helper는 controller debug tail, token maintenance tmux collector, 기존 단위 테스트 같은 compat/debug 표면만 담당합니다.

## 기대 효과
- `backend.py`, `agents.py`가 runtime active path 파일인지 legacy observer 파일인지 경계가 더 명확해졌습니다.
- 이후 legacy surface를 더 줄이거나 삭제할 때 수정 범위를 `legacy_*` 모듈 쪽으로 한정하기 쉬워졌습니다.
- runtime 상태 소유권과 legacy 관측 로직의 개념적 혼합이 더 줄었습니다.

## 남은 리스크
- compat surface는 아직 public 함수명으로 남아 있어 외부 호출자는 계속 사용할 수 있습니다.
- controller의 `/api/runtime/capture-tail`과 token collector의 tmux session 감지는 여전히 substrate 성격의 debug/ops seam을 유지합니다.
- 완전 삭제 단계로 가려면 어떤 compat/debug API를 유지할지 먼저 고정해야 합니다.
