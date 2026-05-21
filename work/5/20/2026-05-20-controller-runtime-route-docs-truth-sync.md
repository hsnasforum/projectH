# 2026-05-20 controller runtime route docs truth sync

## 변경 파일
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/PRODUCT_SPEC.md`
- `work/5/20/2026-05-20-controller-runtime-route-docs-truth-sync.md`

## 사용 skill
- `doc-sync`: controller runtime route/status 구현 truth와 제품/아키텍처/수용 기준 문서의 drift를 좁게 맞추기 위해 사용했다.
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2069`가 socket-free controller route guards와 route-test helper consolidation 이후 current controller runtime route/status documentation truth를 맞추라고 지시했다.
- 최근 controller route-family 작업으로 `/api/runtime/status`의 `runtime_snapshot` 보강, runtime monitor/agent-inspector/capture-tail JSON route, start/stop/restart POST route, `/api/runtime/send-input` fail-closed validation, controller shell/asset JSON 404 계약이 테스트로 고정되었지만 일부 문서에는 route 목록과 validation boundary가 덜 구체적으로 남아 있었다.

## 핵심 변경
- `README.md`의 internal pipeline controller API 목록에 `monitor-snapshot`, `agent-inspector`, `capture-tail` query shape, `runtime_snapshot` 보강, `send-input` fail-closed validation을 반영했다.
- `docs/ARCHITECTURE.md`의 Internal Operator Tooling Note에 controller JSON route boundary와 asset fail-closed behavior를 추가했다.
- `docs/ACCEPTANCE_CRITERIA.md`에 socket-free controller unit coverage가 고정하는 internal JSON route contract를 현재 수용 기준 caveat 안에서 분리해 명시했다.
- `docs/PRODUCT_SPEC.md`의 release-gate 밖 internal tooling 목록에 `runtime_snapshot` backfill과 bounded controller runtime JSON route set, `send-input` validation boundary를 추가했다.
- 코드와 테스트는 변경하지 않았다.

## 검증
- `rg -n "controller|runtime_snapshot|/api/runtime/status|/api/runtime/send-input|monitor-snapshot|agent-inspector|capture-tail" README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
  - 통과. 네 문서에서 controller route/status truth 문구가 검색됨을 확인했다.
- `git diff --check -- README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 docs-only truth-sync에 한정했다. `python3 -m unittest`, Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 작업 트리에는 이전 controller route-family 라운드의 `controller/server.py`, `tests/test_controller_server.py` dirty state가 남아 있다. 이번 라운드에서는 해당 코드/테스트 파일을 수정하지 않았다.
- 같은 문서 파일들에는 이전 라운드에서 생긴 reviewed-memory 관련 dirty hunks도 함께 남아 있다. 이번 라운드는 controller runtime route/status 문구만 의도적으로 동기화했고, 그 외 문서 변경은 검증하거나 정리하지 않았다.
- controller-smoke pass, full-smoke pass, release readiness는 주장하지 않는다.
