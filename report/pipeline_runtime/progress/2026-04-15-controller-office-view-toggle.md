## 변경 파일
- controller/index.html
- tests/test_controller_server.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- 없음

## 변경 이유
- controller에 이미 `텍스트 ON/OFF` 토글이 있지만, operator가 현재 lane 상태를 더 직관적으로 읽을 수 있는 시각화 모드가 필요했습니다.
- 다만 runtime 구조 원칙상 새로운 상태 authority를 만들면 안 되므로, 기존 `/api/runtime/status`와 `/api/runtime/capture-tail`을 그대로 읽는 read-model 토글로만 추가해야 했습니다.

## 핵심 변경
- toolbar에 `Office View ON/OFF` 토글 버튼을 추가했습니다.
- center pane 영역에 optional `Virtual Office` 레이어를 추가했습니다.
  - Claude / Codex / Gemini를 각각 도트풍 사무실 책상 카드로 렌더링합니다.
  - 상태(`READY`, `WORKING`, `BOOTING`, `BROKEN`)는 애니메이션과 색상으로만 표현합니다.
  - `텍스트 ON`일 때는 각 lane의 최근 tail을 말풍선처럼 보여주고, `텍스트 OFF`일 때는 note/status 중심으로 보이게 했습니다.
- 기존 pane 뷰와 runtime API 경로는 유지했고, `Office View`는 controller 내부 렌더링 토글로만 동작하게 했습니다.
- internal runtime 문서에도 Office View가 visual read-model이며 별도 authority가 아님을 명시했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server`

## 남은 리스크
- 현재 Office View는 controller 내부 렌더링만 추가한 것이므로, very long tail을 계속 보여줄 때 시각적 밀도가 높아질 수 있습니다.
- lane별 wrapper event가 더 풍부해지면 나중에 typing/idle 애니메이션도 runtime event 기반으로 더 정확히 분리할 수 있습니다.
