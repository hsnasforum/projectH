# 2026-04-16 office view war-room identity

## 요약
- 기존 Office View는 scene-first 1차 버전까지는 들어갔지만, 아직 generic virtual office에 가까워 외부 레퍼런스를 떠올리게 할 여지가 있었습니다.
- 이번 수정은 controller read-model 안에서만 `projectH 전용 3-lane war-room` 정체성을 더 분명히 고정하는 데 목적이 있습니다.
- runtime authority는 그대로 `status.json / events.jsonl / controller runtime API`만 사용하고, backend/status schema는 바꾸지 않았습니다.

## 변경 파일
- controller/index.html
- tests/test_controller_server.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 핵심 변경
- Office View room title을 `Runtime War-Room`으로 조정하고, `Virtual Office`는 상위 시각 레이어 명칭으로만 남겼습니다.
- Claude / Codex / Gemini를 동등 3석으로 유지하면서 각 desk에 role object를 추가했습니다.
  - Claude: implement object
  - Codex: verify object
  - Gemini: advisory object
- watcher를 inspector 정보만이 아니라 room 내부 `ops core` 오브젝트로 끌어와서, 장면 안에서 runtime heartbeat를 느낄 수 있게 했습니다.
- `READY / WORKING / BOOTING / BROKEN` 상태 차이를 desk glow, role object animation, degraded ambient로 더 분명하게 분리했습니다.
- `auth_login_required`는 generic broken과 구분되도록 `login` badge와 auth-toned visual로 표면화했습니다.
- inspector는 유지하되 `Operations Inspector`로 명명하고, room이 주인공이고 inspector는 보조 패널이라는 구조를 더 분명히 했습니다.

## 검증
- python3 -m unittest -v tests.test_controller_server
- git diff --check -- controller/index.html tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md report/pipeline_runtime/progress/2026-04-16-office-view-war-room-identity.md

## 남은 리스크
- 현재 sprite 자산 품질이 완전히 통일된 것은 아니라, role object와 room identity는 더 좋아졌어도 캐릭터 프레임 자체의 자연스러움은 자산 품질 영향이 남아 있습니다.
- 이번 변경은 controller read-model까지만 다뤘으므로, Office View에서 live command 입력이나 더 풍부한 interaction을 붙이는 일은 별도 slice로 다루는 편이 안전합니다.
