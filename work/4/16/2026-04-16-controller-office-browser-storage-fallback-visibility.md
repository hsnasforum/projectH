# 2026-04-16 controller office browser-local preference fallback visibility

## 변경 파일
- `controller/index.html`
- `tests/test_controller_server.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-office-browser-storage-fallback-visibility.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 toolbar preference persistence를 `localStorage`에 저장하도록 구현했지만, `localStorage`가 차단된 환경(private browsing 등)에서 persistence가 조용히 사라지는 silent fallback 상태가 남아 있었습니다.
- operator에게 persistence 비활성 상태를 알리지 않으면 새로고침 후 설정이 초기화되는 원인을 파악하기 어렵습니다.
- latest verify note에서 이 silent persistence downgrade를 남은 리스크로 기록했습니다.

## 핵심 변경
- `controller/index.html`
  - `PrefStore` IIFE 공유 helper를 추가했습니다. 최초 `localStorage` 접근 시 한 번만 probe를 수행하고, 실패하면 event log에 `환경 설정 저장 불가 — 새로고침 시 toolbar 설정이 초기화됩니다` 경고를 `pushEvent('warn', ...)` 로 표시합니다.
  - `PrefStore.get(key)` / `PrefStore.set(key, val)` / `PrefStore.available` 세 가지 interface를 제공합니다.
  - 기존 4곳의 inline `try { localStorage... } catch(e) {}` 블록을 `PrefStore.get()`/`PrefStore.set()` 호출로 교체했습니다.
  - reduced-motion과 ambient mute의 기능 동작은 변경하지 않았습니다.
- `tests/test_controller_server.py`
  - `test_controller_html_polls_runtime_api_only`에 `PrefStore`, `PrefStore.get(`, `PrefStore.set(`, `_probe()`, `환경 설정 저장 불가` 회귀 검증 5건을 추가했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
  - `PrefStore` helper의 one-time probe와 fallback-visibility 경고 계약을 문서화했습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - `localStorage` 차단 환경에서의 경고 동작과 현재 페이지 한정 정상 동작을 운영 안내에 추가했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.003s`, `OK`
- `git diff --check -- controller/index.html tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `tmp=$(mktemp --suffix=.js); trap 'rm -f "$tmp"' EXIT; sed -n '/<script>/,/<\/script>/p' controller/index.html | sed '1d;$d' > "$tmp"; node --check "$tmp"`
  - 결과: 출력 없음 (JS 구문 오류 없음)
- `rg -n "PrefStore\.(get|set|available)|_probe\(\)|환경 설정 저장 불가" controller/index.html`
  - 결과: `PrefStore.set` 2건, `PrefStore.get` 2건, `_probe()` 4건, fallback 경고 메시지 1건 확인
- `rg -n "/api/.*pref|/api/.*storage|route.*pref" controller/index.html`
  - 결과: 0건 — backend route 추가 없음
- manual controller/browser smoke
  - 결과: 미실행. 이번 변경은 기존 persistence 접근 경로를 공유 helper로 리팩터링하고 fallback 경고만 추가한 것이며, 새 route나 visual contract를 도입하지 않았으므로 browser smoke는 과했습니다.

## 남은 리스크
- `PrefStore` fallback 경고가 event log에만 표시되므로, event log를 주시하지 않는 operator는 인지하지 못할 수 있습니다. 향후 toolbar 영역에 작은 아이콘 표시 등으로 보강할 여지가 있습니다.
- selected-lane, layout/zoom 같은 다른 persistence 대상은 아직 `PrefStore`를 사용하지 않습니다. 현재는 해당 persistence가 구현되지 않았으므로 의도된 제한입니다.
- browser-local 설계이므로 다른 브라우저/기기 간 동기화는 없습니다.
