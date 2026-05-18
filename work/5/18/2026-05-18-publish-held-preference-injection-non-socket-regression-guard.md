# 2026-05-18 publish held preference injection non-socket regression guard

## 변경 파일

- `work/5/18/2026-05-18-publish-held-preference-injection-non-socket-regression-guard.md`

## 사용 skill

- `work-log-closeout`: 실제 실행한 preference unit guard, 정적 검사, 남은 browser-held 리스크를 표준 `/work` 형식으로 기록하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1933` handoff는 publication held 상태에서 web-smoke mock summary prefix drift와 직접 연결된 preference-injection unit guard를 non-socket으로 실행하라고 지시했습니다.
- browser verification은 직전 흐름에서 local webServer socket permission denial 때문에 `local_socket_guard_auto_held`로 남아 있으므로, 이번 slice는 Playwright나 local webServer 없이 실행 가능한 preference unit 범위만 확인했습니다.
- 실패가 있을 때만 preference-injection source/test scope에서 deterministic drift를 수정하는 조건이었고, 대상 unit이 모두 통과해 source/test 수정은 필요하지 않았습니다.

## 핵심 변경

- `python3 -m unittest -v tests.test_preference_injection tests.test_preference_handler`를 실행했고, 37개 test가 모두 통과했습니다.
- 실패가 없어 `tests/test_preference_injection.py`, `tests/test_preference_handler.py`, `core/agent_loop.py`, `app/handlers/preferences.py`, `app/handlers/chat.py`, `storage/preference_store.py`, `storage/sqlite/preference.py`, `storage/session_store.py`, `storage/preference_utils.py`는 수정하지 않았습니다.
- `node --check e2e/tests/web-smoke.spec.mjs`를 실행해 직전 browser smoke fixture/test 파일의 정적 문법 상태를 확인했습니다.
- 기존 dirty 변경인 `controller/js/cozy.js`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_controller_server.py`는 그대로 보존했습니다.
- Playwright, `make e2e-test`, local webServer startup, runtime start/stop/restart, socket/tmux 명령은 실행하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication은 수행하지 않았고 publication은 계속 held 상태입니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - `f509bb2059b19a198250e4bc5c373daffab18216f80ca075f8c24bd9350ca4c7  .pipeline/implement_handoff.md`로 handoff SHA가 일치함을 확인했습니다.
- `python3 -m unittest -v tests.test_preference_injection tests.test_preference_handler`
  - `Ran 37 tests ... OK`로 통과했습니다.
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 출력 없이 통과했습니다.
- `git diff --check -- tests/test_preference_injection.py tests/test_preference_handler.py core/agent_loop.py app/handlers/preferences.py app/handlers/chat.py storage/preference_store.py storage/sqlite/preference.py storage/session_store.py storage/preference_utils.py e2e/tests/web-smoke.spec.mjs work/5/18/2026-05-18-publish-held-preference-injection-non-socket-regression-guard.md`
  - 출력 없이 통과했습니다.
- `git diff --no-index --check -- /dev/null work/5/18/2026-05-18-publish-held-preference-injection-non-socket-regression-guard.md`
  - 출력 없음. `--no-index` exit code 1은 `/dev/null`과 새 파일의 내용 차이로 발생할 수 있어 whitespace-check pass signal로 해석했습니다.
- `git status --short -- tests/test_preference_injection.py tests/test_preference_handler.py core/agent_loop.py app/handlers/preferences.py app/handlers/chat.py storage/preference_store.py storage/sqlite/preference.py storage/session_store.py storage/preference_utils.py e2e/tests/web-smoke.spec.mjs work/5/18/2026-05-18-publish-held-preference-injection-non-socket-regression-guard.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - 출력: `M e2e/tests/web-smoke.spec.mjs`, `?? work/5/18/2026-05-18-publish-held-preference-injection-non-socket-regression-guard.md`

## 남은 리스크

- browser verification은 여전히 `local_socket_guard_auto_held`입니다. socket-capable 환경에서 관련 web-smoke rerun이 필요합니다.
- 이번 slice는 non-socket preference unit/static guard만 완료했으므로 full-smoke pass, release-ready, publication-ready를 주장하지 않습니다.
- 기존 dirty source/test 변경은 유지됩니다. stash apply/pop/drop/clear/branch/store/rewrite/discard는 수행하지 않았습니다.
