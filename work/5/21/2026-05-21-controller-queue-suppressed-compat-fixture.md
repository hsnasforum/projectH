# 2026-05-21 controller Queue suppressed compat fixture

## 변경 파일

- `tests/fixtures/controller_queue_presentation_cases.json`
- `tests/test_controller_queue_presentation.py`
- `work/5/21/2026-05-21-controller-queue-suppressed-compat-fixture.md`

## 사용 skill

- `security-gate`: controller Queue surface가 stale compat `operator_request.md#2072`를 active operator wait처럼 재승격하지 않는 local-only 경계인지 확인하기 위해 사용했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유

- `runtime_snapshot.queue`는 reducer-owned consumer contract이며 controller/state/cozy는 이 값을 우선해야 한다.
- 직전 reducer slice가 suppressed compat `operator_request.md + needs_operator`를 debug-only로 낮췄지만, browser-facing socket-free fixture에는 stale compat operator slot과 reducer-owned queue가 함께 있는 케이스가 없었다.
- rendered cozy surface 테스트는 현재 UI의 한국어 라벨(`큐`, `대기열`) 대신 과거 `Queue` 라벨만 찾고 있어 기존 `normal live idle` 케이스에서 실패했다.

## 핵심 변경

- `tests/fixtures/controller_queue_presentation_cases.json`에 `runtime snapshot queue suppresses stale compat operator control` 케이스를 추가했다.
- 새 fixture는 compat active `operator_request.md#2072 needs_operator`와 `runtime_snapshot.queue.status=VERIFYING`을 함께 넣고, controller presentation이 `VERIFYING`을 표시하도록 고정한다.
- `tests/test_controller_queue_presentation.py`의 rendered surface matcher를 현재 cozy UI의 `큐`/`대기열` 라벨도 허용하도록 좁게 조정했다.
- `controller/js/queue-presentation.js`는 수정하지 않았다. 기존 shared presentation code가 새 fixture를 통과했다.

## 검증

- `python3 -m py_compile tests/test_controller_queue_presentation.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_queue_presentation`
  - 첫 실행: 실패. `test_cozy_queue_presentation_reaches_rendered_surfaces_without_socket`가 기존 `normal live idle` 케이스에서 `Queue` 라벨만 찾다가 현재 cozy UI의 `큐` 라벨을 찾지 못했다.
  - harness 조정 후 재실행: 통과. `Ran 3 tests in 0.117s`, `OK`.
- `git diff --check -- controller/js/queue-presentation.js tests/test_controller_queue_presentation.py tests/fixtures/controller_queue_presentation_cases.json`
  - 통과. 출력 없음.

## 남은 리스크

- Playwright, controller smoke, broad e2e, long soak는 실행하지 않았다. 이번 변경은 socket-free fixture/harness에 한정했다.
- `controller/js/queue-presentation.js`는 이번 라운드에서 수정하지 않았다. fixture가 기존 consumer behavior를 통과했으므로 code path 변경은 필요 없었다.
- 작업트리는 이전 라운드의 여러 dirty/untracked 파일을 계속 포함한다. 이번 closeout은 controller Queue fixture와 rendered-surface test harness 조정만 귀속한다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지 않았고 계속 held 상태다.
