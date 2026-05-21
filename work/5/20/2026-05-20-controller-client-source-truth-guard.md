# 2026-05-20 controller client source truth guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-client-source-truth-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2054`가 controller source-contract test에서 현재 shipped controller shell client인 `cozy.js`와 module-side panel client source인 `panel.js`를 구분하라고 지시했다.
- 이전 request-shape guard는 `cozy.js`와 `panel.js` POST/JSON 형태를 확인했지만, `panel.js`가 `controller/index.html`에서 직접 로드되는 shell script가 아니라 `zones.js`가 import하는 module-side source라는 사실을 테스트에 명시하지 않았다.

## 핵심 변경
- `test_controller_html_polls_runtime_api_only`가 `controller/js/zones.js`도 읽도록 보강했다.
- `controller/index.html`이 `queue-presentation.js`를 `cozy.js`보다 먼저 직접 로드하는지 확인했다.
- `controller/index.html`이 `panel.js`, `zones.js`, `state.js`, `config.js`, `agents.js`, `canvas.js`, `sidebar.js`를 직접 script로 로드하지 않는지 확인했다.
- `cozy.js` action button 및 modal send-input POST/JSON request-shape assertions에는 shipped shell source라는 주석을 붙였다.
- `zones.js`가 `./panel.js`를 import하고, `panel.js`의 send-input POST/JSON request-shape는 module-side source contract로 확인하도록 주석과 assertion을 보강했다.
- `controller/index.html`, `controller/js/cozy.js`, `controller/js/panel.js`, `controller/js/zones.js`, `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 44 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free source-contract truth guard만 추가했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
