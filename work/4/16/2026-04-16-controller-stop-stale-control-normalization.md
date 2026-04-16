# 2026-04-16 controller stop stale control normalization

## 변경 파일
- `pipeline_gui/backend.py`
- `controller/index.html`
- `tests/test_pipeline_gui_backend.py`
- `tests/test_controller_server.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-stop-stale-control-normalization.md`

## 사용 skill
- `work-log-closeout`: 이번 stop 상태 정규화 수정과 실제 검증 결과를 `/work` 형식으로 정리했습니다.

## 변경 이유
- controller에서 stop 이후 lane/watcher는 이미 죽어 있는데 `control=implement`만 초록으로 남아, runtime이 아직 active인 것처럼 보였습니다.
- 실제 원인은 오래된 `STOPPING` 또는 stale `BROKEN(supervisor_missing)` status가 live `control`과 `active_round`를 그대로 보존한 채 browser로 전달되는 데 있었습니다.

## 핵심 변경
- `pipeline_gui/backend.py`
  - stale runtime 정규화 시 live 필드(`control`, `active_round`)를 비우는 공용 정리 경로를 추가했습니다.
  - `STOPPING` 상태인데 supervisor PID가 이미 없으면 stale timeout을 기다리지 않고 `STOPPED`로 정규화하도록 바꿨습니다.
  - stale `BROKEN` 정규화에서도 `control=none`, `active_round=null`, lane `pid/attachable` 정리를 함께 수행하도록 보강했습니다.
- `controller/index.html`
  - `STOPPED`, `STOPPING`, `BROKEN`에서는 runtime info 패널이 `Control`과 `Round`를 active처럼 초록 강조하지 않도록 `runtimeAllowsActiveStatus()` 가드를 추가했습니다.
- `tests/test_pipeline_gui_backend.py`
  - stale `RUNNING -> BROKEN` 케이스에 `control` / `active_round` 정리 검증을 추가했습니다.
  - `STOPPING + supervisor 없음 -> STOPPED` 정규화 회귀 테스트를 새로 추가했습니다.
- `tests/test_controller_server.py`
  - controller HTML 정적 계약 테스트에 inactive runtime 가드 문자열이 들어 있는지 확인하는 검증을 추가했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 오래된 `STOPPING` run을 reader가 다시 만났을 때 `STOPPED + control=none + Round=IDLE`로 정규화하는 운영 truth를 문서에 맞췄습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_gui_backend`
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
- `python3 -m py_compile pipeline_gui/backend.py controller/server.py tests/test_pipeline_gui_backend.py tests/test_controller_server.py`
- `git diff --check -- pipeline_gui/backend.py controller/index.html tests/test_pipeline_gui_backend.py tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- 수정 전 API 확인:
  - `curl -s http://127.0.0.1:8780/api/runtime/status`
  - 결과 핵심: `runtime_state=BROKEN`, `active_control_status=implement`, `active_round.state=VERIFYING`
- controller 재기동:
  - `kill 3392721`
  - `setsid env CONTROLLER_HOST=127.0.0.1 python3 -m controller.server </dev/null >/tmp/projecth-controller.log 2>&1 &`
- 수정 후 API 확인:
  - `ss -ltnp | rg ':8780 '`
  - `curl -s http://127.0.0.1:8780/api/runtime/status`
  - 결과 핵심: `runtime_state=STOPPED`, `active_control_status=none`, `active_round=null`, lane state=`OFF`

## 남은 리스크
- 현재 fix는 stale `STOPPING`을 reader에서 `STOPPED`로 정규화하는 방식이라, supervisor가 final `STOPPED` status를 직접 flush하지 못하는 근본 stop 경로는 별도 점검 대상입니다.
- `compat.control_slots.active`에는 canonical control 파일 정보가 debug surface로 남아 있으므로, 이후 UI가 compat surface를 직접 참조하면 같은 혼동이 다시 생길 수 있습니다.
