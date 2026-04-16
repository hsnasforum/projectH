# 2026-04-16 controller background preload readiness hardening

## 변경 파일
- `controller/index.html`
- `tests/test_controller_server.py`
- `work/4/16/2026-04-16-controller-background-preload-readiness-hardening.md`

## 사용 skill
- `work-log-closeout`: 이번 배경 preload readiness 강화와 실제 검증 결과를 `/work` 형식으로 정리했습니다.

## 변경 이유
- `verify/4/16/2026-04-16-controller-office-reset-base-verification.md`에서 지적한 대로, 이전 경로 수정 라운드 이후에도 Office View 배경 preload는 cached/fast-path readiness를 명시적으로 latch하지 못하고, silent flat-color fallback 진단도 어려운 상태였습니다.
- 같은 controller Office View family 안에서 가장 가까운 current-risk reduction으로, 배경 이미지 preload lifecycle을 강화해 cached asset도 truthful하게 ready 상태를 잡고 실패 시 event log에 operator-facing signal을 남기도록 했습니다.

## 핵심 변경
- `controller/index.html`
  - `_loadBackgroundAsset(index)` 함수를 도입해 `BACKGROUND_ASSET_CANDIDATES` 배열의 순서대로 배경 이미지를 시도합니다.
  - `_bgImg.onload`와 `_bgImg.onerror` 핸들러를 `_bgImg.src` 할당 이전에 등록하여 race condition을 방지합니다.
  - `src` 할당 후 `_bgImg.complete && naturalWidth > 0`를 즉시 확인해 브라우저가 이미 캐시한 이미지도 truthful하게 ready를 latch합니다.
  - load 실패 시 `_emitBackgroundSignal`로 event log에 비권한적(non-authoritative) 경고를 남겨 진단을 돕습니다.
  - event log가 아직 초기화되지 않은 시점의 signal은 `_pendingBackgroundSignals` 큐에 보관했다가 `_flushBackgroundSignals`로 지연 방출합니다.
  - sidebar Runtime info에 `Scene` 행을 추가해 배경 로드 상태(`root` / `fallback` / `asset_error` / `loading`)를 실시간 표시합니다.
- `tests/test_controller_server.py`
  - `test_controller_html_polls_runtime_api_only`에 새 preload readiness 계약 회귀 검증을 추가했습니다:
    - `function _loadBackgroundAsset(` 함수 존재
    - `_bgImg.onload` / `_bgImg.onerror` 핸들러 등록
    - `_bgImg.complete` cached readiness latch
    - `naturalWidth` 기반 유효 이미지 판별
    - `_bgLoadError` 오류 상태 추적
    - `_emitBackgroundSignal(` 진단 signal 존재

## 검증
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.001s`, `OK`
- `git diff --check -- controller/index.html tests/test_controller_server.py`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `rg -n "[ \t]+$" tests/test_controller_server.py`
  - 결과: 출력 없음 (trailing whitespace 없음)
- manual controller/browser smoke
  - 결과: 미실행. 이번 변경은 테스트 파일의 정적 계약 assertion 추가가 주 범위이며, 배경 preload 코드 자체는 이전 working tree에서 이미 작성된 상태라 별도 browser smoke가 과했습니다.

## 남은 리스크
- `controller/assets/generated/bg-office.png` duplicate copy가 live contract 밖에 남아 있어, 배경 자산 source-of-truth를 어디에 둘지는 후속 라운드에서 정리할 여지가 있습니다.
- `_emitBackgroundSignal`의 dedup key는 동일 key 반복을 무시하지만, 완전히 다른 경로로 재시도한 뒤 같은 최종 상태에 도달하면 중복 signal이 발생할 수 있습니다. 실사용에서는 문제가 되지 않을 만큼 드문 경로입니다.
- `BACKGROUND_ASSET_CANDIDATES` 순서 변경 시 fallback 동작이 바뀌므로, 향후 배경 자산을 추가/제거할 때는 이 배열의 순서 의미를 확인해야 합니다.
