# 2026-05-18 publish held dirty bundle truth manifest

## 변경 파일

- `work/5/18/2026-05-18-publish-held-dirty-bundle-truth-manifest.md`

## 사용 skill

- `work-log-closeout`: 현재 dirty source/test bundle, 이미 기록된 non-socket 검증 truth, browser-held 잔여 리스크를 표준 `/work` 형식으로 정리하는 데 사용했습니다.

## 변경 이유

- `CONTROL_SEQ: 1935` handoff는 publication held 상태에서 현재 dirty bundle의 실제 diff, non-socket check truth, browser-held residual risk를 하나의 bounded docs-only manifest로 정리하라고 지시했습니다.
- 같은 publish-held smoke/controller 회복 체인에서 개별 non-socket guard와 docs-only verify가 반복됐으므로, 이번 slice는 source/test를 더 수정하지 않고 현재 local truth를 한 파일에 묶는 것이 목적입니다.
- Playwright와 full smoke는 local webServer socket permission denial 때문에 `local_socket_guard_auto_held`로 남아 있어, 이번 slice에서는 socket을 여는 검증을 실행하지 않았습니다.

## 핵심 변경

- source/test 파일은 수정하지 않았고, `/work` manifest 하나만 추가했습니다.
- 현재 dirty source/test bundle은 `controller/js/cozy.js`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_controller_server.py` 3개입니다.
- `git diff --stat -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py` 기준 dirty bundle은 3개 파일, 49 insertions, 21 deletions입니다.
- `controller/js/cozy.js`는 `activeRoundLaneName`을 추가하고, active round role owner lane이 snapshot상 `ready`일 때 `effectiveLaneState`가 `working`으로 보이도록 합니다. 기본 runtime truth가 lane state라는 guard는 유지됩니다.
- `e2e/tests/web-smoke.spec.mjs`는 active preference가 붙은 mock summary prefix를 허용하고, approval preview expectation을 regex로 정리하며, `수정`/`활성화` locator ambiguity를 좁힙니다.
- `tests/test_controller_server.py`는 controller state unit contract를 새 `activeRoundLaneName`/`effectiveLaneState` behavior에 맞춰 확인합니다.
- 최신 `/work` 기록 기준 non-socket guard는 통과 상태입니다: `python3 -m unittest -v tests.test_controller_server tests.test_preference_injection tests.test_preference_handler`는 `Ran 65 tests ... OK`, `node --check controller/js/cozy.js`와 `node --check e2e/tests/web-smoke.spec.mjs`는 출력 없이 통과했습니다.
- browser/full-smoke는 여전히 `local_socket_guard_auto_held`입니다. release-ready, publication-ready, full-smoke-pass는 주장하지 않습니다.
- commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication은 수행하지 않았고 publication은 계속 held 상태입니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - `05e96b3aa4e9f2cba1907c0a0e090b176dc7b9ab240e27fae53728025a7852d3  .pipeline/implement_handoff.md`로 handoff SHA가 일치함을 확인했습니다.
- `git diff -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py`
  - 현재 dirty source/test bundle의 실제 diff를 확인했습니다.
- `git diff --stat -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py`
  - 출력: `3 files changed, 49 insertions(+), 21 deletions(-)`
- `git status --short -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py work/5/18/2026-05-18-publish-held-dirty-bundle-truth-manifest.md work/5/18/2026-05-18-publish-held-consolidated-non-socket-regression-guard.md work/5/18/2026-05-18-publish-held-preference-injection-non-socket-regression-guard.md work/5/18/2026-05-18-publish-held-controller-non-socket-regression-guard.md work/5/18/2026-05-18-publish-held-controller-state-regression-contract-sync.md work/5/18/2026-05-18-publish-held-non-socket-smoke-artifact-triage.md verify/5/18/2026-05-18-runtime-dispatch-stall-clear-retry.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - 출력은 기존 dirty source/test 3개 파일, 최신 publish-held `/work` records, 이 `/verify` 상태를 확인했습니다.
- `git diff --check -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py work/5/18/2026-05-18-publish-held-dirty-bundle-truth-manifest.md`
  - 출력 없이 통과했습니다.
- `git diff --no-index --check -- /dev/null work/5/18/2026-05-18-publish-held-dirty-bundle-truth-manifest.md`
  - 출력 없음. `--no-index` exit code 1은 `/dev/null`과 새 파일의 내용 차이로 발생할 수 있어 whitespace-check pass signal로 해석했습니다.
- `git status --short -- controller/js/cozy.js e2e/tests/web-smoke.spec.mjs tests/test_controller_server.py work/5/18/2026-05-18-publish-held-dirty-bundle-truth-manifest.md work/5/18/2026-05-18-publish-held-consolidated-non-socket-regression-guard.md work/5/18/2026-05-18-publish-held-preference-injection-non-socket-regression-guard.md work/5/18/2026-05-18-publish-held-controller-non-socket-regression-guard.md work/5/18/2026-05-18-publish-held-controller-state-regression-contract-sync.md work/5/18/2026-05-18-publish-held-non-socket-smoke-artifact-triage.md verify/5/18/2026-05-18-runtime-dispatch-stall-clear-retry.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - 출력: `M controller/js/cozy.js`, `M e2e/tests/web-smoke.spec.mjs`, `M tests/test_controller_server.py`, `?? verify/5/18/2026-05-18-runtime-dispatch-stall-clear-retry.md`, `?? work/5/18/2026-05-18-publish-held-consolidated-non-socket-regression-guard.md`, `?? work/5/18/2026-05-18-publish-held-controller-non-socket-regression-guard.md`, `?? work/5/18/2026-05-18-publish-held-controller-state-regression-contract-sync.md`, `?? work/5/18/2026-05-18-publish-held-dirty-bundle-truth-manifest.md`, `?? work/5/18/2026-05-18-publish-held-non-socket-smoke-artifact-triage.md`, `?? work/5/18/2026-05-18-publish-held-preference-injection-non-socket-regression-guard.md`

## 남은 리스크

- 이번 slice는 docs-only manifest 작성이므로 unit, node syntax, Playwright, `make e2e-test`, local webServer startup, runtime/tmux/socket 명령을 새로 실행하지 않았습니다.
- browser verification은 여전히 `local_socket_guard_auto_held`입니다. socket-capable 환경에서 관련 controller/web-smoke focused rerun이 필요합니다.
- 이번 manifest는 full-smoke pass, release-ready, publication-ready를 주장하지 않습니다.
- 기존 dirty source/test 변경은 유지됩니다. stash apply/pop/drop/clear/branch/store/rewrite/discard는 수행하지 않았습니다.
