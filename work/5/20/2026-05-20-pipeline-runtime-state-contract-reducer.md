# 2026-05-20 파이프라인 런타임 상태 계약 리듀서 정리

## 목적
- 런처/파이프라인이 `READY`, `prompt_visible`, stale operator/advisory stop을 서로 다르게 해석하면서 재시작 루프와 Queue 오표시가 반복되는 문제를 줄였다.
- 자동 파이프라인은 먼저 중지했고, 기준 스냅샷은 `.pipeline/freeze-snapshots/20260520T123920Z/`에 남겼다.
- commit/push/PR/merge는 수행하지 않았다.

## 사용한 스킬
- `security-gate`: 런타임 control/status/dispatch 경로 변경의 승인 경계와 기록 경계를 확인했다.
- `doc-sync`: 실제 변경된 런타임 계약을 `.pipeline/README.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`에 동기화했다.

## 변경 파일
- `pipeline_runtime/state_contract.py`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/cli.py`
- `watcher_prompt_assembly.py`
- `controller/server.py`
- `controller/js/queue-presentation.js`
- `controller/js/state.js`
- `controller/js/cozy.js`
- `controller/index.html`
- `tests/test_pipeline_runtime_state_contract.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_controller_queue_presentation.py`
- `tests/fixtures/controller_queue_presentation_cases.json`
- `.pipeline/README.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 핵심 변경
- `RuntimeSnapshot` 순수 리듀서 계약을 추가했다.
  - `ControlState`, `RoundState`, `LaneLifecycle`, `RuntimeHealth`, `RuntimeSnapshot`로 런타임 표면을 분리했다.
  - 활성 control 또는 active verify round가 있는데 Queue가 `No queued pipeline task`로 내려가는 경우를 불변식 위반으로 잡는다.
  - `prompt_visible`은 관찰값으로만 다루고, 작업 완료 판단은 task hint 해제, dispatch id, receipt 등 명시 근거가 있을 때만 허용한다.
- supervisor와 CLI stopped/status 경로가 `runtime_snapshot`을 함께 쓰도록 했다.
  - `stop` 조기 반환 경로도 status 보정을 건너뛰지 않도록 고쳤다.
  - controller server는 기존 status에 snapshot이 없어도 응답 시 합성한다.
- watcher stale advisory recovery 경로를 고쳤다.
  - 오래된 advisory request를 `superseded`로 바꾼 뒤에도 verify recovery prompt가 active-control mismatch로 드롭되지 않게 했다.
- controller Queue 판단을 공유 JS helper로 모았다.
  - `controller/js/state.js`와 `controller/js/cozy.js`가 `PipelineQueuePresentation`을 함께 사용한다.
  - controller는 `runtime_snapshot.queue`가 있으면 이를 우선 소비한다.
- wrapper `READY`/`prompt_visible` 처리 계약을 보수적으로 바꿨다.
  - active task hint가 남아 있으면 `prompt_visible`만으로 `TASK_DONE`을 만들지 않는다.

## 검증
- `python3 -m py_compile pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py pipeline_runtime/cli.py controller/server.py watcher_prompt_assembly.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_state_contract tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_cli tests.test_watcher_core tests.test_turn_arbitration tests.test_pipeline_runtime_automation_health tests.test_controller_queue_presentation`
  - 528 tests 통과.
- `cd e2e && npx playwright test tests/controller-smoke.spec.mjs -g "controller renders Queue presentation from runtime payloads" --reporter=line`
  - 1 test 통과.
- `git diff --check -- .pipeline/README.md README.md controller/index.html controller/js/cozy.js controller/js/state.js controller/server.py docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_prompt_assembly.py tests/test_pipeline_runtime_cli.py tests/test_controller_queue_presentation.py tests/fixtures/controller_queue_presentation_cases.json`
  - 통과.
- `python3 -m pipeline_runtime.cli stop .`
  - 현재 status는 `STOPPED`, `runtime_snapshot.contract_version=2026-05-20.runtime_snapshot_v1`, Queue는 `Runtime inactive`.

## 남은 리스크
- 기존 worktree에는 이번 라운드 이전부터 많은 수정/미추적 파일이 남아 있다. 이번 라운드에서는 해당 파일을 되돌리지 않았다.
- Playwright는 Queue 표면의 좁은 controller 시나리오만 실행했다. 전체 controller smoke나 장시간 soak는 이번 변경 범위와 비용 대비 실행하지 않았다.
- 자동 파이프라인은 의도적으로 중지 상태다. 재시작은 이 변경을 검토한 뒤 별도 명령으로 수행해야 한다.
