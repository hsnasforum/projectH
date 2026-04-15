# 2026-04-15 controller tail density tuning verification

## 검증 범위
- `controller/index.html`
- `tests/test_controller_server.py`

## 실행한 검증
- `python3 -m unittest -v tests.test_controller_server`
- `node - <<'JS' ... new Function(script) ... JS` 방식의 controller inline script parse 확인

## 결과
- controller server 관련 테스트 12건 통과
- controller inline script parse 확인 통과
- runtime API 경계는 유지되었습니다.
  - `/api/runtime/status`
  - `/api/runtime/start|stop|restart`
  - `/api/runtime/capture-tail`
- 이번 변경은 브라우저 표시 전용 compacting만 추가했고, status authority나 runtime writer ownership은 건드리지 않았습니다.

## 해석
- 문제 원인은 CSS 여백과 terminal-oriented whitespace 보존이 같이 작용한 것이었습니다.
- 추가 확인 결과, tmux pane 자체가 좁은 폭에서 이미 줄바꿈된 상태로 capture-tail에 들어오고 있었습니다.
- 이번 조정으로 debug tail은 더 넓게 쓰이되, raw pane parser나 launcher active path로의 회귀 없이 controller debug surface 안에서만 해결됩니다.
