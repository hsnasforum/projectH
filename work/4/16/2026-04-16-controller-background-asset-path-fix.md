# 2026-04-16 controller background asset path fix

## 변경 파일
- `controller/index.html`
- `tests/test_controller_server.py`
- `work/4/16/2026-04-16-controller-background-asset-path-fix.md`

## 사용 skill
- `work-log-closeout`: 이번 배경 자산 경로 수정과 실제 검증 결과를 `/work` 형식으로 정리했습니다.

## 변경 이유
- Office View 캔버스 배경 로더가 `/controller-assets/bg-office.png`를 찾고 있었지만, 실제 배경 파일은 `controller/assets/background.png`로 들어와 있었습니다.
- 이 상태에서는 배경 이미지가 로드되지 않아 controller가 fallback 단색 배경만 그리게 됩니다.

## 핵심 변경
- `controller/index.html`
  - Office View 배경 preload 경로를 `/controller-assets/background.png`로 수정했습니다.
- `tests/test_controller_server.py`
  - controller HTML 정적 계약 테스트에 `/controller-assets/background.png` 경로가 포함되는지 확인하는 회귀 검증을 추가했습니다.
- `controller/index.html`
  - 같은 파일 안에 남아 있던 trailing whitespace를 함께 정리해 `git diff --check`가 깨끗하게 통과하도록 맞췄습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
- `git diff --check -- controller/index.html tests/test_controller_server.py`
- `rg -n "background\\.png|bg-office\\.png" controller/index.html tests/test_controller_server.py`

## 남은 리스크
- 이번 수정은 배경 이미지 경로만 바로잡는 범위라, `background.png` 자산 자체의 구도나 해상도 문제는 그대로 남습니다.
- 브라우저가 이전 자산을 강하게 캐시한 경우 새로고침만으로 반영이 늦을 수 있어, 그런 경우 hard refresh가 필요할 수 있습니다.
