# 2026-04-15 Pipeline Runtime adoption gate 상태

## 판단
- 현재 상태: `구조 전환과 단기 게이트는 닫힘 / 최신 코드 기준 6h·24h synthetic soak와 최종 sign-off는 미종결`

## 근거
- `supervisor`가 run-scoped `status.json`, `events.jsonl`, `receipts/`의 단일 writer로 동작합니다.
- `pipeline-launcher.py`는 local thin client로 유지되며, start/stop/restart/attach는 `pipeline_runtime.cli` 경로만 사용합니다.
- launcher pending/start failure/attach 문구와 readiness 판정에서 `tmux/watcher` 직접 기준을 제거하고 runtime/lane readiness 기준으로 정리했습니다.
- `pipeline_gui` active path는 runtime status/event만 사용하고, legacy observer는 `legacy_backend_debug.py`, `legacy_agent_observers.py` compat/debug surface로만 격리되어 있습니다.
- 브라우저 controller UI는 `/api/runtime/status`, `/api/runtime/start|stop|restart`만 사용하고 `/api/state`는 compat alias로만 남아 있습니다.
- `pipeline_gui.backend.confirm_pipeline_start()`는 watcher alive 우회 없이 `runtime_state + ready lane`만으로 시작 확인을 수행합니다.
- `pipeline_runtime/supervisor.py`는 session loss 시 lane health가 이미 `OFF`로 떨어져도 `session_missing`을 표면화하도록 보정되었습니다.
- `scripts/pipeline_runtime_gate.py fault-check`는 synthetic workspace에서 `RUNNING + ready lane` 이후 fault를 주입하고, wrapper pid 기준 lane recovery를 검증하도록 안정화되었습니다.
- 최신 코드 기준 short synthetic smoke와 synthetic fault-check가 모두 통과했습니다.

| 조건 | 상태 | 근거 |
| --- | --- | --- |
| launcher thin client | 충족 | `pipeline-launcher.py`, `tests/test_pipeline_launcher.py`, `report/pipeline_runtime/verification/2026-04-15-launcher-thin-client-direct-cli.md` |
| controller/browser runtime API 경계 | 충족 | `controller/server.py`, `controller/index.html`, `tests/test_controller_server.py` |
| supervisor single-writer / receipt / wrapper 계약 | 충족 | `pipeline_runtime/supervisor.py`, `pipeline_runtime/cli.py`, `pipeline_runtime/wrapper_events.py`, `tests/test_pipeline_runtime_supervisor.py` |
| legacy compat/debug surface 정리 | 부분충족 | `pipeline_gui/backend.py`, `pipeline_gui/agents.py`, `pipeline_gui/legacy_*`, `report/pipeline_runtime/verification/2026-04-15-legacy-debug-helper-isolation.md` |
| short synthetic soak | 충족 | `report/pipeline_runtime/verification/2026-04-15-synthetic-soak-short.md` |
| synthetic fault-check | 충족 | `report/pipeline_runtime/verification/2026-04-15-fault-check.md` |
| 최신 6h synthetic soak | 미충족 | 최신 rerun 증빙 부재 |
| 최신 24h synthetic soak | 미충족 | `report/pipeline_runtime/verification/2026-04-12-24h-synthetic-soak.md` receipt 조건 실패 |
| final cutover sign-off | 미충족 | 본 문서 기준 rerun/sign-off 필요 상태 유지 |

## 최신 통과 근거
- short synthetic smoke:
  - `report/pipeline_runtime/verification/2026-04-15-synthetic-soak-short.md`
- synthetic fault check:
  - `report/pipeline_runtime/verification/2026-04-15-fault-check.md`
- 경계/회귀 테스트:
  - launcher/supervisor/controller/backend/home-controller/home-presenter/app/agents/runtime-gate 관련 단위·회귀 테스트 통과

## 아직 남은 gate
- 최신 코드 기준 synthetic 6시간 mini soak 1회
- 최신 코드 기준 synthetic 24시간 soak 1회
- 위 두 결과를 반영한 최종 채택 문구 갱신

## rollback 기준
- false READY
- duplicate dispatch
- missing receipt
- control mismatch
- false CLOSED
- silent close

## 메모
- shipped browser release gate는 여전히 `app.web` 기준입니다.
- 이번 문서는 internal/operator tooling 채택 상태만 기록합니다.
- `pipeline-launcher` 자체는 문서가 요구한 thin client 방향에 대체로 부합합니다.
- 다만 `docs/projectH_pipeline_runtime_docs` 전체 완료 조건 기준으로는 아직 채택 완료가 아닙니다.
- 현재 가장 큰 미종결 항목은 최신 코드 기준 `6h`/`24h` synthetic soak와 최종 cutover sign-off입니다.
