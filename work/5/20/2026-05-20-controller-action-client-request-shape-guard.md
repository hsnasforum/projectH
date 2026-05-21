# 2026-05-20 controller action client request shape guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-action-client-request-shape-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2053`가 server-side POST route guard와 맞물려 controller UI clients가 runtime action routes를 올바른 POST/JSON request shape로 호출하는지 source-level unit guard로 고정하라고 지시했다.
- 기존 source-string 테스트는 endpoint 존재 여부를 확인했지만, `cozy.js`와 `panel.js`가 `/api/runtime/send-input` 및 start/stop/restart routes를 POST/JSON 형태로 호출하는지는 직접 고정하지 않았다.

## 핵심 변경
- `test_controller_html_polls_runtime_api_only`가 `controller/js/panel.js`도 읽도록 보강했다.
- `controller/js/cozy.js`의 `apiPost(path)`가 `fetch(path, { method: 'POST' })`를 유지하는지 확인했다.
- `controller/js/cozy.js`의 start/stop/restart 버튼이 각각 `apiPost('/api/runtime/start')`, `apiPost('/api/runtime/stop')`, `apiPost('/api/runtime/restart')`에 연결되는지 확인했다.
- `controller/js/cozy.js`의 `sendModalInput()`이 `/api/runtime/send-input`에 `method: 'POST'`, `Content-Type: application/json`, `JSON.stringify({ lane, text })`를 사용하는지 확인했다.
- `controller/js/panel.js`의 `sendInput()`이 `/api/runtime/send-input`에 `method: 'POST'`, `Content-Type: application/json`, `JSON.stringify({ lane: _panelLane, text })`를 사용하는지 확인했다.
- `controller/js/cozy.js`, `controller/js/panel.js`, `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 44 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free source-level request-shape guard만 추가했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
