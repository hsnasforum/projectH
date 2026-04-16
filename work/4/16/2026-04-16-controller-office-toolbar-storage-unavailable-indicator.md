# 2026-04-16 controller office toolbar storage-unavailable indicator

## 변경 파일
- `controller/index.html`
- `tests/test_controller_server.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-office-toolbar-storage-unavailable-indicator.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 `PrefStore` 공유 helper와 event log 경고를 추가했지만, event log 경고는 한 번만 표시되고 스크롤되면 놓칠 수 있어 toolbar 영역을 주시하는 operator가 persistence 비활성 상태를 인지하지 못하는 gap이 남아 있었습니다.
- latest work note에서 이 event-log-only 경고를 남은 리스크로 기록했습니다.

## 핵심 변경
- `controller/index.html`
  - `.toolbar .storage-warn` CSS 추가: amber 색상 경고 chip, 기본 `display: none`.
  - toolbar HTML에 `<span class="storage-warn" id="storage-warn">⚠ 설정 비저장</span>` 추가. tooltip은 `localStorage 사용 불가 — 새로고침 시 toolbar 설정이 초기화됩니다`.
  - BOOT 섹션에서 `PrefStore.available`이 false일 때 `#storage-warn`의 `display`를 활성화합니다.
  - 기존 event log 경고와 reduced-motion/ambient mute 기능 동작은 변경하지 않았습니다.
- `tests/test_controller_server.py`
  - `test_controller_html_polls_runtime_api_only`에 `storage-warn`, `설정 비저장`, `PrefStore.available` 회귀 검증 3건을 추가했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
  - `#storage-warn` chip의 동작, tooltip, `PrefStore.available` 조건, non-authoritative 성격을 문서화했습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 차단 환경에서 toolbar 영역에 `⚠ 설정 비저장` chip이 지속 표시된다는 점을 운영 안내에 추가했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.002s`, `OK`
- `git diff --check -- controller/index.html tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `tmp=$(mktemp --suffix=.js); trap 'rm -f "$tmp"' EXIT; sed -n '/<script>/,/<\/script>/p' controller/index.html | sed '1d;$d' > "$tmp"; node --check "$tmp"`
  - 결과: 출력 없음 (JS 구문 오류 없음)
- `rg -n "storage-warn|설정 비저장|PrefStore\\.available" controller/index.html`
  - 결과: CSS 1건, HTML element 1건, BOOT logic 2건 확인
- `rg -n "/api/.*storage|/api/.*pref|route.*storage" controller/index.html`
  - 결과: 0건 — backend route 추가 없음
- manual controller/browser smoke
  - 결과: 미실행. 이번 변경은 기존 `PrefStore.available` 값을 읽어 hidden chip을 표시하는 것뿐이며, 새 route나 기존 visual contract 변경은 없으므로 browser smoke는 과했습니다.

## 남은 리스크
- `localStorage` 차단 환경에서 실제 chip 표시를 browser로 확인하지 않았습니다. private browsing 환경에서의 실 확인은 향후 browser smoke로 보강할 수 있습니다.
- selected-lane, layout/zoom 같은 다른 persistence 대상은 아직 scope 밖입니다.
- browser-local 설계이므로 다른 브라우저/기기 간 동기화는 없습니다.
