# 2026-04-16 office view density trim

## 요약
- 이전 war-room 패치가 정체성을 맞추는 데는 성공했지만, 화면 밀도가 너무 높아 장면보다 텍스트가 먼저 읽히는 문제가 있었습니다.
- 이번 후속 수정에서는 `role` 표기, agent strip, inspector 소제목 같은 보조 라벨을 줄여서 room과 sprite가 먼저 보이게 정리했습니다.
- runtime authority는 계속 바뀌지 않았고, controller read-model의 시각 밀도만 낮췄습니다.

## 변경 파일
- controller/index.html
- tests/test_controller_server.py

## 핵심 변경
- desk header와 agent pill에서 role 텍스트를 제거했습니다.
- 상단 summary와 inspector의 소제목을 줄여서 정보 밀도를 낮췄습니다.
- `office-agent-strip`을 화면에서 제거해 room 내부 시각 흐름이 끊기지 않게 했습니다.
- avatar zone과 sprite display 크기를 키워 캐릭터와 desk가 더 먼저 보이도록 조정했습니다.

## 검증
- python3 -m unittest -v tests.test_controller_server
- node --check /tmp/projecth-controller-office-warroom.js

## 남은 리스크
- 이번 수정으로도 sprite asset 자체의 자연스러움은 남아 있을 수 있습니다.
- 실제 브라우저에서 보이는 비율은 viewport 크기와 사용 중인 sprite sheet 품질에 따라 조금 더 미세조정이 필요할 수 있습니다.
