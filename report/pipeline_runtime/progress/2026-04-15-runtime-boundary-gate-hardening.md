# 2026-04-15 runtime boundary and gate hardening

## 요약
- `pipeline-launcher.py`의 잔존 `tmux/watcher` readiness 문구와 attach helper naming을 runtime 중심으로 정리했습니다.
- `pipeline_gui.backend.confirm_pipeline_start()`가 supervisor runtime state를 watcher alive로 다시 재판정하지 않도록 정리했습니다.
- `pipeline_runtime/supervisor.py`와 `scripts/pipeline_runtime_gate.py`의 fault/recovery 경계를 보정해, synthetic short smoke와 synthetic fault-check가 최신 코드 기준으로 다시 통과하도록 만들었습니다.

## 변경 파일
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
- `docs/projectH_pipeline_runtime_docs/00_문서세트_안내.md`
- `docs/projectH_pipeline_runtime_docs/01_개발계획서.md`
- `docs/projectH_pipeline_runtime_docs/02_요구사항_명세서.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `docs/projectH_pipeline_runtime_docs/06_ADR_아키텍처_결정기록.md`
- `docs/projectH_pipeline_runtime_docs/07_마이그레이션_체크리스트.md`
- `report/pipeline_runtime/cutover/2026-04-11-adoption-gate-status.md`

## 핵심 변경
- launcher/runtime 경계
  - `tmux_attach`를 `runtime_attach`로 정리했습니다.
  - pending/start 안내 문구를 `tmux/watcher 기동` 표현 대신 `runtime lane readiness` 기준으로 바꿨습니다.
  - pending clear도 watcher alive shortcut을 제거하고 `runtime_state in RUNNING/DEGRADED + ready lane` 기준으로 좁혔습니다.
- backend/controller 경계
  - `confirm_pipeline_start()`는 watcher alive 재확인을 제거하고 supervisor status를 신뢰하게 했습니다.
  - controller/browser UI가 runtime API only surface라는 점을 소스 회귀 테스트로 고정했습니다.
- single-writer / receipt / wrapper 회귀
  - `current_run.json`이 run-scoped `status.json` / `events.jsonl`을 가리키는 계약을 테스트로 고정했습니다.
  - `VERIFY_DONE`라도 receipt 없이는 `CLOSED`가 아니라 `RECEIPT_PENDING`에 머무는 전이를 테스트로 고정했습니다.
  - enabled lane 전부 READY 전에는 `RUNNING`이 아니라 `STARTING`이어야 한다는 전이를 테스트로 고정했습니다.
  - session loss 시 lane health가 이미 `OFF`로 떨어져도 `session_missing` degraded가 유지되도록 보정했습니다.
- gate 안정화
  - `fault-check`는 synthetic workspace에서 실행되도록 바꿨습니다.
  - `fault-check`가 `RUNNING + ready lane` 이후에만 fault를 넣고, pane pid fallback 대신 wrapper pid를 우선 사용하도록 바꿨습니다.
  - latest code 기준 short synthetic smoke와 fault-check를 다시 통과시켰습니다.

## 남은 리스크
- 최신 코드 기준 6시간 / 24시간 synthetic soak는 아직 rerun하지 않았습니다.
- `pipeline_gui/backend.py`, `pipeline_gui/agents.py`의 legacy compat/debug surface는 남아 있으므로, 완전 삭제는 후속 정리 작업이 필요합니다.
- 이번 라운드는 PTY pilot 범위를 열지 않았으므로 canonical runtime 채택 범위는 여전히 `TmuxAdapter` 기반입니다.
