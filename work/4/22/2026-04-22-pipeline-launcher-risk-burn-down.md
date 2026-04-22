# 2026-04-22 pipeline launcher risk burn-down

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `watcher_core.py`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/cli.py`
- `scripts/pipeline_runtime_gate.py`
- `pipeline-launcher.py`
- `pipeline_gui/home_models.py`
- `pipeline_gui/home_controller.py`
- `controller/server.py`
- `controller/js/cozy.js`
- `controller/js/state.js`
- `e2e/tests/controller-smoke.spec.mjs`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_gui_home_controller.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_controller_server.py`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.pipeline/operator_request.md` active slot header를 `OPERATOR_POLICY: internal_only`, `DECISION_CLASS: release_gate`로 정규화했습니다.

## 사용 skill
- `security-gate`: runtime stop/cleanup, shell command override, status CLI, restart 검증의 로컬/감사 경계를 확인했습니다.
- `approval-flow-audit`: operator approval/gate 경계가 product save approval과 섞이지 않고 real-risk stop을 자동 진행하지 않는지 확인했습니다.
- `doc-sync`: controller smoke, runtime status, operator gate shared evaluator 변경을 문서에 동기화했습니다.
- `release-check`: 테스트, 문서, live runtime 상태, 남은 리스크를 마감 전 점검했습니다.
- `work-log-closeout`: 실제 변경과 검증 결과 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- 서브에이전트 감사에서 pipeline launcher/watcher/supervisor의 남은 주요 리스크가 operator gate/stale 판정 중복, 넓은 watcher cleanup fallback, Tk/TUI/controller 상태 detail 누락으로 좁혀졌습니다.
- 목표는 product MVP 동작을 넓히지 않고, 런처 자동화가 같은 runtime truth를 얇게 소비하도록 정리하는 것이었습니다.

## 핵심 변경
- `pipeline_runtime.operator_autonomy`에 stale operator recovery와 gated operator marker 공용 helper를 추가하고, watcher/supervisor가 같은 marker shape을 소비하게 했습니다.
- supervisor watcher cleanup은 `current_run.json`의 watcher pid/fingerprint를 먼저 사용하고, `pgrep -f` fallback은 repo root cwd가 정확히 맞는 watcher 프로세스에만 적용하도록 좁혔습니다.
- lane command override는 `PIPELINE_RUNTIME_ALLOW_LANE_COMMAND_OVERRIDE=1`이 있을 때만 활성화하고, 명령 원문을 남기지 않고 `lane_command_override` event에 source와 `command_sha256`만 기록합니다. opt-in 없는 override는 `lane_command_override_ignored` event만 남깁니다.
- `python3 -m pipeline_runtime.cli status <project-root> --json` read-only 상태 명령을 추가했습니다.
- Tk `HomeSnapshot`, curses launcher, controller sidebar가 runtime-owned automation detail, stale control age, stale advisory pending을 표시하도록 맞췄습니다.
- controller smoke에 automation attention detail 시나리오를 추가하고 관련 README/runtime docs를 동기화했습니다.
- runtime 재시작 후 새 run `20260422T051327Z-p279400`가 `RUNNING`, `automation_health=ok`, watcher alive 상태로 확인됐습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py pipeline_runtime/cli.py pipeline_gui/home_models.py pipeline_gui/home_controller.py controller/server.py` -> 통과
- `python3 -m unittest tests.test_operator_request_schema tests.test_pipeline_runtime_cli tests.test_pipeline_gui_home_controller tests.test_pipeline_launcher tests.test_controller_server -q` -> 95 tests OK
- `python3 -m pytest tests/test_pipeline_launcher.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_schema.py tests/test_turn_arbitration.py tests/test_pipeline_runtime_cli.py tests/test_operator_request_schema.py tests/test_pipeline_gui_home_controller.py tests/test_pipeline_gui_home_presenter.py tests/test_controller_server.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_gate.py -q` -> 554 passed, 12 subtests passed
- `cd e2e && CONTROLLER_SMOKE_PORT=8781 npx playwright test -c playwright.controller.config.mjs --reporter=line` -> 13 passed
- `git diff --check` -> 통과
- `python3 -m pipeline_runtime.cli status . --json` -> read-only status 출력 확인
- `python3 -m pipeline_runtime.cli restart . --mode experimental --session aip-projectH --no-attach` -> 재시작 성공, 이후 status `RUNNING / automation_health=ok`

## 남은 리스크
- 이번 런처 안정화 범위에서 확인된 High/Medium 리스크는 코드와 테스트로 닫았습니다.
- controller `cozy.js`와 `state.js` presentation 중복은 이번에 같은 필드를 동기화했지만, 완전한 JS shared-helper 통합은 별도 UI refactor 후보로 남깁니다.
- 현재 worktree에는 live pipeline의 별도 Axis 3 작업 파일(`core/contracts.py`, `app/frontend/src/components/MessageBubble.tsx`, `work/4/22/2026-04-22-content-reason-label-chips.md`)이 함께 dirty 상태입니다. 이 파일들은 이번 런처 안정화 변경이 아니며 되돌리지 않았습니다.
- 전체 `app.web` browser smoke는 이번 operator tooling 범위가 아니어서 실행하지 않았습니다.
