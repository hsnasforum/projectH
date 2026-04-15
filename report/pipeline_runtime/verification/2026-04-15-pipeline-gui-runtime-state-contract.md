# 2026-04-15 pipeline_gui runtime state contract verification

## 검증 범위
- `pipeline_gui/home_models.py`
- `pipeline_gui/home_controller.py`
- `pipeline_gui/home_presenter.py`
- `pipeline_gui/app.py`
- `tests/test_pipeline_gui_home_controller.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `tests/test_pipeline_gui_app.py`

## 실행한 검증
- `python3 -m py_compile pipeline_gui/home_models.py pipeline_gui/home_controller.py pipeline_gui/home_presenter.py pipeline_gui/app.py tests/test_pipeline_gui_home_controller.py tests/test_pipeline_gui_home_presenter.py`
- `python3 -m unittest -v tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_home_presenter`
- `python3 -m unittest -v tests.test_pipeline_gui_app`

## 결과
- `py_compile` 통과
- `tests.test_pipeline_gui_home_controller` + `tests.test_pipeline_gui_home_presenter` 14건 통과
- `tests.test_pipeline_gui_app` 51건 통과

## 확인한 포인트
- `HomeController`가 runtime status/event만으로 snapshot을 구성하는지
- presenter가 raw pane fallback 없이 runtime lane detail을 표시하는지
- GUI app이 `runtime_state` 기준으로 상태 바, poll freshness, start/restart gating을 유지하는지

## 메모
- 이번 라운드는 `pipeline_gui` 활성 경로 정리에 한정했습니다.
- `pipeline_gui/backend.py` legacy helper와 `pipeline_gui/agents.py`의 raw tmux/log parser는 active path 바깥 정리 대상으로 남겨 두었습니다.
