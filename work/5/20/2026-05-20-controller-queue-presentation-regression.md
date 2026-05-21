# 2026-05-20 controller queue presentation regression

## 변경 파일

- `tests/test_controller_queue_presentation.py`
- `work/5/20/2026-05-20-controller-queue-presentation-regression.md`

## 사용 skill

- `finalize-lite`: 구현 라운드 종료 전 실제 검증 결과, 문서 동기화 필요성, 남은 리스크를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- controller Queue 표시가 문자열 존재 여부로만 보호되어, 실제 runtime status payload에서 정상 idle과 active/recovering/operator-needed 상태가 다시 섞여 보이는 회귀를 잡기 어려웠습니다.
- 이번 handoff의 목표는 `No queued pipeline task`가 정상 live idle에서만 나오고, active control / active round / stuck 계열 automation 상태는 별도 Queue 상태로 유지되도록 payload 수준 회귀 테스트를 추가하는 것입니다.

## 핵심 변경

- 새 `ControllerQueuePresentationTests` unittest를 추가했습니다.
- Python 테스트가 Node `--input-type=module`로 `controller/js/state.js`의 `PipelineState.getPresentation()`을 import해 실제 Queue presentation 결과를 검사합니다.
- 정상 live idle payload는 `noQueuedPipelineTask=true`, `pipelineQueueStatus="No queued pipeline task"`, `pipelineQueueClass="ok"`로 고정했습니다.
- active implement control, active verify round, `attention`, `recovering`, `needs_operator` automation payload는 `noQueuedPipelineTask=false`이며 각각 active/attention Queue 상태를 유지하도록 검증했습니다.
- dispatch, control selection, supervisor liveness, socket, approval, publication 동작은 변경하지 않았습니다.

## 검증

- `python3 -m py_compile tests/test_controller_queue_presentation.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_controller_queue_presentation`
  - 결과: PASS. 1개 테스트가 통과했습니다.
- `git diff --check -- tests/test_controller_queue_presentation.py`
  - 결과: PASS.
- `git diff --check -- tests/test_controller_queue_presentation.py work/5/20/2026-05-20-controller-queue-presentation-regression.md`
  - 결과: PASS.
- `node --input-type=module --check < controller/js/state.js`
  - 결과: PASS.
- `node --check controller/js/cozy.js`
  - 결과: PASS.

## 남은 리스크

- Playwright/e2e, 전체 unittest, socket-bound smoke, long soak는 실행하지 않았습니다. 이번 슬라이스는 controller Queue presentation의 payload 수준 회귀 테스트 추가로 제한했습니다.
- `controller/js/cozy.js`는 syntax check만 실행했습니다. 이번 테스트는 handoff가 제안한 좁은 경로대로 `controller/js/state.js`의 shared `PipelineState.getPresentation()` behavior를 직접 검증합니다.
- 제품 문서는 수정하지 않았습니다. shipped behavior 변경이 아니라 기존 Queue 표시의 회귀 보호 추가로 판단했습니다.
- worktree에는 이번 라운드 이전부터 존재한 다른 dirty 변경과 미추적 `/work`·`/verify` 파일이 남아 있습니다. 이번 라운드는 위 변경 파일만 다뤘습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
