# 2026-04-26 e2e healthcheck wrapper

## 변경 파일
- `Makefile`
- `e2e/start-server.sh`
- `README.md`
- `e2e/README.md`
- `docs/MILESTONES.md`
- `work/4/26/2026-04-26-e2e-healthcheck-wrapper.md`

## 사용 skill
- `doc-sync`: E2E 실행 wrapper의 실제 동작과 README/MILESTONES 설명을 맞췄습니다.
- `finalize-lite`: 변경 파일, 검증 결과, 미검증 경로, `/work` closeout 준비 상태를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 이 `/work` closeout으로 정리했습니다.

## 변경 이유
- `make e2e-test`가 smoke 포트를 강제로 kill하고 고정 sleep 뒤 Playwright를 실행하던 흐름은 기존 서버 상태와 서버 readiness에 취약했습니다.
- handoff 요구대로 `make e2e-test`가 서버 상태와 무관하게 healthcheck를 거쳐 실행되고, 자동 시작한 서버만 테스트 종료 후 정리하도록 만들 필요가 있었습니다.

## 핵심 변경
- `Makefile`의 inline 서버 kill/start/sleep 로직을 `e2e/start-server.sh` 호출로 대체했습니다.
- `e2e/start-server.sh`를 추가해 `http://127.0.0.1:8879/healthz`가 healthy하면 기존 서버를 재사용하고, 아니면 mock `app.web` 서버를 isolated temp SQLite DB로 자동 시작하도록 했습니다.
- wrapper가 직접 시작한 서버는 `trap` 기반 cleanup으로 Playwright 종료 뒤 정리하고, 기존 서버는 종료하지 않게 했습니다.
- root `README.md`와 `e2e/README.md`의 E2E smoke 실행 설명을 healthcheck 재사용/자동 시작 흐름에 맞췄습니다.
- `docs/MILESTONES.md`의 E2E 환경 개선 note를 "향후 가능"에서 현재 wrapper 구현 및 다음 verify lane 확인 필요 상태로 갱신했습니다.

## 검증
- `bash -n e2e/start-server.sh`
  - 통과, 출력 없음.
- `git diff --check -- Makefile e2e/start-server.sh README.md e2e/README.md docs/MILESTONES.md`
  - 통과, 출력 없음.
- `make e2e-test`
  - no-server auto-start 경로로 진입했습니다.
  - `[e2e] Starting app.web server at http://127.0.0.1:8879`
  - `150 passed (13.4m)`
- `python3 - <<'PY' ... urllib.request.urlopen('http://127.0.0.1:8879/healthz', timeout=1) ... PY`
  - auto-start smoke 종료 후 `not healthy: URLError`를 확인했습니다. wrapper가 직접 시작한 서버는 정리된 상태입니다.
- `bash -lc '<mock app.web를 8879에 먼저 띄운 뒤 make e2e-test 실행>'`
  - 기존 서버 재사용 경로 준비 단계에서 실패했습니다.
  - `python3 -m app.web --host 127.0.0.1 --port 8879`가 `PermissionError: [Errno 1] Operation not permitted`로 종료되어 `make e2e-test`까지 도달하지 못했습니다.
- `timeout 5s env -u LOCAL_AI_MODEL_PROVIDER -u LOCAL_AI_OLLAMA_MODEL LOCAL_AI_MODEL_PROVIDER=mock LOCAL_AI_OLLAMA_MODEL= LOCAL_AI_MOCK_STREAM_DELAY_MS=10 LOCAL_AI_SQLITE_DB_PATH=/tmp/projecth-direct-e2e.db python3 -m app.web --host 127.0.0.1 --port 8879`
  - 같은 `PermissionError: [Errno 1] Operation not permitted`로 실패했습니다.
- `e2e/start-server.sh bash -lc 'sleep 900'`
  - existing-server 경로를 만들기 위한 장기 서버 준비 시도였으나, 현재 sandbox에서 새 socket 생성이 막혀 같은 `PermissionError`로 실패했습니다.

## 남은 리스크
- existing-server 재사용 경로의 full `make e2e-test`는 실행하지 못했습니다. 현재 sandbox가 새 socket 생성 자체를 막아 healthy 기존 서버를 준비할 수 없었습니다.
- `make e2e-test` auto-start full smoke는 통과했지만, 별도 환경에서 이미 healthy한 `app.web`가 떠 있는 상태의 재사용 경로는 verify lane에서 다시 확인해야 합니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, 기존 미추적 `work/`/`verify/` 파일들은 이번 변경 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
