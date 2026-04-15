# 2026-04-11 Pipeline Runtime thin-client 정리 기록

## 변경 파일
- `pipeline-launcher.py`
- `pipeline_gui/home_controller.py`
- `pipeline_gui/app.py`
- `pipeline_gui/backend.py`
- `pipeline_runtime/tmux_adapter.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_pipeline_gui_home_controller.py`
- `tests/test_pipeline_gui_agents.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- `doc-sync`
- `security-gate`
- `release-check`

## 변경 이유
- launcher / GUI의 남아 있던 compatibility 관측 경로를 더 줄여서, 실제 active path가 runtime status와 run events만 보도록 코드와 문서를 맞추기 위해서입니다.

## 핵심 변경
- `pipeline-launcher.py`에서 직접 `tmux has-session`, watcher pid, watcher log, latest `/work`·`/verify` 스캔을 current truth로 쓰던 경로를 제거하고 runtime status/event 기반 snapshot만 남겼습니다.
- launcher attach는 direct `tmux attach` 대신 runtime adapter 경유 attach로 바꿨습니다.
- `pipeline_gui/home_controller.py`에서 dead compatibility layer였던 pane capture/status 추론 캐시와 latest-md 캐시를 제거하고 runtime status reader만 남겼습니다.
- `pipeline_gui/app.py`에서도 사용되지 않던 legacy wrapper 메서드를 정리해 active path가 `build_snapshot()` 중심으로만 흐르도록 줄였습니다.
- `RuntimeSupervisor`는 session loss를 `session_missing` degraded reason으로 surface하고, manifest mismatch 시 receipt를 쓰지 않고 degraded로 남도록 테스트를 보강했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/wrapper_events.py pipeline_runtime/tmux_adapter.py pipeline_runtime/supervisor.py pipeline_runtime/cli.py pipeline_gui/backend.py pipeline_gui/home_controller.py pipeline_gui/app.py controller/server.py pipeline-launcher.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_controller_server tests.test_pipeline_launcher tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_agents tests.test_pipeline_gui_backend tests.test_pipeline_gui_home_presenter`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_controller_server tests.test_pipeline_launcher tests.test_pipeline_gui_backend tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_agents tests.test_pipeline_gui_app tests.test_watcher_core.TransitionTurnTest`

## 남은 리스크
- live fault injection은 unit 수준 계약으로 일부 자동화했지만, 실제 CLI/tmux lane이 붙은 장시간 운영 검증은 아직 별도 실행이 필요합니다.
- 6시간 mini soak, 24시간 soak는 이번 라운드에서 실행하지 않았습니다.
- `pipeline_gui/agents.py`와 `pipeline_gui/backend.py` 안의 일부 legacy helper는 compat 용도로 남아 있지만 active status path에서는 더 이상 authority로 쓰지 않습니다.
