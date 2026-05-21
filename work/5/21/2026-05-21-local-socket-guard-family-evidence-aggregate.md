# 2026-05-21 local socket guard family evidence aggregate

## 변경 파일

- `work/5/21/2026-05-21-local-socket-guard-family-evidence-aggregate.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 검증 결과, skip/held 상태, 남은 리스크를 `/work` 형식으로 기록하는 데 사용했다.

## 변경 이유

- `.pipeline/implement_handoff.md#2082`는 local socket guard helper, consumer placement, consumer import/dedup 보강 뒤 같은 failure family를 한 번에 재검증하고 aggregate evidence로 남기도록 요구했다.
- 이번 라운드는 source/test/product docs 변경 없이 post-fix evidence만 갱신하는 슬라이스다.
- 현재 lane은 local loopback socket unavailable 상태를 계속 보이므로, socket-bound 테스트 skip을 pass와 분리해 기록해야 한다.

## 핵심 변경

- 소스, 테스트, 제품 문서, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 변경하지 않았다.
- local socket guard 관련 compile/unit checks와 web/http aggregate checks를 재실행했다.
- socket-free helper/import/cleanup 검증은 통과로 기록했다.
- socket-bound HTTP/web handler 경로는 `local loopback socket unavailable in this environment` skip으로 기록하고 `local_socket_guard_auto_held`로 분리했다.
- live socket behavior, full smoke, release readiness, publication readiness는 주장하지 않았다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `5ceb846a9bb27e1c481995b1146eb90644832ba87a360ca55c0198d422d819ac`와 일치했다.
- `python3 -m py_compile tests/local_socket_guard.py tests/test_local_socket_guard.py tests/test_web_app.py tests/test_http_integration.py`
  - 통과: 출력 없이 종료했다.
- `python3 -m unittest -v tests.test_local_socket_guard`
  - 통과: `Ran 10 tests in 1.116s`, `OK`.
- `python3 -m unittest -v tests.test_http_integration.TestHTTPIntegrationBaseCleanup`
  - 통과: `Ran 1 test in 0.000s`, `OK`.
- `python3 -W error::ResourceWarning -m unittest -v tests.test_http_integration`
  - 환경 held: `Ran 26 tests in 0.001s`, `OK (skipped=25)`.
  - 25개 socket-bound tests는 모두 `local loopback socket unavailable in this environment` 사유로 skip됐다.
  - `TestHTTPIntegrationBaseCleanup.test_tear_down_closes_server_resources_without_socket` 1개는 통과했다.
  - `ResourceWarning` failure는 없었지만, socket-bound live behavior는 이 lane에서 검증되지 않았다.
- `python3 -m unittest -v tests.test_web_app`
  - 1차 실행은 도구 세션에서 최종 exit code를 회수하지 못해 aggregate 판정에는 사용하지 않았다.
- `timeout 900 bash -lc 'python3 -m unittest -v tests.test_web_app > /tmp/projecth-test-web-app-2082.log 2>&1'`
  - 통과: exit code 0.
  - 로그 요약: `Ran 334 tests in 29.559s`, `OK (skipped=13)`.
  - 13개 direct HTTP/web handler socket-bound tests는 모두 `local loopback socket unavailable in this environment` 사유로 skip됐다.
- `git diff --check -- tests/local_socket_guard.py tests/test_local_socket_guard.py tests/test_web_app.py tests/test_http_integration.py work/5/21/`
  - closeout 작성 전 통과: 출력 없이 종료했다.
  - closeout 작성 후 통과: 출력 없이 종료했다.

## 남은 리스크

- `local_socket_guard_auto_held`: 현재 lane에서 local loopback socket이 unavailable이므로 socket-bound HTTP/web handler live behavior는 검증되지 않았다.
- `tests.test_http_integration`의 25개 socket-bound tests와 `tests.test_web_app`의 13개 direct socket-bound tests는 environment-held skip이며 live socket pass가 아니다.
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` liveness checks는 handoff 범위 밖이라 실행하지 않았다.
- commit, push, branch/PR publish, merge, release, publication readiness claim은 수행하지 않았다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, 다음 handoff/control은 작성하지 않았다.
