# 2026-04-15 runtime boundary and gate hardening verification

## 검증 범위
- `pipeline-launcher.py`
- `pipeline_gui/backend.py`
- `pipeline_runtime/supervisor.py`
- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_pipeline_gui_backend.py`
- `tests/test_controller_server.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_gate.py`
- `tests/test_pipeline_gui_home_controller.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `tests/test_pipeline_gui_app.py`
- `tests/test_pipeline_gui_agents.py`

## 실행한 검증
- `python3 -m py_compile pipeline-launcher.py pipeline_gui/backend.py tests/test_pipeline_launcher.py tests/test_pipeline_gui_backend.py tests/test_controller_server.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_gui_home_controller.py`
- `python3 -m unittest -v tests.test_pipeline_launcher tests.test_pipeline_runtime_supervisor tests.test_controller_server tests.test_pipeline_gui_backend tests.test_pipeline_gui_home_controller`
- `python3 -m unittest -v tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_app tests.test_pipeline_gui_agents tests.test_pipeline_runtime_gate`
- `python3 -m py_compile pipeline_runtime/supervisor.py scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_gate.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_gate`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental synthetic-soak --duration-sec 30 --sample-interval-sec 1 --min-receipts 1 --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-15-synthetic-soak-short.md`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental fault-check --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-15-fault-check.md`

## 결과
- `py_compile` 통과
- launcher/supervisor/controller/backend/home-controller 회귀 73건 통과
- presenter/app/agents/runtime-gate 회귀 78건 통과
- supervisor/runtime-gate 재검증 24건 통과
- short synthetic soak 통과
  - `receipt_count=1`
  - `duplicate_dispatch_count=0`
  - `control_mismatch_max_streak=0`
  - `orphan_session=False`
- synthetic fault-check 통과
  - `status surface ready` = `RUNNING`
  - `session loss degraded` 확인
  - `lane recovery` = `recovery_completed` 이벤트 확인

## 확인한 포인트
- launcher에 `tmux/watcher` readiness 표현과 attach naming이 active path에 재유입되지 않는지
- backend/controller가 supervisor runtime status를 watcher alive heuristic 없이 신뢰하는지
- `current_run.json`, run-scoped `status.json`, `events.jsonl`, `receipts/` 계약이 유지되는지
- `VERIFY_DONE`와 receipt 경계가 `RECEIPT_PENDING` / `CLOSED`로 분리되는지
- `fault-check`와 short synthetic soak가 최신 코드 기준으로 다시 녹색인지

## 메모
- 이번 검증 라운드는 문서 완료 조건 중 “코드 정리 + 단기 게이트”를 닫는 데 초점을 맞췄습니다.
- 최종 채택 선언에는 최신 코드 기준 6시간 / 24시간 synthetic soak 결과가 추가로 필요합니다.
