# 2026-04-16 controller state gif priority sync

## 변경 파일
- `controller/index.html`
- `tests/test_controller_server.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-state-gif-priority-sync.md`

## 사용 skill
- `doc-sync`: controller Office View 자산 우선순위가 바뀌어서 runtime 문서를 구현 truth에 맞췄습니다.
- `work-log-closeout`: 이번 라운드 변경 파일, 검증, 남은 리스크를 `/work` 형식으로 정리했습니다.

## 변경 이유
- `controller/assets/` 아래에 상태별 GIF(`BOOTING`, `WORKING`, `BROKEN`, `READY`, `DEAD`)가 준비되었는데, 현재 Office View는 generated PNG sprite manifest만 우선 사용하고 있었습니다.
- operator가 올려 둔 GIF를 바로 쓰되, 기존 generated sprite fallback은 유지해야 현재 controller read-model 계약을 깨지 않고 시각화만 개선할 수 있습니다.

## 핵심 변경
- `controller/index.html`
  - `STATE_GIF_ASSETS`를 추가해 상태별 GIF 경로를 선언했습니다.
  - `SpriteManager`가 GIF를 먼저 preload하고, 해당 상태 GIF가 로드되면 이를 우선 반환하도록 바꿨습니다.
  - 상태 GIF가 없거나 아직 로드되지 않았을 때는 기존 `office-sprite-manifest.json` 기반 PNG frame animation으로 그대로 fallback 하도록 유지했습니다.
- `tests/test_controller_server.py`
  - controller HTML 정적 계약 테스트에 다섯 개 GIF 경로와 `STATE_GIF_ASSETS` 선언이 포함되는지 확인하는 회귀 검증을 추가했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
  - Office View 자산 우선순위를 `상태별 GIF -> generated PNG manifest -> raw sheet/circle fallback` 순서로 명시했습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - operator가 GIF 다섯 개를 `controller/assets/`에 두면 browser가 이를 우선 사용하고, 없으면 기존 sprite build 경로를 쓰는 운영 절차로 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
- `git diff --check -- controller/index.html tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 남은 리스크
- GIF 애니메이션 품질은 브라우저의 GIF 디코딩/캔버스 redraw 타이밍에 의존하므로, 상태 전환 직후 첫 몇 프레임은 환경에 따라 약간 다르게 보일 수 있습니다.
- 일부 상태 GIF만 교체된 경우 나머지 상태는 generated PNG manifest fallback을 계속 사용하므로, 자산 스타일이 완전히 통일되지 않을 수 있습니다.
