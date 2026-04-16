# 2026-04-16 controller undated ambiguous hardening verification

## 변경 파일
- 없음

## 사용 skill
- 없음

## 변경 이유
- 최신 `/work` 기준으로 undated ambiguous snapshot과 watcher-only half-broken payload가 실제로 uncertain `DEGRADED`로 내려오는지, 그리고 controller HTML contract가 새 uncertain reason set을 포함하는지 재검증하는 라운드입니다.

## 핵심 변경
- backend는 `supervisor_missing_snapshot_undated`를 새 uncertain degraded reason으로 사용하고, watcher `alive=true` / `pid 없음` claim도 ambiguous activity로 다룹니다.
- controller HTML은 uncertain runtime reason set으로 `supervisor_missing_recent_ambiguous`와 `supervisor_missing_snapshot_undated`를 함께 인식합니다.
- 임시 `/tmp` fixture 기반 controller 서버를 실제로 띄워 `/api/runtime/status` HTTP 응답이 `DEGRADED + supervisor_missing_snapshot_undated`를 반환하는 것까지 확인했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_controller_server`
  - 결과: `Ran 60 tests`, `OK`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/server.py tests/test_controller_server.py`
  - 결과: 오류 없음
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/index.html tests/test_controller_server.py README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 출력 없음
- 실제 HTTP smoke
  - `PROJECT_ROOT=/tmp/projecth-controller-fixture-wMOZNM CONTROLLER_HOST=127.0.0.1 CONTROLLER_PORT=8784 python3 -m controller.server`
  - `curl -fsS http://127.0.0.1:8784/api/runtime/status`
  - 결과: `runtime_state=DEGRADED`, `degraded_reason=supervisor_missing_snapshot_undated`, `control.active_control_status=implement`, `watcher.alive=true`, `watcher.pid=null`
  - `curl -fsS http://127.0.0.1:8784/controller | rg -n "supervisor_missing_snapshot_undated|UNCERTAIN_RUNTIME_REASONS|getRuntimePresentation|log-modal-info"`
  - 결과: uncertain runtime helper와 modal wrap contract 문자열 확인
- browser DOM smoke 시도
  - `npx playwright test ...`
  - 결과: local `playwright` package import 실패로 미완료. 검증 성공으로 계산하지 않음

## 남은 리스크
- 실제 browser DOM assertion은 아직 정식으로 통과시키지 못했습니다.
- 더 심하게 손상된 snapshot family는 계속 follow-up hardening 후보로 남습니다.
