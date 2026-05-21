# 2026-05-20 controller queue coverage doc sync

## 변경 파일

- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/5/20/2026-05-20-controller-queue-coverage-doc-sync.md`

## 사용 skill

- `doc-sync`: controller Queue presentation coverage의 현재 구현/검증 사실을 문서에 맞추기 위해 사용했습니다.
- `finalize-lite`: 구현 라운드 종료 전 실제 검증 결과, 문서 동기화 필요성, 남은 리스크를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `tests/test_controller_queue_presentation.py`는 `state.js` payload-level guard와 socket-free `cozy.js` Queue behavior guard를 갖고 있습니다.
- `e2e/tests/controller-smoke.spec.mjs`에는 sidebar `Queue` 행과 marquee payload 문구를 확인하는 browser-level Queue presentation scenario가 추가되어 있습니다.
- 기존 `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`는 dedicated controller Playwright smoke를 설명했지만, 새 Queue coverage와 현재 local Playwright `local_socket_guard_auto_held` 상태를 반영하지 않았습니다.

## 핵심 변경

- `docs/MILESTONES.md`의 internal operator runtime slice에 controller Queue presentation coverage 문구를 추가했습니다.
- `docs/TASK_BACKLOG.md`의 operator tooling 설명 아래에 같은 coverage truth를 추가했습니다.
- 문구는 browser-level Queue smoke scenario와 socket-free `controller/js/cozy.js` Queue behavior guard를 모두 언급합니다.
- 현재 환경의 Playwright 실행은 `local_socket_guard_auto_held`일 수 있음을 명시해 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않도록 했습니다.
- controller/operator tooling이 current `app.web` release gate 밖이라는 기존 경계는 유지했습니다.

## 검증

- `rg -n 'Queue presentation coverage|sidebar \`Queue\` row|socket-free \`controller/js/cozy.js\` Queue behavior guard|local_socket_guard_auto_held' docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: PASS. 두 문서에서 새 Queue coverage 문구가 확인되었습니다.
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: PASS.
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md work/5/20/2026-05-20-controller-queue-coverage-doc-sync.md`
  - 결과: PASS.

## 남은 리스크

- Playwright, full controller smoke, broad e2e, 전체 unittest, long soak는 실행하지 않았습니다. 이번 slice는 문서 동기화에 한정되어 있고, Playwright 실행 실패는 기존 `/verify`에 `local_socket_guard_auto_held`로 기록되어 있습니다.
- `controller/js/cozy.js`와 `controller/js/state.js`의 Queue presentation helper 중복은 이번 slice에서 정리하지 않았습니다.
- 실제 browser DOM에서 Queue scenario가 통과하는지는 가능한 환경에서 별도로 확인해야 합니다.
- worktree에는 이번 라운드 이전부터 있던 다른 dirty 변경과 미추적 `/work`·`/verify` 파일들이 남아 있습니다. 이번 라운드는 위 변경 파일만 다뤘습니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
