## 변경 파일
- controller/index.html
- tests/test_controller_server.py

## 사용 skill
- 없음

## 변경 이유
- controller 상태 화면에서 lane의 `READY/WORKING`만 보이고, 실제 작업 중인 최근 텍스트를 바로 확인하려면 별도 attach가 필요했습니다.
- runtime 문서 기준으로 launcher thin client 경계는 유지해야 하므로, raw pane text를 launcher active path에 재도입하지 않고 controller debug surface에서만 opt-in 표시가 필요했습니다.

## 핵심 변경
- controller toolbar에 `텍스트 ON/OFF` 토글을 추가했습니다.
- 토글이 꺼져 있을 때는 기존처럼 lane status 정보만 표시하고, 켜져 있을 때만 `/api/runtime/capture-tail?lane=`를 호출해 각 pane의 최근 output tail을 표시합니다.
- 기본값은 `OFF`로 두어 raw pane text가 기본 surface를 차지하지 않도록 했습니다.
- 구현은 기존 `/api/runtime/capture-tail` debug API를 그대로 재사용해 새 state authority나 watcher/log 해석 경로를 추가하지 않았습니다.
- launcher는 이번 변경에서 건드리지 않아 thin client + status/event viewer 경계를 그대로 유지합니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server`

## 남은 리스크
- `텍스트 ON` 상태에서는 visible lane 수만큼 추가 fetch가 발생합니다. 내부 operator tooling 용도로는 허용 가능한 범위지만, 필요하면 후속으로 poll 간격이나 focus lane 우선 fetch로 더 줄일 수 있습니다.
- raw pane text는 debug surface이므로, 상태 truth 판단은 계속 `status.json`과 runtime event fold만 사용해야 합니다.
