# 2026-05-20 controller route family local evidence aggregate

## 변경 파일
- `work/5/20/2026-05-20-controller-route-family-local-evidence-aggregate.md`

## 사용 skill
- `work-log-closeout`: evidence-only implement 라운드의 실제 실행 명령, 변경 파일, 남은 리스크를 한국어 `/work` closeout 형식으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2070`가 controller runtime route docs truth-sync 이후 누적 controller route-family local evidence를 socket-free aggregate로 재확인하라고 지시했다.
- 최신 docs truth-sync는 이미 `/api/runtime/status`의 `runtime_snapshot` backfill, monitor/agent-inspector/capture-tail read routes, POST runtime action routes, `/api/runtime/send-input` validation/fail-closed behavior, controller shell/asset JSON 404 boundary를 문서화했다.
- 이번 라운드는 해당 누적 route-family 변경을 새 코드 변경 없이 로컬 단위 검증으로 다시 묶어 확인하는 evidence-only slice였다.

## 핵심 변경
- production code, test, docs는 수정하지 않았다.
- `controller/server.py`와 `tests/test_controller_server.py` compile을 확인했다.
- `tests.test_controller_server` socket-free aggregate가 58개 test 통과로 controller route-family behavior를 다시 확인했다.
- 기존 dirty tree의 controller/runtime/reviewed-memory 변경은 되돌리거나 정리하지 않았다.
- commit, push, branch/PR publication, merge, release는 수행하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md`
  - 통과. handoff SHA가 `7a117236f5381fbe1d4d6e3fd3c44aaca55844ce3441c8f16abde03cb56df434`와 일치했다.
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 통과. `Ran 58 tests in 0.056s`, `OK`.
- `git diff --check -- controller/server.py tests/test_controller_server.py README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md work/5/20/ verify/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free compile/unit aggregate에 한정했다. Playwright, full controller smoke, broad e2e, long soak, socket-bound HTTP, runtime start/stop, `status --json`, `doctor --json`, `tmux` liveness checks는 실행하지 않았다.
- 작업 트리에는 이전 controller route-family 라운드의 `controller/server.py`, `tests/test_controller_server.py` dirty state와 더 큰 runtime/reviewed-memory dirty bundle이 남아 있다.
- 같은 문서 파일들에는 controller route/status docs truth-sync hunk 외에도 이전 reviewed-memory 관련 dirty hunk가 함께 남아 있으며, 이번 라운드는 그 제품 truth를 재판정하지 않았다.
- controller-smoke pass, full-smoke pass, release readiness, publication approval은 주장하지 않는다.
