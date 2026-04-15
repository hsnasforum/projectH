# 2026-04-15 legacy debug helper isolation verification

## 검증 범위
- `pipeline_gui/backend.py`
- `pipeline_gui/agents.py`
- `pipeline_gui/legacy_backend_debug.py`
- `pipeline_gui/legacy_agent_observers.py`
- `tests/test_pipeline_gui_backend.py`
- `tests/test_pipeline_gui_agents.py`
- `tests/test_token_backend.py`
- `tests/test_controller_server.py`
- `tests/test_pipeline_gui_home_controller.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `tests/test_pipeline_gui_app.py`

## 실행한 검증
- `python3 -m py_compile pipeline_gui/backend.py pipeline_gui/agents.py pipeline_gui/legacy_backend_debug.py pipeline_gui/legacy_agent_observers.py tests/test_pipeline_gui_backend.py tests/test_pipeline_gui_agents.py tests/test_token_backend.py tests/test_controller_server.py`
- `python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_pipeline_gui_agents tests.test_token_backend tests.test_controller_server`
- `python3 -m unittest -v tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_app`

## 결과
- `py_compile` 통과
- `tests.test_pipeline_gui_backend` + `tests.test_pipeline_gui_agents` + `tests.test_token_backend` + `tests.test_controller_server` 69건 통과
- `tests.test_pipeline_gui_home_controller` + `tests.test_pipeline_gui_home_presenter` + `tests.test_pipeline_gui_app` 65건 통과

## 확인한 포인트
- legacy helper 분리 후에도 기존 compat API 이름으로 테스트와 controller debug surface가 계속 동작하는지
- token collector가 `tmux_alive` compat seam을 계속 사용할 수 있는지
- `pipeline_gui` active snapshot/presenter/app 경로가 새 legacy 모듈 분리 이후에도 깨지지 않는지

## 메모
- 이번 라운드는 active path에서 legacy helper를 제거한 뒤, 그 남은 compat/debug 구현을 별도 모듈로 분리하는 데 집중했습니다.
- 문서형 제품 계약 변화는 없어서 root product docs는 건드리지 않았습니다.
