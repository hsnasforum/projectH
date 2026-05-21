# 2026-05-21 http integration socket-free cleanup guard

## 변경 파일

- `tests/test_http_integration.py`
- `work/5/21/2026-05-21-http-integration-socket-free-cleanup-guard.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 검증 결과, 환경-held 리스크를 `/work` 형식으로 기록하는 데 사용했다.

## 변경 이유

- `.pipeline/implement_handoff.md#2078`은 #2077의 `local_socket_unavailable` block을 복구하기 위해 live loopback socket 없이도 `HTTPIntegrationBase.tearDown()` cleanup contract를 검증하도록 요구했다.
- 직전 검증에서 `tests.test_http_integration`은 통과했지만 `ResourceWarning: unclosed <socket.socket ...>` 경고가 재현됐고, 이후 현재 lane에서는 local loopback socket이 unavailable 상태라 socket-bound integration tests가 모두 skip됐다.
- 이번 라운드는 production HTTP behavior가 아니라 test lifecycle cleanup과 socket-free regression guard만 다룬다.

## 핵심 변경

- `HTTPIntegrationBase.tearDown()`이 missing attribute를 `getattr`으로 처리하도록 바꾸고, server가 있을 때 `shutdown()`과 thread `join(timeout=5)` 뒤 `server_close()`를 호출하도록 했다.
- `server_close()`와 tempdir `cleanup()`은 `finally` cleanup path에서 실행되도록 해 일반 성공 경로와 부분 setup 경로 모두에서 자원 정리를 시도한다.
- `TestHTTPIntegrationBaseCleanup.test_tear_down_closes_server_resources_without_socket`을 추가해 실제 socket bind 없이 fake server/thread/tempdir으로 `shutdown()`, `join(timeout=5)`, `server_close()`, `cleanup()` 호출 순서를 검증했다.
- 기존 HTTP integration assertions, shared socket guard API, production `LocalOnlyHTTPServer`, HTTP response shape는 변경하지 않았다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `5a1f13b04e14954a029172bba4bf7f9b94b8d4ce66d67973434785120b3336b3`와 일치했다.
- `python3 -m py_compile tests/test_http_integration.py`
  - 통과: 출력 없이 종료했다.
- `python3 -m unittest -v tests.test_http_integration.TestHTTPIntegrationBaseCleanup`
  - 통과: `Ran 1 test in 0.000s`, `OK`.
- `python3 -W always::ResourceWarning -m unittest -v tests.test_http_integration`
  - 통과: `Ran 26 tests in 0.003s`, `OK (skipped=25)`.
  - 현재 lane은 `local loopback socket unavailable in this environment` 상태라 socket-bound 25개 integration tests는 skip됐고, socket-free cleanup test 1개만 실행됐다.
  - 출력에는 `ResourceWarning: unclosed <socket.socket ...>` 라인이 없었지만, live socket-bound 경로가 실행되지 않았으므로 live `ResourceWarning` clearance나 release readiness로 주장하지 않는다.
- `git diff --check -- tests/test_http_integration.py work/5/21/`
  - 통과: closeout 작성 전/후 모두 출력 없이 종료했다.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-http-integration-socket-free-cleanup-guard.md`
  - 통과: 출력 없이 `exit code 1`로 종료해, untracked work note의 diff-present 상태에서 공백 오류가 없음을 확인했다.

## 남은 리스크

- `local_socket_guard_auto_held`: 현재 lane에서 local loopback socket이 unavailable이라 socket-bound HTTP integration cases는 실행되지 않았고, live `ResourceWarning` 제거는 직접 재현 검증하지 못했다.
- socket-free cleanup test는 `tearDown()`의 cleanup 호출 계약을 검증하지만, socket-capable 환경에서 전체 HTTP integration suite가 실제 server lifecycle을 경고 없이 통과하는지는 다음 verify 또는 socket-capable lane에서 확인해야 한다.
- Playwright, full controller smoke, broad e2e, runtime start/stop, `status --json`, `doctor --json`, `tmux`, release/publication 검증은 handoff 범위 밖이라 실행하지 않았다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, 다음 handoff/control은 작성하지 않았다.
