# 2026-04-15 pipeline launcher vs runtime docs conformance audit

## 요약
- `pipeline-launcher` 자체는 문서가 요구한 thin client 방향에 대체로 부합합니다.
- 다만 `docs/projectH_pipeline_runtime_docs` 전체 완료 조건 기준으로는 아직 채택 완료가 아닙니다.
- 현재 가장 큰 미종결 항목은 최신 코드 기준 `6h`/`24h` synthetic soak와 최종 cutover sign-off입니다.

## 판정
- 현재 상태: `구조 전환과 단기 게이트는 닫힘 / 최신 코드 기준 6h·24h synthetic soak와 최종 sign-off는 미종결`

## 점검 표
| 항목 | 판정 | 근거 | 메모 |
| --- | --- | --- | --- |
| launcher thin client | 충족 | `pipeline-launcher.py`, `tests/test_pipeline_launcher.py`, `report/pipeline_runtime/verification/2026-04-15-launcher-thin-client-direct-cli.md` | start/stop/restart/attach는 `pipeline_runtime.cli` 경로만 사용하고 runtime status/event만 읽습니다. |
| controller/browser runtime API 경계 | 충족 | `controller/server.py`, `controller/index.html`, `tests/test_controller_server.py` | 브라우저 UI active path는 `/api/runtime/status`, `/api/runtime/start|stop|restart` 중심입니다. |
| supervisor single-writer | 충족 | `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py`, `report/pipeline_runtime/verification/2026-04-11-supervisor-authority-slice.md` | run-scoped `status.json`, `events.jsonl`, `receipts/`를 supervisor가 작성합니다. |
| run-scoped status/events | 충족 | `pipeline_runtime/supervisor.py`, `pipeline_gui/backend.py`, `report/pipeline_runtime/verification/2026-04-15-runtime-boundary-gate-hardening.md` | `.pipeline/current_run.json`와 `.pipeline/runs/<run_id>/status.json`, `events.jsonl` 경로를 active reader가 사용합니다. |
| receipt close authority | 충족 | `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py` | receipt 없이 `VERIFY_DONE -> CLOSED`가 되지 않도록 gate가 분리되어 있습니다. |
| wrapper readiness/recovery | 충족 | `pipeline_runtime/cli.py`, `pipeline_runtime/wrapper_events.py`, `tests/test_pipeline_runtime_supervisor.py`, `tests/test_pipeline_runtime_gate.py` | `READY`, `HEARTBEAT`, `TASK_ACCEPTED`, `TASK_DONE`, `BROKEN` 경계와 recovery 검증이 들어와 있습니다. |
| legacy compat/debug surface | 부분충족 | `pipeline_gui/backend.py`, `pipeline_gui/agents.py`, `pipeline_gui/legacy_backend_debug.py`, `pipeline_gui/legacy_agent_observers.py`, `report/pipeline_runtime/verification/2026-04-15-legacy-debug-helper-isolation.md` | active path blocker는 아니지만 compat/debug helper가 코드베이스에 남아 있습니다. |
| short smoke / fault-check | 충족 | `report/pipeline_runtime/verification/2026-04-15-synthetic-soak-short.md`, `report/pipeline_runtime/verification/2026-04-15-fault-check.md`, `tests/test_pipeline_runtime_gate.py` | 최신 코드 기준 단기 게이트는 통과 기록이 있습니다. |
| 6h synthetic soak | 미충족 | `report/pipeline_runtime/verification/2026-04-11-6h-mini-soak.md`, `report/pipeline_runtime/cutover/2026-04-11-adoption-gate-status.md` | 현재 채택 기준에서 요구하는 최신 synthetic rerun 증빙은 아직 없습니다. |
| 24h synthetic soak | 미충족 | `report/pipeline_runtime/verification/2026-04-12-24h-synthetic-soak.md`, `report/pipeline_runtime/cutover/2026-04-11-adoption-gate-status.md` | existing synthetic 24h 기록은 receipt 조건 실패가 있어 최신 채택 근거로 쓸 수 없습니다. |
| final cutover sign-off | 미충족 | `report/pipeline_runtime/cutover/2026-04-11-adoption-gate-status.md` | cutover 상태 문서가 아직 rerun/sign-off 필요 상태로 남아 있습니다. |

## 근거
- 문서 기준선은 `docs/projectH_pipeline_runtime_docs/01_개발계획서.md`, `02_요구사항_명세서.md`, `04_QA_시험계획서.md`, `07_마이그레이션_체크리스트.md`입니다.
- 현재 구현은 launcher/controller/pipeline_gui active path를 runtime status/event 중심으로 전환했고, supervisor single-writer와 receipt/wrapper 계약도 코드와 테스트에 반영되어 있습니다.
- 다만 문서 세트의 최종 채택 조건은 구조 전환만이 아니라 최신 기준 `6h`/`24h` synthetic soak와 cutover sign-off까지 포함합니다.

## 남은 갭
- 최신 코드 기준 `6h` synthetic mini soak 재실행 및 통과 기록 추가
- 최신 코드 기준 `24h` synthetic soak 재실행 및 통과 기록 추가
- 위 결과를 반영한 cutover/sign-off 문구 갱신
- compat/debug surface 잔존 여부를 후속 정리 대상으로 유지하되, active path 재유입은 계속 금지
