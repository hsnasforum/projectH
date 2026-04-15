# 2026-04-15 pipeline_gui runtime state contract

## 요약
- `pipeline_gui` 활성 경로를 `runtime status/event` 기준으로 더 강하게 고정했습니다.
- `HomeController`는 이제 `status.json`에서 `runtime_state`, `degraded_reason`, lane detail block을 직접 접고, `turn_state.json` 직접 fallback 없이 compat mirror만 사용합니다.
- `HomePresenter`와 `PipelineGUI`는 더 이상 `pane 출력` 개념을 중심으로 화면을 만들지 않고, selected lane의 runtime 상태와 전체 runtime state를 기준으로 표시합니다.

## 변경 파일
- `pipeline_gui/home_models.py`
- `pipeline_gui/home_controller.py`
- `pipeline_gui/home_presenter.py`
- `pipeline_gui/app.py`
- `tests/test_pipeline_gui_home_controller.py`
- `tests/test_pipeline_gui_home_presenter.py`

## 핵심 변경
- snapshot contract
  - `HomeSnapshot`에 `runtime_state`, `degraded_reason`, `lane_details`를 추가했습니다.
  - `session_ok`는 이제 `STOPPED`가 아닌 runtime이면 참으로 유지되어, `BROKEN`에서도 GUI가 runtime 존재를 잃어버리지 않게 했습니다.
- controller fold
  - `HomeController.build_snapshot()`는 run-scoped `status.json`의 lane block에서 UI용 `agents`와 `lane_details`를 함께 만듭니다.
  - active path에서 `.pipeline/state/turn_state.json` 직접 읽기를 제거했습니다.
- presenter
  - focused console은 `최근 pane 출력` 대신 selected lane의 runtime detail을 보여줍니다.
  - `runtime_state`, `attachable`, `pid`, `last_heartbeat_at`, `last_wrapper_event`, `degraded_reason`가 있으면 그대로 노출합니다.
- app status strip
  - 상단 상태 바는 `RUNNING/STARTING/DEGRADED/BROKEN/STOPPED`를 서로 다른 표시로 렌더링합니다.
  - poll freshness와 start/restart enable 판단도 `runtime_state` 기준으로 정리했습니다.

## 기대 효과
- `pipeline_gui` 활성 경로가 tmux pane 개념 없이도 runtime truth만으로 상태를 그릴 수 있습니다.
- `BROKEN`이나 `DEGRADED` 같은 상태가 단순 `중지됨`으로 뭉개지지 않고 UI에 그대로 드러납니다.
- compat mirror는 유지하되, active path authority는 run-scoped runtime status/event 쪽으로 더 명확해졌습니다.

## 남은 리스크
- `pipeline_gui/backend.py`와 `pipeline_gui/agents.py` 안에는 여전히 legacy tmux/log helper가 남아 있습니다. 현재 active snapshot 경로에서는 쓰지 않지만, 디버그/compat 정리는 한 번 더 남아 있습니다.
- focused console이 raw pane tail 대신 runtime fold를 보여주므로, pane-level 디버깅이 꼭 필요할 때는 별도 debug surface를 정리해 둘 필요가 있습니다.
