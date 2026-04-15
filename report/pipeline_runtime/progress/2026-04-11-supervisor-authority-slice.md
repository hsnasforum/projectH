# 2026-04-11 Pipeline Runtime 진행 기록

## 변경 파일
- `pipeline_runtime/__init__.py`
- `pipeline_runtime/schema.py`
- `pipeline_runtime/wrapper_events.py`
- `pipeline_runtime/receipts.py`
- `pipeline_runtime/tmux_adapter.py`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/cli.py`
- `start-pipeline.sh`
- `stop-pipeline.sh`
- `watcher_core.py`
- `controller/server.py`
- `controller/index.html`
- `pipeline_gui/backend.py`
- `pipeline_gui/home_controller.py`
- `pipeline_gui/home_presenter.py`
- `pipeline_gui/app.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_gui_backend.py`
- `tests/test_pipeline_gui_home_controller.py`
- `tests/test_pipeline_gui_home_presenter.py`

## 사용 skill
- `doc-sync`
- `release-check`

## 변경 이유
- launcher/controller/pipeline_gui가 `tmux pane`, `watcher.log`, 최신 `/work`·`/verify` 스캔에 직접 의존하던 상태 판단 경로를 끊고, run-scoped runtime status를 authority로 세우기 위해서입니다.

## 핵심 변경
- `pipeline_runtime` 패키지를 추가해 `supervisor`, `TmuxAdapter`, `receipt`, `wrapper-event`, `cli` 경계를 만들었습니다.
- `start-pipeline.sh`, `stop-pipeline.sh`를 thin wrapper로 바꾸고, supervisor가 legacy start/stop 경로를 env flag로 감싸서 호출하도록 연결했습니다.
- production 경로에서는 watcher exporter를 끌 수 있도록 `watcher_core.py`에 `PIPELINE_RUNTIME_DISABLE_EXPORTER` 지원을 넣었습니다.
- `controller/server.py`는 runtime status만 읽고 `/api/runtime/status`, `/api/runtime/start|stop|restart|attach`를 canonical API로 사용하도록 정리했습니다.
- `controller/index.html`은 pane capture 대신 lane/runtime/control/receipt 중심으로 렌더링하도록 바꿨습니다.
- `pipeline_gui/home_controller.py`는 runtime status와 run events만 읽어 snapshot을 만들게 바꿨고, `pipeline_gui/app.py`의 start/stop/restart/attach 흐름도 runtime 상태를 기준으로 판단하게 바꿨습니다.
- supervisor는 run-scoped `status.json`, `events.jsonl`, `receipts/`, `wrapper-events/`, `compat/`를 쓰고, `VERIFY_DONE` job state를 바탕으로 receipt를 발급합니다.

## 남은 리스크
- lane wrapper는 `READY`/`HEARTBEAT`/`BROKEN` 중심의 1차 구현이며, vendor 출력 기반의 세밀한 `TASK_ACCEPTED`/`TASK_DONE` 계약은 아직 supervisor 보조 이벤트에 일부 의존합니다.
- recovery는 Codex/Gemini bounded restart, Claude post-accept degraded 전이까지 넣었지만, 장시간 soak 전의 수치는 아직 조정되지 않았습니다.
- full end-to-end soak, fault injection, optional PTY pilot은 아직 실행하지 않았습니다.
