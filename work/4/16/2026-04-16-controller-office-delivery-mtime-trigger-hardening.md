# 2026-04-16 controller office delivery artifact-mtime trigger hardening

## 변경 파일
- `controller/index.html`
- `tests/test_controller_server.py`
- `work/4/16/2026-04-16-controller-office-delivery-mtime-trigger-hardening.md`

## 사용 skill
- 없음

## 변경 이유
- `verify/4/16/2026-04-16-controller-background-preload-readiness-hardening-verification.md`에서 지적된 delivery trigger blind spot을 해소합니다.
- `checkDeliveryTrigger()`가 `latest_work.path`와 `latest_verify.path`만 비교하고 `mtime`을 무시했기 때문에, 같은 경로에서 내용만 갱신된 update-in-place `/work` 또는 `/verify` 노트는 Office View에서 감지되지 않았습니다.
- runtime payload는 이미 `artifacts.latest_work.mtime`과 `artifacts.latest_verify.mtime`을 제공하고 있으므로, 새 route나 authority path 없이 기존 필드를 읽는 것만으로 해결 가능했습니다.

## 핵심 변경
- `controller/index.html`
  - `_deliveryState`에 `latestWorkMtime`과 `latestVerifyMtime` 필드를 추가했습니다.
  - `checkDeliveryTrigger()`에서 `artifacts.latest_work.mtime`과 `artifacts.latest_verify.mtime`을 읽어 이전 값과 비교합니다.
  - Work/Verify delivery 판정 조건을 `path` 변경 **또는** `mtime` 변경으로 확장하여, 같은 경로에서 내용이 갱신된 경우에도 one-shot delivery event가 발생합니다.
  - 함수 끝에서 `latestWorkMtime`과 `latestVerifyMtime`도 함께 저장합니다.
- `tests/test_controller_server.py`
  - `test_controller_html_polls_runtime_api_only`에 mtime-aware delivery 계약 회귀 검증을 추가했습니다:
    - `latestWorkMtime` 필드 존재
    - `latestVerifyMtime` 필드 존재
    - `.mtime` payload 읽기 존재

## 검증
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.002s`, `OK`
- `git diff --check -- controller/index.html tests/test_controller_server.py`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `tmp=$(mktemp --suffix=.js); trap 'rm -f "$tmp"' EXIT; sed -n '/<script>/,/<\/script>/p' controller/index.html | sed '1d;$d' > "$tmp"; node --check "$tmp"`
  - 결과: 출력 없음 (JS 구문 오류 없음)
- `rg -n "latestWorkMtime|latestVerifyMtime|\\.mtime" controller/index.html`
  - 결과: state 선언, payload 읽기, 초기화, 비교, 저장 경로 10개 라인에서 mtime 필드 확인
- manual controller/browser smoke
  - 결과: 미실행. 이번 변경은 기존 payload 필드를 읽는 비교 조건 확장이며, 새 route/visual contract를 추가하지 않았으므로 browser smoke는 과했습니다.

## 남은 리스크
- `mtime` 값이 runtime payload에서 빈 문자열로 오는 경우(`mtime` 필드 누락 등), mtime 비교는 건너뛰고 기존 path-only 동작으로 graceful fallback합니다.
- `controller/assets/generated/bg-office.png` duplicate copy는 여전히 live contract 밖에 남아 있습니다.
- decorative layer(Pet, Weather, Delivery) 전체에 대한 통합 browser smoke는 아직 이번 범위 밖입니다.
