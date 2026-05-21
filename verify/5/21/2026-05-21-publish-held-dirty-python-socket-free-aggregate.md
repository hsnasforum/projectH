# 2026-05-21 publish held dirty Python socket-free aggregate 검증

## 검증 대상

- `work/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`
- `verify/5/21/2026-05-21-publish-held-worktree-autoclean-guard.md`
- `.pipeline/implement_handoff.md#2074`

## 변경 파일

- `verify/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`
- 이 검증 단계는 코드, 테스트, 제품 문서, `/work`, `.pipeline/operator_request.md`, `.pipeline/advisory_request.md`를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill

- `round-handoff`: 최신 `/work`를 직전 `/verify` 및 좁은 markdown/log evidence와 대조하고 다음 control 전 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 advisory 비활성 조건에서 다음 safe local slice를 고르는 데 사용했다.

## 실행한 확인

- `sed -n '1,260p' work/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`
  - 통과. 최신 `/work`는 코드/테스트/제품 문서를 수정하지 않고 closeout만 추가했으며, compile 통과와 unit aggregate의 socket permission blocker를 구분해 기록한다.
- `sed -n '1,260p' verify/5/21/2026-05-21-publish-held-worktree-autoclean-guard.md`
  - 통과. 직전 `/verify`는 publish held 상태, dirty bundle 잔존, browser/socket/live-runtime/release/publication gate held 상태를 확인한다.
- `git diff --check -- work/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md verify/5/21/2026-05-21-publish-held-worktree-autoclean-guard.md .pipeline/implement_handoff.md .pipeline/operator_request.md`
  - 통과.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`
  - whitespace 오류 없음. 파일이 untracked라 diff 존재로 종료코드 1이 반환되지만 출력은 없었다.
- `rg -n "^Ran 1086|FAILED \\(errors=13\\)|PermissionError|LocalOnlyHTTPServer" /tmp/projecth-unit-2074.log`
  - 통과. `/work`가 기록한 `Ran 1086 tests in 86.009s`, `FAILED (errors=13)`, `PermissionError: [Errno 1] Operation not permitted`, `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 실패 원인을 로그에서 확인했다.
- `rg -n "^ERROR:|^Ran 1086|FAILED \\(errors=13\\)" /tmp/projecth-unit-2074.log`
  - 통과. 실패한 13개 항목이 모두 `tests.test_web_app.WebAppServiceTest`의 HTTP handler/socket-bound 테스트임을 확인했다.
- `rg -n "LocalOnlyHTTPServer\\(\\(\\\"127\\.0\\.0\\.1\\\", 0\\)" tests/test_web_app.py`
  - 통과. `tests/test_web_app.py`에 direct `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 생성 지점 13개가 남아 있음을 확인했다.

## 판단

- 최신 `/work`의 핵심 주장은 현재 증거와 일치한다. 실제 코드/테스트 변경은 없었고, closeout만 새로 추가됐다.
- `py_compile` 통과 주장은 implement 단계의 기록으로 남아 있으며, 이번 verify는 변경 파일이 `/work`뿐이라는 scope hint에 따라 unit/Playwright를 재실행하지 않았다.
- unit aggregate 실패는 제품 코드 실패로 확정할 증거가 아니라 local sandbox의 loopback socket 생성 권한 거부다. 실패한 지점들은 `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 생성 중 `PermissionError: [Errno 1] Operation not permitted`로 닫혔다.
- 따라서 controller-smoke pass, full-smoke pass, release-ready, publication-ready, unit aggregate pass는 주장하지 않는다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 실행하지 않은 확인

- `python3 -m py_compile`, `python3 -m unittest`, Playwright, full controller smoke, broad e2e, long soak, socket-bound HTTP, runtime start/stop 검사는 실행하지 않았다.
- 이유: 최신 `/work`의 변경 파일은 `/work` closeout뿐이고, 검증 지시가 code/test/runtime 변경이 없으면 unit 또는 Playwright로 넓히지 말라고 제한했다.

## 남은 확인과 위험

- `tests.test_web_app`의 socket-bound HTTP handler 테스트 13개가 local sandbox 소켓 권한 거부에 직접 노출되어 있다.
- handoff #2074는 socket-free aggregate를 의도했지만 실제 aggregate에 socket-bound `tests.test_web_app` HTTP server cases가 포함되어 environment-held 실패로 끝났다.
- dirty bundle은 여전히 크며, browser/socket/live-runtime/release/publication gate도 held 상태다.
- publication은 operator decision `HOLD_PUBLICATION` 상태로 유지되며 commit, push, branch/PR publish, merge는 수행하지 않았다.

## 다음 control 판단

- `COUNCIL_DECISION: implement`
- `REASON_CODE: publish_held_web_app_socket_bound_unit_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2075`
- `EVIDENCE: work/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`
- `EVIDENCE: verify/5/21/2026-05-21-publish-held-worktree-autoclean-guard.md`
- `EVIDENCE: /tmp/projecth-unit-2074.log`
- `REJECTED: operator_request` - dispatcher runtime surface는 running/recovering이며, 실패 증거는 local socket permission 환경 mismatch다. destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 current evidence에서 next safe local slice가 결정된다.
- `REJECTED: rerun_same_unit_aggregate` - 같은 aggregate를 재실행해도 socket-bound HTTP cases가 동일한 환경-held 실패를 반복할 가능성이 높다.
- 다음 safe local slice는 `tests/test_web_app.py`의 direct `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` HTTP handler tests를 명시적인 local socket availability guard 아래에 두어, no-socket sandbox에서 code failure처럼 실패하지 않고 skipped/environment-held로 표면화되게 하는 것이다. product code는 건드리지 않고 test-only guard로 제한한다.
