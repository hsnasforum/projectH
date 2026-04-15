# 2026-04-11 Pipeline Runtime thin-client 검증 기록

## 실행 명령
- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/wrapper_events.py pipeline_runtime/tmux_adapter.py pipeline_runtime/supervisor.py pipeline_runtime/cli.py pipeline_gui/backend.py pipeline_gui/home_controller.py pipeline_gui/app.py controller/server.py pipeline-launcher.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_controller_server tests.test_pipeline_launcher tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_agents tests.test_pipeline_gui_backend tests.test_pipeline_gui_home_presenter`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_controller_server tests.test_pipeline_launcher tests.test_pipeline_gui_backend tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_agents tests.test_pipeline_gui_app tests.test_watcher_core.TransitionTurnTest`

## 결과
- 컴파일 체크 통과
- 82개 focused runtime/controller/gui/launcher 테스트 통과
- 134개 확장 회귀 테스트 통과

## fault/recovery 확인 포인트
- wrapper heartbeat timeout -> `BROKEN` lane read-model 전이 확인
- Claude post-accept breakage -> blind replay 금지 확인
- Codex pre-completion breakage -> bounded retry 확인
- retry budget 초과 -> `codex_broken` 전이 확인
- tmux session loss -> `session_missing` degraded 전이 확인
- manifest mismatch -> receipt 미작성 + degraded 유지 확인

## 미실행 항목
- 실제 tmux lane + vendor CLI를 붙인 live fault injection
- 6시간 mini soak
- 24시간 soak

## 현재 판단
- 문서에서 고정한 thin-client / single-writer / wrapper-readiness / receipt-gate 계약은 코드와 자동화 테스트 기준으로 맞춰졌습니다.
- adoption gate를 “완료”로 선언하려면 live soak 결과가 추가로 필요합니다.
