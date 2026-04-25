# 2026-04-25 M34 release gate stale-server fix 실패 기록

## 변경 파일
- `Makefile`
- `work/4/25/2026-04-25-m34-release-gate-stale-server-fix-failed.md`

## 사용 skill
- `security-gate`: `make e2e-test` 시작 시 포트 8879 점유 프로세스를 강제 종료하는 runtime control 변경이므로 위험 경계를 확인했습니다.
- `work-log-closeout`: Makefile 변경, 실제 gate 실패 결과, 미실행 검증을 `/work` closeout으로 기록하기 위해 사용했습니다.

## 변경 이유
- M34 Axis 2 handoff에 따라 `make e2e-test`가 신규 서버를 띄우기 전에 포트 8879에 남아 있는 구버전/stale 서버를 종료하도록 보강해야 했습니다.

## 핵심 변경
- `Makefile`의 `e2e-test` 타겟 시작부에 `lsof -ti:8879 2>/dev/null | xargs kill -9 2>/dev/null || true`를 추가했습니다.
- stale 서버 종료 후 포트 해제를 기다리도록 `sleep 1`을 추가했습니다.
- 기존 mock provider, sqlite temp DB, `python3 -m app.web --host 127.0.0.1 --port 8879`, `cd e2e && npm test` 흐름은 유지했습니다.
- 보안 경계: 종료 대상은 로컬 포트 8879 점유 프로세스로 한정되며, 외부 네트워크/저장 형식/승인 흐름 변경은 없습니다.

## 검증
- `git diff --check -- Makefile`
  - 통과, 출력 없음.
- `lsof -ti:8879 2>/dev/null || true`
  - gate 시작 전 출력 없음. 포트 8879 비어 있음.
- `make e2e-test 2>&1 | tail -10`
  - 실패. 마지막 출력:
    - `PermissionError: [Errno 1] Operation not permitted`
    - `Error: Process from config.webServer was not able to start. Exit code: 1`
    - `make: *** [Makefile:13: e2e-test] Error 1`
- `lsof -ti:8879 2>/dev/null || true`
  - 실패 후 출력 없음. 포트 8879 비어 있음.
- `python3 -m unittest tests/test_watcher_core.py tests/test_watcher_signals.py tests/test_controller_monitor.py tests/test_preference_handler.py -v 2>&1 | tail -5`
  - 실행하지 않음. handoff가 E2E 실패 시 실패 시나리오를 기록하고 STOP하라고 지시해 자체 추가 검증으로 진행하지 않았습니다.

## 남은 리스크
- M28-M34 누적 bundle release gate는 통과하지 못했습니다. 실패는 Playwright webServer 시작 단계의 `PermissionError: [Errno 1] Operation not permitted`로 관찰됐고, handoff 지시에 따라 자체 수정은 시도하지 않았습니다.
- Makefile stale-server kill 보강은 적용됐지만, 현재 환경에서는 release gate가 webServer startup permission 문제로 막혀 실제 `147 passed` 이상 여부를 확인하지 못했습니다.
