# 2026-05-18 publish held controller non-socket regression guard

## 변경 파일

- `work/5/18/2026-05-18-publish-held-controller-non-socket-regression-guard.md`

## 사용 skill

- `e2e-smoke-triage`: controller smoke failure 계열의 browser-held 상태에서 non-socket controller regression guard로 검증 범위를 좁히는 데 사용했습니다.
- `work-log-closeout`: 실제 실행한 검사, 수정하지 않은 파일, 남은 browser 검증 리스크를 표준 `/work` 형식으로 기록하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1932` handoff는 publication held 상태에서 `tests.test_controller_server` 전체 모듈을 Playwright/webServer/socket/tmux/runtime 명령 없이 실행하라고 지시했습니다.
- 직전 slice에서 targeted controller unit contract는 통과 상태로 돌아왔지만, 같은 controller static/server contract 전체가 흔들리지 않았는지 non-socket guard가 필요했습니다.
- 이번 slice의 목적은 browser smoke pass를 주장하는 것이 아니라, socket 없이 실행 가능한 controller unittest regression guard를 완료하는 것입니다.

## 핵심 변경

- `python3 -m unittest -v tests.test_controller_server`를 실행했고, 28개 test가 모두 통과했습니다.
- 실패가 없어 `tests/test_controller_server.py`, `controller/js/cozy.js`, `controller/server.py`, `controller/index.html`, `controller/css/office.css`는 이번 slice에서 추가 수정하지 않았습니다.
- 직전 slice의 dirty 변경인 `controller/js/cozy.js`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_controller_server.py`는 그대로 보존했습니다.
- Playwright, `make e2e-test`, local webServer startup, runtime start/stop/restart, socket/tmux 명령은 실행하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication은 수행하지 않았고 publication은 계속 held 상태입니다.

## 검증

- `python3 -m unittest -v tests.test_controller_server`
  - `Ran 28 tests ... OK`로 통과했습니다.
- `node --check controller/js/cozy.js`
  - 출력 없이 통과했습니다.
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 출력 없이 통과했습니다.
- `git diff --check -- tests/test_controller_server.py controller/js/cozy.js controller/server.py controller/index.html controller/css/office.css e2e/tests/web-smoke.spec.mjs work/5/18/2026-05-18-publish-held-controller-non-socket-regression-guard.md`
  - 출력 없이 통과했습니다.
- `git diff --no-index --check -- /dev/null work/5/18/2026-05-18-publish-held-controller-non-socket-regression-guard.md`
  - 출력 없음. `--no-index` exit code 1은 `/dev/null`과 새 파일의 내용 차이로 발생할 수 있어 whitespace-check pass signal로 해석했습니다.
- `git status --short -- tests/test_controller_server.py controller/js/cozy.js controller/server.py controller/index.html controller/css/office.css e2e/tests/web-smoke.spec.mjs work/5/18/2026-05-18-publish-held-controller-non-socket-regression-guard.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - 출력: `M controller/js/cozy.js`, `M e2e/tests/web-smoke.spec.mjs`, `M tests/test_controller_server.py`, `?? work/5/18/2026-05-18-publish-held-controller-non-socket-regression-guard.md`

## 남은 리스크

- browser verification은 여전히 `local_socket_guard_auto_held`입니다. socket-capable 환경에서 controller focused smoke와 관련 web-smoke rerun이 필요합니다.
- 이번 slice는 non-socket controller unittest/static guard만 완료했으므로 full-smoke pass, release-ready, publication-ready를 주장하지 않습니다.
- `controller/js/cozy.js`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_controller_server.py`의 기존 dirty 변경은 유지됩니다.
- dirty tree는 그대로 보존했습니다. stash apply/pop/drop/clear/branch/store/rewrite/discard는 수행하지 않았습니다.
