# 2026-04-15 controller office sprite hookup verification

## 검증 범위
- `controller/server.py`
- `controller/index.html`
- `tests/test_controller_server.py`

## 실행한 검증
- `python3 -m unittest -v tests.test_controller_server`

## 결과
- controller server 테스트가 통과했습니다.
- 아래 계약을 함께 확인했습니다.
  - controller HTML은 `/controller-assets/fren-office-sheet.png`를 optional Office View 자산 경로로 참조함
  - controller는 계속 `/api/runtime/status`, `/api/runtime/start|stop|restart`, `/api/runtime/capture-tail`만 사용함
  - asset path resolver는 기존 controller 디렉터리 밖으로 나가는 traversal을 거부함

## 해석
- 이번 변경으로 사용자는 sprite sheet PNG 한 장만 `controller/assets/fren-office-sheet.png`에 두고 새로고침하면 Office View에서 바로 시험할 수 있습니다.
- 자산이 없을 때도 controller는 깨지지 않고 fallback avatar를 유지하므로 current operator flow를 막지 않습니다.

## 메모
- 실제 PNG가 들어오면 crop 위치와 state별 frame 선택을 live로 한 번 조정해 보는 것이 좋습니다.
