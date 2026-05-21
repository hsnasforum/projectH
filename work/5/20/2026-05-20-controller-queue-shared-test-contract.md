# 2026-05-20 controller queue shared test contract

## 변경 파일

- `tests/test_controller_queue_presentation.py`
- `work/5/20/2026-05-20-controller-queue-shared-test-contract.md`

## 사용 skill

- `finalize-lite`: 구현 범위, 실제 검증, 문서 동기화 필요 여부, 남은 리스크를 마무리 전에 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- 기존 `tests/test_controller_queue_presentation.py`는 `state.js` payload-level guard와 socket-free `cozy.js` guard가 각각 별도 Queue presentation case matrix를 갖고 있어 기대값 drift가 생길 수 있었습니다.
- handoff `#2040`은 controller runtime 동작이나 classic `cozy.js` 로딩 경계를 바꾸지 않고, 두 guard가 하나의 테스트 contract를 공유하도록 요구했습니다.

## 핵심 변경

- `QUEUE_PRESENTATION_CASES`를 Python module-level 단일 case matrix로 추가했습니다.
- `QUEUE_PRESENTATION_CONTRACT_TEMPLATE`와 `_queue_contract_script()`를 추가해 Node 검사 두 곳이 같은 base payload, payload merge, `assertQueuePresentation()` 계약을 주입받도록 했습니다.
- `PipelineState.getPresentation()` 경로와 socket-free extracted `cozy.js` `getPresentation()` 경로가 같은 expected matrix를 검증합니다.
- 공유 matrix에는 normal live idle, active implement control seq suffix, active verify round, attention, recovering, needs_operator warning case를 포함했습니다.
- `controller/js/state.js`, `controller/js/cozy.js`, `controller/index.html`은 이번 라운드에서 수정하지 않았습니다.

## 검증

- `python3 -m py_compile tests/test_controller_queue_presentation.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_controller_queue_presentation`
  - 결과: PASS. 2개 테스트가 통과했습니다.
- `node --check controller/js/cozy.js`
  - 결과: PASS.
- `node --input-type=module --check < controller/js/state.js`
  - 결과: PASS.
- `git diff --check -- tests/test_controller_queue_presentation.py controller/js/state.js controller/js/cozy.js work/5/20/`
  - 결과: PASS.
- `git diff --no-index --check -- /dev/null tests/test_controller_queue_presentation.py`
  - 결과: whitespace warning 없음. `tests/test_controller_queue_presentation.py`는 현재 git 기준 미추적 파일이라 `/dev/null` 비교 자체로 exit 1이 발생하지만, check warning 출력은 없었습니다.
- `git diff --no-index --check -- /dev/null work/5/20/2026-05-20-controller-queue-shared-test-contract.md`
  - 결과: whitespace warning 없음. 새 `/work` 파일도 git 기준 미추적 파일이라 `/dev/null` 비교 자체로 exit 1이 발생하지만, check warning 출력은 없었습니다.

## 남은 리스크

- production helper duplication은 남아 있습니다. `cozy.js`는 classic script로 로드되고 있어 production shared-helper extraction은 controller script/module boundary 변경을 동반할 수 있으므로 이번 test-contract slice에서는 수행하지 않았습니다.
- 실제 browser DOM Queue scenario pass는 확인하지 않았습니다. 기존 검증에서 focused controller Playwright는 `local_socket_guard_auto_held` 환경 이슈로 보류되어 있으며, 이번 라운드는 browser-visible runtime 동작을 바꾸지 않았습니다.
- `controller/js/cozy.js`, `controller/js/state.js`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, 미추적 `/verify`·기존 `/work` 파일 등 이번 라운드 이전부터 누적된 dirty worktree가 남아 있습니다. 이번 라운드는 위 변경 파일만 다뤘습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
