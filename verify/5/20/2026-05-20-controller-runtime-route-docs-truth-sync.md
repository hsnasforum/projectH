# 2026-05-20 controller runtime route docs truth sync 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-runtime-route-docs-truth-sync.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/PRODUCT_SPEC.md`

## 변경 파일
- 없음
- 이 검증 단계는 코드, 테스트, 제품 문서를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill
- `round-handoff`: 최신 `/work` closeout을 직전 `/verify`와 대조하고, handoff 범위에 맞는 좁은 검증을 rerun한 뒤 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 advisory/operator 없이 이어갈 수 있는 한 가지 다음 local slice를 고르는 데 사용했다.

## 실행한 확인
- `git diff -- README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
  - 통과. 이번 handoff가 주장한 controller runtime route/status 문구가 네 문서에 반영된 것을 확인했다.
  - 같은 문서 diff 안에 이전 reviewed-memory 관련 hunk도 함께 남아 있음을 확인했고, 이번 검증 범위에서는 controller runtime route/status truth-sync만 판정했다.
- `rg -n "controller|runtime_snapshot|/api/runtime/status|/api/runtime/send-input|monitor-snapshot|agent-inspector|capture-tail" README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
  - 통과. `runtime_snapshot`, `/api/runtime/status`, `/api/runtime/send-input`, `monitor-snapshot`, `agent-inspector`, `capture-tail` 관련 문구가 target docs에서 검색되었다.
- `git diff --check -- README.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md work/5/20/ verify/5/20/`
  - 통과.
- `git status --short`
  - 확인. 작업 트리는 여전히 큰 dirty bundle 상태이며, 이번 검증은 최신 docs-only truth-sync와 새 `/verify` 기록 범위만 판정했다.

## 판단
- 최신 `/work`의 docs-only 변경 주장은 현재 문서 diff와 일치한다.
- `README.md`의 internal pipeline controller API 목록은 `/api/runtime/status`, `/api/runtime/monitor-snapshot`, `/api/runtime/agent-inspector`, `/api/runtime/capture-tail`, `/api/runtime/start|stop|restart`, `/api/runtime/send-input`를 현재 controller-internal surface로 설명한다.
- `README.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/PRODUCT_SPEC.md`는 `/api/runtime/status`의 `runtime_snapshot` backfill, read-oriented monitor/agent-inspector/capture-tail routes, POST start/stop/restart action routes, `/api/runtime/send-input` object JSON validation/fail-closed behavior, local controller shell/static asset JSON 404 boundary를 현재 구현/테스트 truth와 같은 방향으로 설명한다.
- 문서들은 controller runtime route/status surface를 internal/operator tooling 및 release-gate 밖 경계로 유지하며, controller-smoke/full-smoke pass, release readiness, autonomous desktop-agent behavior, unsupported route behavior를 새로 주장하지 않는다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 실행하지 않은 확인
- `python3 -m unittest`, Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, socket-bound HTTP 검사는 실행하지 않았다.
- 이번 handoff의 `SCOPE_HINT`가 docs-only truth-sync였고 code/test/runtime 변경이 없었으므로 unit 또는 browser smoke로 넓히지 않았다.

## 남은 확인과 위험
- 작업 트리에는 이전 controller route-family 라운드의 `controller/server.py`, `tests/test_controller_server.py` dirty state와 더 큰 reviewed-memory/runtime dirty bundle이 계속 남아 있다.
- 같은 문서 파일에는 이번 controller route/status hunk 외에 이전 reviewed-memory 관련 dirty hunk가 함께 남아 있다. 이 검증에서는 해당 unrelated doc hunk의 제품 truth를 재판정하지 않았다.
- local socket guard 환경 제약, browser/socket/live-runtime/release/publication gate는 해소를 주장하지 않는다.
- controller-smoke pass, full-smoke pass, release-ready, publication-approved 상태는 주장하지 않는다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_route_family_local_evidence_aggregate`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2070`
- `EVIDENCE: work/5/20/2026-05-20-controller-runtime-route-docs-truth-sync.md`
- `EVIDENCE: verify/5/20/2026-05-20-controller-runtime-route-docs-truth-sync.md`
- `EVIDENCE: verify/5/20/2026-05-20-controller-runtime-json-route-test-consolidation.md`
- `REJECTED: operator_request` - destructive write, credential/auth, approval-record repair, merge/release/publication execution, immediate safety stop이 아니며 safe local work가 남아 있다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이고 next slice가 current evidence에서 좁게 결정된다.
- `REJECTED: another docs-only truth-sync` - controller route/status docs truth-sync는 완료되었고, 같은 docs-only micro-loop를 반복할 근거가 없다.
- `REJECTED: new controller route behavior expansion` - 현재 route-family behavior는 이미 여러 socket-free guard와 docs sync로 누적되었으므로 추가 route를 넓히기보다 먼저 local aggregate evidence를 재확인하는 편이 current-risk reduction에 맞다.
- 다음 safe local slice는 누적 controller route-family 변경을 대상으로 socket-free aggregate evidence를 다시 모으는 것이다. 코드 변경은 실패가 발견될 때만 `controller/server.py` 또는 `tests/test_controller_server.py`에 한정하고, 기본 성공 경로는 aggregate evidence `/work` closeout만 남긴다.
