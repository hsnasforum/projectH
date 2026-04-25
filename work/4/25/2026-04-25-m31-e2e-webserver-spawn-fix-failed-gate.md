# 2026-04-25 M31 e2e webServer spawn fix failed gate

## 변경 파일
- `Makefile`
- `e2e/playwright.config.mjs`
- `work/4/25/2026-04-25-m31-e2e-webserver-spawn-fix-failed-gate.md`

## 사용 skill
- `security-gate`: `make e2e-test`의 shell 실행 경로와 로컬 webServer 기동 방식을 바꾸는 작업이라 local-only/권한/rollback 범위를 확인하기 위해 사용했습니다.
- `release-check`: M28–M30 bundle release gate의 ready/not ready 상태와 확인 범위를 구분하기 위해 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 실패 결과, 미실행 검증, 남은 리스크를 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- `CONTROL_SEQ: 150` implement handoff에 따라 Playwright가 Node.js 자식 프로세스로 webServer를 스폰할 때 발생하던 `PermissionError: [Errno 1] Operation not permitted`를 우회하고 release gate를 완료해야 했습니다.
- handoff의 지정 변경은 `Makefile`에서 로컬 mock web server를 먼저 직접 기동하고, `e2e/playwright.config.mjs`에서 `reuseExistingServer`를 켜는 방식이었습니다.

## 핵심 변경
- `e2e/playwright.config.mjs`에서 `webServer.reuseExistingServer`를 `true`로 변경했습니다.
- `Makefile`의 `e2e-test` 타겟이 `mktemp -d` 기반 SQLite DB 경로를 만들고, mock provider 환경변수와 함께 `python3 -m app.web --host 127.0.0.1 --port 8879`를 먼저 백그라운드 실행한 뒤 `cd e2e && npm test`를 실행하도록 변경했습니다.
- 테스트 종료 후 `kill $SERVER_PID`로 직접 기동한 서버를 정리하도록 했습니다.
- 변경은 로컬 `127.0.0.1` 테스트 서버 기동 경로에 한정되며, 승인/저장/외부 publication 흐름은 건드리지 않았습니다.
- E2E gate는 여전히 통과하지 못했습니다. tail 출력 기준으로 Playwright가 `config.webServer` 시작을 시도했고 동일한 socket 생성 `PermissionError`가 발생했습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `e40a774c0750197ad1462f33884719d1cf60d086819d3c4b1d3ce172a1bff2c4`
- `git diff --check -- Makefile e2e/playwright.config.mjs`
  - 통과: 출력 없음
- `make e2e-test 2>&1 | tail -10`
  - 실패: webServer process start 실패, `make` exit code 2
  - 관찰된 tail:
    - `[WebServer] super().__init__(server_address, LocalAssistantHandler)`
    - `[WebServer] File "/usr/lib/python3.12/socketserver.py", line 453, in __init__`
    - `[WebServer] self.socket = socket.socket(self.address_family,`
    - `[WebServer] File "/usr/lib/python3.12/socket.py", line 233, in __init__`
    - `[WebServer] _socket.socket.__init__(self, family, type, proto, fileno)`
    - `[WebServer] PermissionError: [Errno 1] Operation not permitted`
    - `Error: Process from config.webServer was not able to start. Exit code: 1`
    - `make: *** [Makefile:13: e2e-test] Error 1`
- `python3 -m unittest tests/test_watcher_core.py tests/test_watcher_signals.py tests/test_controller_monitor.py -v 2>&1 | tail -5`
  - 미실행: handoff가 E2E 실패 시 실패 상세 기록 후 stop을 지시했습니다.
- `python3 -m py_compile watcher_core.py watcher_signals.py controller/monitor.py`
  - 미실행: E2E gate 실패 후 stop 지시를 따랐습니다.

## 남은 리스크
- release gate는 통과하지 못했습니다. 현재 변경 후에도 `make e2e-test`는 Playwright webServer socket 생성 단계의 `PermissionError: [Errno 1] Operation not permitted`로 실패합니다.
- direct prestart server가 재사용 가능한 상태가 되지 않아 Playwright가 자체 `webServer` command를 시도한 것으로 보이지만, tail 출력만으로 direct prestart 실패 원인을 별도 확정하지는 않았습니다.
- unit 216 tests와 compile check는 이번 round에서 확인하지 않았습니다.
- 추가 E2E 환경 수정, 권한/포트/서버 readiness 재진단, 다음 slice 선택, advisory/operator_request 작성은 implement handoff 범위 밖이라 수행하지 않았습니다.
