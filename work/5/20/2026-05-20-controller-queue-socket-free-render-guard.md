# 2026-05-20 controller queue socket-free render guard

## 변경 파일

- `tests/test_controller_queue_presentation.py`
- `work/5/20/2026-05-20-controller-queue-socket-free-render-guard.md`

## 사용 skill

- `e2e-smoke-triage`: Playwright를 재시도하지 않고 browser-visible Queue 표시 계약을 socket-free 검증으로 좁히기 위해 사용했습니다.
- `finalize-lite`: 구현 범위, 실제 검증, 문서 동기화 필요 여부, 남은 리스크를 마무리 전에 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- 기존 Queue presentation guard는 `state.js`와 socket-free `cozy.js`의 순수 presentation 값을 검증했지만, `cozy.js`의 rendered sidebar `Queue` row와 marquee `Queue ...` text까지 같은 contract가 도달하는지는 Playwright 없이 확인하지 못했습니다.
- focused controller Playwright는 기존 검증에서 `local_socket_guard_auto_held`로 보류되어 있으므로, handoff `#2041`은 server socket 없이 rendered surface를 확인하는 Node guard를 요구했습니다.

## 핵심 변경

- `test_cozy_queue_presentation_reaches_rendered_surfaces_without_socket`를 추가했습니다.
- 새 테스트는 기존 `QUEUE_PRESENTATION_CASES`를 그대로 사용하며 별도 Queue expected matrix를 만들지 않습니다.
- Node에서 `controller/js/cozy.js` 원문을 읽고 `getPresentation()`, `restartMarqueeAnimation()`/`setMarqueeText()`/`updateMarqueeFromState()`, `renderSidebar()` 범위만 평가합니다.
- 최소 fake DOM과 `runtimeStateStore`를 구성해 `#tab-content` sidebar HTML의 `Queue` row text/class와 `#marquee-text`의 `Queue ...` 문구를 모든 shared Queue case에 대해 검증합니다.
- `controller/js/cozy.js`, `controller/js/state.js`, `controller/index.html`은 이번 라운드에서 수정하지 않았습니다. 문서도 기존 coverage 문구와 모순이 없어 변경하지 않았습니다.

## 검증

- `python3 -m py_compile tests/test_controller_queue_presentation.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_controller_queue_presentation`
  - 결과: PASS. 3개 테스트가 통과했습니다.
- `git diff --check -- tests/test_controller_queue_presentation.py controller/js/cozy.js work/5/20/`
  - 결과: PASS.
- `git diff --no-index --check -- /dev/null tests/test_controller_queue_presentation.py`
  - 결과: whitespace warning 없음. `tests/test_controller_queue_presentation.py`는 현재 git 기준 미추적 파일이라 `/dev/null` 비교 자체로 exit 1이 발생하지만, check warning 출력은 없었습니다.

## 남은 리스크

- production helper duplication은 남아 있습니다. 이번 slice는 classic `cozy.js` script/module loading boundary를 바꾸지 않는 socket-free render test guard에 한정했습니다.
- 실제 browser DOM Queue scenario pass는 확인하지 않았습니다. focused controller Playwright는 기존 검증에서 `local_socket_guard_auto_held` 환경 이슈로 보류되어 있으며, 이번 라운드는 browser-visible runtime 동작을 바꾸지 않았습니다.
- `controller/js/cozy.js`, `controller/js/state.js`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, 미추적 `/verify`·기존 `/work` 파일 등 이번 라운드 이전부터 누적된 dirty worktree가 남아 있습니다. 이번 라운드는 위 변경 파일만 다뤘습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
