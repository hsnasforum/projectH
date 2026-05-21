# 2026-05-20 controller queue shared fixture contract

## 변경 파일

- `tests/fixtures/controller_queue_presentation_cases.json`
- `tests/test_controller_queue_presentation.py`
- `e2e/tests/controller-smoke.spec.mjs`
- `work/5/20/2026-05-20-controller-queue-shared-fixture-contract.md`

## 사용 skill

- `e2e-smoke-triage`: Playwright 재시도 없이 browser-level Queue scenario의 fixture drift를 줄이는 범위를 정하기 위해 사용했습니다.
- `finalize-lite`: 실제 검증, 문서 동기화 필요 여부, 남은 리스크를 구현 라운드 종료 전에 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `tests/test_controller_queue_presentation.py`는 shared `QUEUE_PRESENTATION_CASES`로 socket-free Queue guard를 실행했지만, `e2e/tests/controller-smoke.spec.mjs`의 browser-level Queue scenario는 별도 payload/expected cases를 유지하고 있었습니다.
- handoff `#2042`는 Queue case data를 JSON fixture 하나로 묶어 Python socket-free guard와 Playwright Queue scenario의 기대값 drift를 줄이도록 요구했습니다.

## 핵심 변경

- `tests/fixtures/controller_queue_presentation_cases.json`를 추가해 Queue presentation cases를 단일 JSON fixture로 분리했습니다.
- Python socket-free guard는 해당 fixture를 읽어 기존 pure `state.js`, socket-free `cozy.js`, rendered sidebar/marquee 검증을 계속 수행합니다.
- Playwright controller Queue scenario도 같은 fixture를 읽어 `expected.pipelineQueueStatus`와 `expected.pipelineQueueClass`를 기존 `expectQueuePresentation()` helper에 전달합니다.
- Queue coverage는 normal live idle, active implement control, active verify round, attention, recovering, needs_operator case를 유지합니다.
- `controller/js/cozy.js`, `controller/js/state.js`, `controller/index.html`은 이번 라운드에서 수정하지 않았고, Playwright 실행 pass도 주장하지 않습니다.

## 검증

- `python3 -m py_compile tests/test_controller_queue_presentation.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_controller_queue_presentation`
  - 결과: PASS. 3개 테스트가 통과했습니다.
- `node --check e2e/tests/controller-smoke.spec.mjs`
  - 결과: PASS.
- `python3 -m json.tool tests/fixtures/controller_queue_presentation_cases.json >/tmp/controller_queue_cases.json.check`
  - 결과: PASS.
- `git diff --check -- tests/test_controller_queue_presentation.py tests/fixtures/controller_queue_presentation_cases.json e2e/tests/controller-smoke.spec.mjs work/5/20/`
  - 결과: PASS.
- `git diff --no-index --check -- /dev/null tests/test_controller_queue_presentation.py`
  - 결과: whitespace warning 없음. `tests/test_controller_queue_presentation.py`는 현재 git 기준 미추적 파일이라 `/dev/null` 비교 자체로 exit 1이 발생하지만, check warning 출력은 없었습니다.
- `git diff --no-index --check -- /dev/null tests/fixtures/controller_queue_presentation_cases.json`
  - 결과: whitespace warning 없음. 새 fixture는 현재 git 기준 미추적 파일이라 `/dev/null` 비교 자체로 exit 1이 발생하지만, check warning 출력은 없었습니다.

## 남은 리스크

- Playwright, controller full smoke, broad e2e는 실행하지 않았습니다. 기존 검증에서 focused controller Playwright는 `local_socket_guard_auto_held` 환경 이슈로 보류되어 있으며, 이번 라운드는 fixture contract 정리에 한정됩니다.
- production helper duplication은 남아 있습니다. 이번 slice는 classic `cozy.js` script/module loading boundary를 바꾸지 않는 test fixture 정리에 한정했습니다.
- 실제 browser DOM Queue scenario pass는 가능한 환경에서 별도 확인이 필요합니다.
- `controller/js/cozy.js`, `controller/js/state.js`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, 미추적 `/verify`·기존 `/work` 파일 등 이번 라운드 이전부터 누적된 dirty worktree가 남아 있습니다. 이번 라운드는 위 변경 파일만 다뤘습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
