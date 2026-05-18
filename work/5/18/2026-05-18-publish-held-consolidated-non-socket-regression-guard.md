# 2026-05-18 publish held consolidated non-socket regression guard

## 변경 파일

- `work/5/18/2026-05-18-publish-held-consolidated-non-socket-regression-guard.md`

## 사용 skill

- `work-log-closeout`: 통합 non-socket 회귀 guard의 실제 실행 결과와 남은 browser-held 리스크를 표준 `/work` 형식으로 기록하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1934` handoff는 publication held 상태에서 현재 dirty source/test bundle을 하나의 non-socket regression guard로 확인하라고 지시했습니다.
- 직전 개별 guard들은 controller, preference-injection, web-smoke static 범위를 각각 확인했지만, 이번 slice는 같은 bundle을 한 번에 묶어 재확인하는 목적입니다.
- focused Playwright는 local webServer socket permission denial 때문에 `local_socket_guard_auto_held`로 남아 있으므로, 이번 slice는 Playwright, local webServer, socket/tmux, runtime 명령 없이 실행 가능한 검사로 제한했습니다.

## 핵심 변경

- `python3 -m unittest -v tests.test_controller_server tests.test_preference_injection tests.test_preference_handler`를 실행했고, 65개 test가 모두 통과했습니다.
- `node --check controller/js/cozy.js`와 `node --check e2e/tests/web-smoke.spec.mjs`가 출력 없이 통과했습니다.
- 실패가 없어 `controller/js/cozy.js`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_controller_server.py` 및 preference 관련 source/test 파일은 이번 slice에서 추가 수정하지 않았습니다.
- 기존 dirty 변경인 `controller/js/cozy.js`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_controller_server.py`와 기존 untracked `/work`/`/verify` records는 그대로 보존했습니다.
- Playwright, `make e2e-test`, local webServer startup, runtime start/stop/restart, socket/tmux 명령은 실행하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication은 수행하지 않았고 publication은 계속 held 상태입니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - `61386841be8d8fd8915d8aba1e91ccc09849577dcbc7ebf1e2890f855a334ba2  .pipeline/implement_handoff.md`로 handoff SHA가 일치함을 확인했습니다.
- `python3 -m unittest -v tests.test_controller_server tests.test_preference_injection tests.test_preference_handler`
  - `Ran 65 tests ... OK`로 통과했습니다.
- `node --check controller/js/cozy.js`
  - 출력 없이 통과했습니다.
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 출력 없이 통과했습니다.
- `git diff --check -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py tests/test_preference_injection.py tests/test_preference_handler.py core/agent_loop.py app/handlers/preferences.py app/handlers/chat.py storage/preference_store.py storage/sqlite/preference.py storage/session_store.py storage/preference_utils.py work/5/18/2026-05-18-publish-held-consolidated-non-socket-regression-guard.md`
  - 출력 없이 통과했습니다.
- `git diff --no-index --check -- /dev/null work/5/18/2026-05-18-publish-held-consolidated-non-socket-regression-guard.md`
  - 출력 없음. `--no-index` exit code 1은 `/dev/null`과 새 파일의 내용 차이로 발생할 수 있어 whitespace-check pass signal로 해석했습니다.
- `git status --short -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py tests/test_preference_injection.py tests/test_preference_handler.py core/agent_loop.py app/handlers/preferences.py app/handlers/chat.py storage/preference_store.py storage/sqlite/preference.py storage/session_store.py storage/preference_utils.py work/5/18/2026-05-18-publish-held-consolidated-non-socket-regression-guard.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - 출력: `M controller/js/cozy.js`, `M e2e/tests/web-smoke.spec.mjs`, `M tests/test_controller_server.py`, `?? work/5/18/2026-05-18-publish-held-consolidated-non-socket-regression-guard.md`

## 남은 리스크

- browser verification은 여전히 `local_socket_guard_auto_held`입니다. socket-capable 환경에서 관련 controller/web-smoke focused rerun이 필요합니다.
- 이번 slice는 non-socket unit/static guard만 완료했으므로 full-smoke pass, release-ready, publication-ready를 주장하지 않습니다.
- 기존 dirty source/test 변경은 유지됩니다. stash apply/pop/drop/clear/branch/store/rewrite/discard는 수행하지 않았습니다.
