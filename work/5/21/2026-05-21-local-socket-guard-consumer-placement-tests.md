# 2026-05-21 local socket guard consumer placement tests

## 변경 파일

- `tests/test_local_socket_guard.py`
- `work/5/21/2026-05-21-local-socket-guard-consumer-placement-tests.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 검증 결과, 남은 리스크를 `/work` 형식으로 기록하는 데 사용했다.

## 변경 이유

- `.pipeline/implement_handoff.md#2080`은 shared local socket guard가 현재 소비자 위치에 계속 적용되는지 live socket 없이 검증하도록 요구했다.
- 현재 lane은 local loopback socket unavailable 상태라 socket-bound web/app integration tests가 skip될 수 있으므로, guard placement 자체를 deterministic AST test로 고정할 필요가 있었다.
- 이번 라운드는 test-only regression coverage이며 production HTTP behavior, shared helper API, 기존 소비자 파일은 변경하지 않는다.

## 핵심 변경

- `tests/test_local_socket_guard.py`에 AST/source-read helper를 추가했다.
- `tests/test_web_app.py`에서 direct `LocalOnlyHTTPServer(("127.0.0.1", 0), service)`를 포함하는 test method가 `_requires_local_loopback_socket` decorator를 유지하는지 검증했다.
- `tests/test_http_integration.py`의 `HTTPIntegrationBase.setUp()`이 direct `LocalOnlyHTTPServer(("127.0.0.1", 0), self.service)` 생성 전에 `skip_unless_local_loopback_socket(self)`를 호출하는지 검증했다.
- 기존 helper behavior tests는 유지했고, `tests/local_socket_guard.py`, `tests/test_web_app.py`, `tests/test_http_integration.py`, production code는 변경하지 않았다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `507bda617ec0d14979088b51a421e286d5412d39ba75dd68270ab59843fd6f84`와 일치했다.
- `python3 -m py_compile tests/test_local_socket_guard.py`
  - 통과: 출력 없이 종료했다.
- `python3 -m unittest -v tests.test_local_socket_guard`
  - 통과: `Ran 7 tests in 0.636s`, `OK`.
- `git diff --check -- tests/test_local_socket_guard.py work/5/21/`
  - 통과: closeout 작성 전/후 모두 출력 없이 종료했다.
- `git diff --check --no-index -- /dev/null tests/test_local_socket_guard.py`
  - 통과: 출력 없이 `exit code 1`로 종료해, untracked test file의 diff-present 상태에서 공백 오류가 없음을 확인했다.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-local-socket-guard-consumer-placement-tests.md`
  - 통과: 출력 없이 `exit code 1`로 종료해, untracked work note의 diff-present 상태에서 공백 오류가 없음을 확인했다.

## 남은 리스크

- 이번 tests는 guard placement를 socket-free로 검증하지만, 현재 lane의 local socket unavailable 상태 때문에 live socket-bound web_app/http integration cases는 실행하지 않았다.
- live `ResourceWarning` clearance, Playwright, full controller smoke, broad e2e, runtime start/stop, `status --json`, `doctor --json`, `tmux`, release/publication 검증은 handoff 범위 밖이라 실행하지 않았다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, 다음 handoff/control은 작성하지 않았다.
