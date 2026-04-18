# 2026-04-18 controller cozy runtime shared-module ownership restore

## 변경 파일
- `controller/index.html`
- `controller/js/cozy.js` (new)
- `controller/css/office.css`
- `tests/test_controller_server.py`
- `e2e/tests/controller-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 사용 skill
- `superpowers:using-superpowers`

## 변경 이유
- `verify/4/18/2026-04-18-controller-cozy-assets-runtime-sync-verification.md`가 cozy 전환 이후 `controller/index.html`이 74–2815행짜리 standalone inline runtime 한 덩어리로 바뀌고 `/controller-assets/js/*.js` 모듈 경계가 사라진 현실을 기록했습니다.
- 같은 verify 노트는 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`가 open-floor walkable-bounds, desk exclusion rect, anti-stacking proximity, `_roamHistory` penalty 계약을 설명하고 있지만 실제 구현은 zone-bounded idle roam + 빈 `testHistoryPenalty` + `testAntiStacking→testPickIdleTargets` 위임으로 바뀌어 있다는 문서 drift도 같이 잡았습니다.
- `.pipeline/claude_handoff.md` `STATUS: implement`(`CONTROL_SEQ: 291`)는 이 두 축(소유권 경계 + roam 문서 truth)을 한 bounded slice로 닫도록 지시했습니다.
- cozy UI(Party Roster, Quest Log, marquee, 존 배치, GIF/background 미사용)와 현재 `/api/runtime/*` 계약, zone-bounded idle roam 동작은 그대로 유지해야 했습니다.

## 핵심 변경
- `controller/index.html`의 inline `<script>` 블록(74–2816행)을 새 공용 모듈 `controller/js/cozy.js`로 통째 이식하고, HTML에는 `<script src="/controller-assets/js/cozy.js"></script>` 한 줄만 남겼습니다. 이 덕분에 polling, sidebar rendering, log modal input/tail refresh, `PrefStore` storage 경고 와이어링, idle-roam test hooks(`setAgentFatigue`, `getRoamBounds`, `testPickIdleTargets`, `testAntiStacking`, `testHistoryPenalty`)이 모두 `/controller-assets/js/` 공용 소유권 아래로 돌아왔습니다.
- `cozy.js` 최상단에 모듈 역할/경계를 설명하는 짧은 주석 헤더를 달았고, 내부 런타임 로직/전역 심볼은 기존과 동일하게 유지해 브라우저 실행 의미는 바뀌지 않았습니다.
- `controller/server.py`의 `_resolve_controller_asset`가 이미 `controller/js/` 아래 파일을 `application/javascript`로 서빙하므로 추가 서버 변경 없이 `/controller-assets/js/cozy.js`가 그대로 로드됩니다.
- `tests/test_controller_server.py::test_controller_html_polls_runtime_api_only`를 새 소유권 경계에 맞게 다시 맞췄습니다. HTML은 DOM shell + `src="/controller-assets/js/cozy.js"`만 assert하고, 런타임 심볼(`POLL_MS`, `ACTION_REPOLL_MS`, `LOG_REFRESH_MS`, `logRefreshInFlight`, `modalSendInFlight`, `sendModalInput`, `getPresentation`, `UNCERTAIN_RUNTIME_REASONS`, `ZONE_MAP`, `sampleIdleTarget`, `setAgentFatigue`, `getRoamBounds`, `testPickIdleTargets`, `testAntiStacking`, `testHistoryPenalty`, `PrefStore`, localStorage 접근, `Latest work →` / `Latest verify →` / `Receipt issued →`, `Runtime truth uncertain` 등)은 `controller/js/cozy.js`에서 assert하도록 바꿨습니다. 동시에 `pollRuntime`/`sendModalInput`이 HTML에 inline으로 남아 있지 않다는 역-assert도 추가해 이번 변경이 되돌려지지 않도록 잠갔습니다.
- `e2e/tests/controller-smoke.spec.mjs`에 `cozy runtime loads from shared /controller-assets/js/cozy.js module` 시나리오를 추가했습니다. 페이지에 `/controller-assets/js/cozy.js` 스크립트 태그가 정확히 한 개 있는지, 그리고 그 모듈이 노출하는 test hook(`window.getRoamBounds`, `setAgentFatigue`, `testPickIdleTargets`, `testAntiStacking`, `testHistoryPenalty`)가 모두 function으로 reachable한지를 같이 확인합니다. 기존 zone-bounded idle roam / 빈 `testHistoryPenalty` / zone-isolation anti-stacking 시나리오는 그대로 유지해 최종 roam 의미를 truthfully 고정합니다.
- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`의 roam 설명 문단을 실제 구현에 맞게 다시 썼습니다. 이제 open-floor walkable-bounds, desk exclusion rect, anti-stacking proximity, `_roamHistory` 45% free-walk / ×2.6 jitter / 3-tier wander interval / stale-position timer 같은 낡은 주장 대신 "자기 데스크 존 안에서 zone-bounded 연속 micro-roam, zone rect clamp, 존 분리로 stacking 자연 방지, `testAntiStacking→testPickIdleTargets` 위임, `testHistoryPenalty` 빈 배열"을 현재 shipped 계약으로 적습니다. `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`에는 cozy 런타임이 `<script src="/controller-assets/js/cozy.js">`로 공용 모듈 소유권 아래 돌아왔다는 사실도 함께 기록했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`의 non-working lane wandering 문단과 `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`의 controller 테마/와이어링 문단을 zone-bounded 설명 + `controller/js/cozy.js` 실제 사용 파일 목록으로 truth-sync했습니다. 05 RUNBOOK의 `controller/js/config.js` 단일 언급도 `controller/js/cozy.js`로 바꿔 실제 shipped 파일을 가리키게 했습니다.
- `controller/css/office.css` 37행과 43행에 이전 라운드부터 남아 있던 `--px-border:` / `--px-border-sm:` trailing whitespace 두 칸을 제거해 이번 슬라이스에 적힌 `git diff --check` 검증 명령이 실제로 통과하도록 맞췄습니다(unrelated content 변경은 없음).

## 검증
- `node --check controller/js/cozy.js`
  - 결과: 통과
- `node --check controller/js/agents.js`
  - 결과: 통과
- `node --check controller/js/config.js`
  - 결과: 통과
- `python3 -m unittest tests.test_controller_server -v`
  - 결과: `Ran 23 tests`, `OK`
- `git diff --check -- controller/index.html controller/css/office.css controller/js/config.js controller/js/agents.js controller/js/audio.js controller/js/panel.js controller/js/sidebar.js controller/js/state.js controller/js/cozy.js tests/test_controller_server.py e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 통과(trailing whitespace 해소 후 0건)
- `cd e2e && CONTROLLER_SMOKE_PORT=8881 npx playwright test tests/controller-smoke.spec.mjs --reporter=line`
  - 결과: `10 passed (12.1s)` — 새 `cozy runtime loads from shared /controller-assets/js/cozy.js module` 시나리오 포함 전 시나리오 통과
- `make e2e-test`는 이번 라운드 실행하지 않았습니다. 변경된 browser-visible 계약 표면이 controller에 국한되어 있고 isolated controller smoke가 이미 모든 관련 시나리오를 truthfully 커버하므로, 넓은 browser suite를 다시 돌리는 것은 이번 bounded slice에 과한 검증이라고 판단했습니다.

## 남은 리스크
- `controller/js/cozy.js`는 여전히 2741행짜리 단일 모듈로, 기존 `controller/js/{state,sidebar,panel,audio,agents,config,canvas,delivery,zones}.js`와 상징(symbol)을 통합하지 않았습니다. 후속 라운드에서 같은 family 안의 더 작은 risk를 닫는다면 cozy.js의 polling/sidebar/log-modal/PrefStore/test-hook 영역을 기존 공용 모듈로 점진 분해하는 것이 자연스러운 다음 슬라이스입니다.
- 현재 `controller/js/{state,sidebar,panel,audio,agents,config,canvas,delivery,zones}.js`는 더 이상 브라우저에서 로드되지 않는 orphan 모듈입니다. 이번 라운드 handoff는 unrelated 변경을 건드리지 말라고 했으므로 그대로 두었고, 삭제/재배선 판단은 후속 슬라이스로 넘깁니다.
- Controller bind는 sandbox/runtime 환경에 따라 여전히 `PermissionError: [Errno 1] Operation not permitted`를 낼 수 있지만, 이번 라운드에서는 `CONTROLLER_SMOKE_PORT=8881`로 Playwright smoke가 정상 bind되어 재현됐습니다. 다른 환경에서 다시 실패하면 해당 결과는 "bind 환경 제약"으로 분리 기록하는 편이 맞습니다.
