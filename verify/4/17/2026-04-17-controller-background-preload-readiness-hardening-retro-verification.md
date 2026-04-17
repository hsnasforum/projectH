# 2026-04-17 controller background preload readiness hardening retro verification

## 변경 파일
- `verify/4/17/2026-04-17-controller-background-preload-readiness-hardening-retro-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 요청으로 지정된 archival 대상 `work/4/16/2026-04-16-controller-background-preload-readiness-hardening.md`의 핵심 preload readiness hardening 주장이 현재 트리에서도 사실인지 다시 확인하는 verification 라운드입니다.
- read-first 입력으로 지정된 `verify/4/16/2026-04-16-reviewed-memory-aggregate-reload-smoke-split-verification.md`는 다른 family의 기존 verify note라 참고만 했고, 이번 controller archival truth는 별도 4/17 `/verify` note로 남깁니다.

## 핵심 변경
- 대상 `/work`의 핵심 preload readiness hardening 주장은 현재 트리와 맞습니다.
  - `controller/index.html`에는 `BACKGROUND_ASSET_CANDIDATES`, `_pendingBackgroundSignals`, `_loadBackgroundAsset()`, `_bgImg.onload` / `_bgImg.onerror` 선등록, `_bgImg.complete && naturalWidth` cached readiness latch가 그대로 남아 있습니다.
  - 같은 파일의 runtime info surface는 `Scene` 행에서 `root` / `fallback` / `asset_error` / `loading` 상태를 계속 노출합니다.
  - `tests/test_controller_server.py`의 `test_controller_html_polls_runtime_api_only`도 위 preload/signal/Scene 계약 문자열을 현재 그대로 검사합니다.
- focused 자동 검증은 현재 통과했습니다.
  - `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only` → `Ran 1 test in 0.003s`, `OK`
  - extracted controller script에 대한 `node --check` → 출력 없음
  - `git diff --check -- controller/index.html tests/test_controller_server.py` → 출력 없음
- current docs mismatch도 이번 범위에서는 보이지 않았습니다.
  - `README.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`를 다시 찾은 결과, controller가 release gate 밖 internal/operator tooling이라는 현재 계약과 Office View background fallback + `Scene` state surface가 이미 문서에 반영돼 있었습니다.
- 다만 이번 note는 archival truth 확인이지 최신 controller family 전체의 readiness 판정은 아닙니다.
  - 현재 트리에는 later same-day controller/runtime 후속 변경이 이미 더 섞여 있으므로, 이번 결론은 "`background preload readiness hardening` slice의 핵심 주장은 아직 truthful하다"는 뜻으로만 읽어야 합니다.
  - live automation 관점의 다음 쟁점은 controller가 아니라 sqlite browser same-family truth-sync입니다.
  - `verify/4/17/2026-04-17-sqlite-browser-history-card-noisy-single-source-strong-plus-missing-click-reload-exact-title-parity-verification.md`까지는 이미 존재하지만, `work/4/17/2026-04-17-sqlite-browser-history-card-natural-reload-chain-parity.md`는 여전히 matching `/verify`가 없습니다.
  - 따라서 seq 275 control은 controller family를 더 파지 않고, 이미 seq 272 Gemini advice로 좁혀진 natural-reload-chain retro-closeout bundle을 그대로 유지하는 편이 가장 truthfully 맞습니다.

## 검증
- `rg -n "BACKGROUND_ASSET_CANDIDATES|_pendingBackgroundSignals|function _loadBackgroundAsset\\(|_bgImg\\.onload|_bgImg\\.onerror|_bgImg\\.complete|naturalWidth|_bgLoadError|_emitBackgroundSignal\\(|<span class=\\"info-label\\">Scene</span>|root'|fallback'|asset_error'|loading'" controller/index.html`
  - 결과: preload fallback/readiness/signal/`Scene` 상태 표시 문자열이 현재 HTML에 남아 있음을 확인했습니다.
- `nl -ba controller/index.html | sed -n '1090,1160p'`
  - 결과: `BACKGROUND_ASSET_CANDIDATES`, `_pendingBackgroundSignals`, `_loadBackgroundAsset()`, `_bgImg.onload`, `_bgImg.onerror`, `_bgImg.complete`, `naturalWidth` fast-path를 줄 단위로 재확인했습니다.
- `nl -ba controller/index.html | sed -n '2808,2820p'`
  - 결과: runtime info에 `Scene` 행과 `root` / `fallback` / `asset_error` / `loading` state 계산이 남아 있음을 확인했습니다.
- `nl -ba tests/test_controller_server.py | sed -n '88,118p'`
  - 결과: `test_controller_html_polls_runtime_api_only`가 background asset fallback, preload readiness, `_emitBackgroundSignal(`, `Scene` surface를 정적 HTML 계약으로 검사함을 확인했습니다.
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.004s`, `OK`
- `tmp=$(mktemp --suffix=.js); trap 'rm -f "$tmp"' EXIT; awk '/<script>/{flag=1; next} /<\\/script>/{flag=0} flag' controller/index.html > "$tmp"; node --check "$tmp"`
  - 결과: 출력 없음
- `git diff --check -- controller/index.html tests/test_controller_server.py`
  - 결과: 출력 없음
- `rg -n "controller|Scene|background fallback|internal/operator tooling|controller has its own Playwright smoke" README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: current docs가 controller internal scope와 background fallback/`Scene` 상태를 이미 설명하고 있음을 확인했습니다.
- `find verify/4/17 -maxdepth 1 -type f -name '*sqlite-browser-history-card*.md' | sort`
  - 결과: `noisy-single-source-strong-plus-missing-click-reload-exact-title-parity` verify는 이미 존재하고, `natural-reload-chain-parity` verify만 비어 있음을 확인했습니다.
- `test -f verify/4/17/2026-04-17-sqlite-browser-history-card-natural-reload-chain-parity-verification.md && echo exists || echo missing`
  - 결과: `missing`
- manual controller/browser smoke, `make controller-test`
  - 결과: 미실행. 이번 요청은 archival `/work` truth 재대조가 범위였고, static controller HTML contract + script syntax 재검증으로도 대상 주장 확인에는 충분했습니다.

## 남은 리스크
- 대상 `/work`의 핵심 주장은 유지되지만, current controller family에는 later same-day 후속 변경이 이미 들어와 있어 이 note를 최신 controller state 전체의 verification으로 읽으면 안 됩니다.
- live automation 관점의 blocker는 별개입니다. `work/4/17/2026-04-17-sqlite-browser-history-card-natural-reload-chain-parity.md`는 newer same-family `/work`인데 아직 matching `/verify`가 없습니다. 이번 round의 next control은 그 bounded retro-closeout bundle을 Claude implement lane에 다시 고정하는 데 그칩니다.
- controller browser smoke나 manual Office View 확인은 이번 archival round에서 다시 돌리지 않았으므로, controller visual behavior 전체를 새로 보증하는 note는 아닙니다.
