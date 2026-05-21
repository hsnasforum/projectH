# 2026-05-21 local socket guard consumer placement tests 검증

## 검증 대상

- `work/5/21/2026-05-21-local-socket-guard-consumer-placement-tests.md`
- `verify/5/21/2026-05-21-local-socket-guard-socket-free-unit-tests.md`
- `.pipeline/implement_handoff.md#2080`

## 변경 파일

- `verify/5/21/2026-05-21-local-socket-guard-consumer-placement-tests.md`
- 이 검증 단계는 코드, 테스트, 제품 문서, `/work`, `.pipeline/operator_request.md`, `.pipeline/advisory_request.md`를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill

- `round-handoff`: 최신 `/work`를 코드 truth와 재실행 결과에 대조하고 다음 control 전 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 advisory 비활성 조건에서 다음 safe local slice를 고르는 데 사용했다.

## 실행한 확인

- `sed -n '1,260p' tests/test_local_socket_guard.py`
  - 통과. `ast`와 local source read로 `tests/test_web_app.py` direct `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` test methods의 `_requires_local_loopback_socket` decorator 유지와 `HTTPIntegrationBase.setUp()`의 skip-before-server-create 순서를 검증하는 테스트가 추가된 것을 확인했다.
- `python3 -m py_compile tests/test_local_socket_guard.py`
  - 통과. 출력 없이 종료했다.
- `python3 -m unittest -v tests.test_local_socket_guard`
  - 통과. `Ran 7 tests in 0.608s`, `OK`.
- `git diff --check -- tests/test_local_socket_guard.py work/5/21/ verify/5/21/ .pipeline/implement_handoff.md`
  - 통과. 출력 없이 종료했다.
- `git diff --check --no-index -- /dev/null tests/test_local_socket_guard.py`
  - 통과. `--no-index` 특성상 diff-present로 exit code 1을 반환했지만 출력은 없었고, untracked test file의 공백 오류는 없었다.

## 판단

- 최신 `/work`의 핵심 주장은 현재 코드와 재실행 결과에 부합한다.
- shared local socket guard의 소비자 placement는 이제 실제 socket 없이 검증된다.
- `tests/local_socket_guard.py`, `tests/test_web_app.py`, `tests/test_http_integration.py`, production code는 이번 구현에서 변경되지 않았다.
- 현재 lane은 local loopback socket unavailable 상태로 남아 있으므로 live socket-bound web_app/http integration behavior나 live `ResourceWarning` clearance는 이번 검증 범위에서 확정하지 않는다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 실행하지 않은 확인

- `python3 -W always::ResourceWarning -m unittest -v tests.test_http_integration`는 이번 consumer-placement 검증에서는 재실행하지 않았다. 직전 verify에서 같은 lane이 `OK (skipped=25)` 환경-held임을 확인했고, 이번 변경은 live socket-bound 경로를 건드리지 않았다.
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.
- release-ready, full-smoke-pass, publication-ready는 주장하지 않는다.

## 남은 확인과 위험

- `local_socket_guard_auto_held`: 현재 lane의 local loopback socket unavailable 상태 때문에 socket-bound integration tests는 계속 local verification-held 상태다.
- 소비자 placement는 고정됐지만, `tests/test_web_app.py`가 file-local guard를 다시 만들지 않고 shared helper import를 유지하는지, `tests/test_http_integration.py`가 shared helper import를 유지하는지는 별도 socket-free regression으로 아직 고정하지 않았다.
- dirty bundle은 계속 크고 publication은 operator decision `HOLD_PUBLICATION` 상태다. commit, push, branch/PR publish, merge는 수행하지 않았다.

## 다음 control 판단

- `COUNCIL_DECISION: implement`
- `REASON_CODE: local_socket_guard_consumer_import_dedup_tests`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2081`
- `EVIDENCE: work/5/21/2026-05-21-local-socket-guard-consumer-placement-tests.md`
- `EVIDENCE: verify/5/21/2026-05-21-local-socket-guard-consumer-placement-tests.md`
- `EVIDENCE: tests/test_local_socket_guard.py`
- `EVIDENCE: tests/test_web_app.py`
- `EVIDENCE: tests/test_http_integration.py`
- `REJECTED: operator_request` - live socket verification remains environment-held, but the next bounded action is deterministic local import/dedup regression coverage and not an operator-only boundary.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 current evidence에서 next safe local slice가 결정된다.
- 다음 safe local slice는 `tests/test_web_app.py`가 `tests.local_socket_guard.requires_local_loopback_socket`를 `_requires_local_loopback_socket`로 import하고 file-local loopback guard definitions를 다시 만들지 않는지, 그리고 `tests/test_http_integration.py`가 shared `skip_unless_local_loopback_socket` import를 유지하는지를 socket-free AST regression test로 고정하는 것이다.
