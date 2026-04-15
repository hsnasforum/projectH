# 2026-04-15 controller office view toggle verification

## 검증 범위
- `controller/index.html`
- `tests/test_controller_server.py`
- internal runtime docs

## 실행한 검증
- `python3 -m unittest -v tests.test_controller_server`

## 결과
- controller HTML 계약 테스트가 통과하면 아래를 함께 보장합니다.
  - controller는 계속 `/api/runtime/status`, `/api/runtime/start|stop|restart`, `/api/runtime/capture-tail`만 사용함
  - `toggleOfficeView()`와 `office-toggle` UI surface가 존재함
  - `/api/state`나 arbitrary runtime exec 경로를 다시 끌어오지 않음

## 해석
- 이번 Office View 추가는 새로운 상태 source를 만든 것이 아니라, 기존 runtime status/tail을 시각적으로 재배치한 UI slice입니다.
- 따라서 문서가 요구한 single-writer / runtime API-only 경계를 해치지 않고 operator UX를 확장한 변경으로 볼 수 있습니다.

## 메모
- 브라우저에서 실제 시각 밀도와 애니메이션 인상은 live 확인 가치가 있습니다.
