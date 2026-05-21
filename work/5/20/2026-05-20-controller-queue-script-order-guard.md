# 2026-05-20 controller Queue script order guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-queue-script-order-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2045`가 `controller/index.html`에서 `/controller-assets/js/queue-presentation.js`가 `/controller-assets/js/cozy.js`보다 먼저 로드되는지 socket-free 정적 guard로 고정하라고 지시했다.
- `controller/js/cozy.js`는 `globalThis.PipelineQueuePresentation`에 의존하므로, script 순서가 바뀌면 Queue presentation helper가 로드되기 전에 사용될 수 있다.

## 핵심 변경
- `test_controller_html_polls_runtime_api_only`가 `queue-presentation.js`와 `cozy.js` script tag 존재를 모두 확인하도록 했다.
- 같은 테스트가 HTML 내 `queue-presentation.js` script 위치가 `cozy.js`보다 앞서는지 `html.index(...)`로 확인하도록 했다.
- `controller/js/queue-presentation.js`가 `PipelineQueuePresentation = Object.freeze`를 export하고, `controller/js/cozy.js`가 `queuePresentationHelper()`와 `globalThis.PipelineQueuePresentation`을 계속 참조하는지 확인했다.
- `controller/index.html`과 생산 JS 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 29 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free 정적 server/HTML guard만 추가했다. Playwright, full controller smoke, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
