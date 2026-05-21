# 2026-05-21 http integration socket-free cleanup guard 검증

## 검증 대상

- `work/5/21/2026-05-21-http-integration-socket-free-cleanup-guard.md`
- `verify/5/21/2026-05-21-shared-local-socket-test-guard.md`
- `.pipeline/implement_handoff.md#2078`

## 변경 파일

- `verify/5/21/2026-05-21-http-integration-socket-free-cleanup-guard.md`
- 이 검증 단계는 코드, 테스트, 제품 문서, `/work`, `.pipeline/operator_request.md`, `.pipeline/advisory_request.md`를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill

- `round-handoff`: 최신 `/work`를 코드 truth와 재실행 결과에 대조하고 다음 control 전 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 advisory 비활성 조건에서 다음 safe local slice를 고르는 데 사용했다.

## 실행한 확인

- `sed -n '45,180p' tests/test_http_integration.py`
  - 통과. `HTTPIntegrationBase.tearDown()`이 `getattr`으로 `server`, `_server_thread`, `_tmpdir`를 읽고, `shutdown()`, `join(timeout=5)`, `server_close()`, `cleanup()` 순서로 cleanup을 시도하는 것을 확인했다.
  - `TestHTTPIntegrationBaseCleanup.test_tear_down_closes_server_resources_without_socket`가 fake server/thread/tempdir으로 socket 없이 cleanup 호출 순서를 검증하는 것도 확인했다.
- `python3 -m py_compile tests/test_http_integration.py`
  - 통과. 출력 없이 종료했다.
- `python3 -m unittest -v tests.test_http_integration.TestHTTPIntegrationBaseCleanup`
  - 통과. `Ran 1 test in 0.000s`, `OK`.
- `python3 -W always::ResourceWarning -m unittest -v tests.test_http_integration`
  - 통과. `Ran 26 tests in 0.004s`, `OK (skipped=25)`.
  - 현재 lane에서는 `local loopback socket unavailable in this environment`로 socket-bound 25개 integration tests가 skip됐고, socket-free cleanup test 1개만 실행됐다.
  - 출력에는 `ResourceWarning: unclosed <socket.socket ...>` 라인이 없었지만, live socket-bound 경로가 실행되지 않았으므로 live `ResourceWarning` clearance, full-smoke pass, release readiness는 주장하지 않는다.
- `git diff --check -- tests/test_http_integration.py work/5/21/ verify/5/21/ .pipeline/implement_handoff.md`
  - 통과. 출력 없이 종료했다.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-http-integration-socket-free-cleanup-guard.md`
  - 통과. `--no-index` 특성상 diff-present로 exit code 1을 반환했지만 출력은 없었고, untracked work note의 공백 오류는 없었다.
- `git status --short -- tests/local_socket_guard.py tests/test_http_integration.py tests/test_web_app.py work/5/21/ verify/5/21/ .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - 확인. 관련 dirty state는 `tests/test_http_integration.py`, `tests/test_web_app.py`, `tests/local_socket_guard.py`, `work/5/21/`, `verify/5/21/`에 한정된다. advisory/operator control 파일은 이번 검증에서 수정하지 않았다.

## 판단

- 최신 `/work`의 핵심 주장은 현재 코드와 재실행 결과에 부합한다.
- `HTTPIntegrationBase.tearDown()`은 이제 server socket을 `server_close()`로 닫는 cleanup path를 갖고, socket-free test가 그 호출 계약을 검증한다.
- live HTTP integration suite는 현재 lane의 local socket 불가로 환경-held 상태다. 따라서 이번 검증은 socket-bound HTTP behavior나 live server lifecycle의 경고 제거를 완료로 확정하지 않는다.
- production `LocalOnlyHTTPServer`, HTTP response shape, reviewed-memory behavior, product docs는 변경되지 않았다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 실행하지 않은 확인

- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.
- socket-capable 환경에서 `python3 -W always::ResourceWarning -m unittest -v tests.test_http_integration`가 26개를 모두 실제 실행하는지는 확인하지 못했다.
- release-ready, full-smoke-pass, publication-ready는 주장하지 않는다.

## 남은 확인과 위험

- `local_socket_guard_auto_held`: 현재 lane의 local loopback socket unavailable 상태 때문에 socket-bound integration tests가 skip된다. live `ResourceWarning` 제거는 socket-capable lane에서 재확인해야 한다.
- shared `tests/local_socket_guard.py`는 이번 연쇄의 핵심 helper가 됐지만, helper 자체의 success/failure/skip branch를 socket 없이 검증하는 단위 테스트는 아직 없다. 같은 incident family에서 다음 local risk reduction으로 적합하다.
- dirty bundle은 계속 크고 publication은 operator decision `HOLD_PUBLICATION` 상태다. commit, push, branch/PR publish, merge는 수행하지 않았다.

## 다음 control 판단

- `COUNCIL_DECISION: implement`
- `REASON_CODE: local_socket_guard_socket_free_unit_tests`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2079`
- `EVIDENCE: work/5/21/2026-05-21-http-integration-socket-free-cleanup-guard.md`
- `EVIDENCE: verify/5/21/2026-05-21-http-integration-socket-free-cleanup-guard.md`
- `EVIDENCE: tests/local_socket_guard.py`
- `REJECTED: operator_request` - local socket unavailability leaves a live verification gap, but the next bounded action is socket-free helper coverage and does not require destructive action, credential/auth, approval-record repair, truth-sync repair, merge, release, or external publication.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 current evidence에서 next safe local slice가 결정된다.
- 다음 safe local slice는 `tests/local_socket_guard.py`의 availability probe와 skip helper behavior를 socket-free unittest로 고정해, local socket unavailable 환경에서도 같은 guard family를 재현 가능하게 만드는 것이다.
