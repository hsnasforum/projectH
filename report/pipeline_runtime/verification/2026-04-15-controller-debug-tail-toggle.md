# 2026-04-15 controller debug tail toggle verification

## 검증 범위
- `controller/index.html`
- `tests/test_controller_server.py`

## 실행한 검증
- `python3 -m unittest -v tests.test_controller_server`

## 결과
- controller server 관련 테스트 12건 통과
- HTML 정적 검사 항목에 아래를 추가해 확인했습니다.
  - `/api/runtime/status`
  - `/api/runtime/start|stop|restart`
  - `/api/runtime/capture-tail`
  - `toggleTail()`
- `fetch("/api/state")`와 legacy `/api/start` 직접 호출이 active path에 재도입되지 않았음을 유지했습니다.

## 해석
- 이번 변경은 state authority를 넓힌 것이 아니라, 이미 분리돼 있던 controller debug tail surface를 브라우저에서 opt-in으로 노출한 것입니다.
- launcher thin client 경계는 유지되고, raw pane text는 controller에서만 사용자가 명시적으로 켰을 때 보입니다.

## 메모
- runtime 문서에서 의도한 “browser UI는 controller HTTP만 사용”과 “raw pane text는 기본 surface가 아니라 debug 경로”라는 방향에 맞춘 구현입니다.
