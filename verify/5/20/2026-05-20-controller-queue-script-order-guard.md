# 2026-05-20 controller Queue script order guard 검증

## 검증 대상
- `tests/test_controller_server.py`의 controller HTML/script 정적 guard
- `queue-presentation.js`가 `cozy.js`보다 먼저 로드되는지 확인
- `PipelineQueuePresentation` export와 `cozy.js` helper 의존성 확인

## 변경 파일
- 검증 기록 파일 자체 외에는 없음.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 29 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_controller_html_polls_runtime_api_only`는 `src="/controller-assets/js/queue-presentation.js"`와 `src="/controller-assets/js/cozy.js"`가 모두 존재하고, `queue-presentation.js`가 `cozy.js`보다 먼저 나타나는지 확인한다.
- 같은 테스트는 `controller/js/queue-presentation.js`가 `PipelineQueuePresentation = Object.freeze`를 export하고, `controller/js/cozy.js`가 `queuePresentationHelper()`와 `globalThis.PipelineQueuePresentation`을 계속 참조하는지 확인한다.
- `controller/index.html`, `controller/js/queue-presentation.js`, `controller/js/cozy.js` 생산 코드는 이번 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2045`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.
- 다음 같은 계열의 안전한 local slice는 controller asset resolver가 `js/queue-presentation.js`와 `js/cozy.js`를 실제 파일로 해석하고 JS content type으로 제공하는지 socket-free unit guard를 추가하는 것이다.
