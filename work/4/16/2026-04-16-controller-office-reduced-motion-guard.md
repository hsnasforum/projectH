# 2026-04-16 controller office reduced-motion guard

## 변경 파일
- `controller/index.html`
- `tests/test_controller_server.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-office-reduced-motion-guard.md`

## 사용 skill
- 없음

## 변경 이유
- `docs/superpowers/plans/2026-04-16-controller-office-view-projecth-adaptation.md`에서 "Provide a clean low-motion or off path if the effect starts to compete with readability or frame stability"를 명시했으나, 아직 browser-local reduced-motion/off 경로가 없었습니다.
- weather rain, pet roaming, event particle, delivery packet animation이 한꺼번에 그려지는 상태에서, runtime truth(agent 상태, badge, event log)만 집중적으로 보고 싶은 operator에게 bounded control이 없었습니다.

## 핵심 변경
- `controller/index.html`
  - toolbar에 `✨` reduced-motion 토글 버튼(`motion-btn`)을 추가했습니다.
  - `_lowMotion` 플래그와 `toggleLowMotion()` 함수를 도입했습니다.
  - low-motion 활성화 시 기존 particles와 deliveryPackets를 즉시 비웁니다.
  - main loop에서 `_lowMotion`이 켜진 경우 다음을 건너뜁니다:
    - particle update/draw
    - deliveryPacket update/draw
    - Weather update/draw
    - Pet update/draw
    - processIdleChatter
  - `spawnParticle()`에서 `_lowMotion` early return을 추가해 새 particle 생성도 차단합니다.
  - agent 렌더링, runtime badge, event log, log modal, needs-operator overlay, AmbientAudio는 low-motion과 무관하게 유지됩니다.
  - 이 설정은 순수 browser-local이며 backend route를 추가하지 않습니다.
- `tests/test_controller_server.py`
  - `test_controller_html_polls_runtime_api_only`에 low-motion 계약 회귀 검증 4건을 추가했습니다:
    - `let _lowMotion = false` 플래그 존재
    - `function toggleLowMotion()` 함수 존재
    - `motion-btn` UI 요소 존재
    - `if (_lowMotion) return` particle guard 존재
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
  - ambient audio 절 뒤에 reduced-motion 토글 계약을 추가했습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - ambient audio 운영 안내 뒤에 `✨` 버튼의 동작과 범위를 설명하는 항목을 추가했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.002s`, `OK`
- `git diff --check -- controller/index.html tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `tmp=$(mktemp --suffix=.js); trap 'rm -f "$tmp"' EXIT; sed -n '/<script>/,/<\/script>/p' controller/index.html | sed '1d;$d' > "$tmp"; node --check "$tmp"`
  - 결과: 출력 없음 (JS 구문 오류 없음)
- `rg -n "_lowMotion" controller/index.html`
  - 결과: 선언(1561), 토글(1564), UI 반영(1567-1568), 초기화(1570), update gate(1592), draw gate 4곳(1611, 1618, 1630), spawnParticle guard(787) — 총 10개 라인에서 gate 확인
- manual controller/browser smoke
  - 결과: 미실행. 이번 변경은 새 route 없이 기존 draw loop에 boolean gate만 추가했으므로, 별도 browser smoke는 과했습니다.

## 남은 리스크
- `_lowMotion` 설정은 브라우저 새로고침 시 초기화됩니다. localStorage 같은 영속화는 이번 범위 밖입니다.
- agent의 idle wandering이나 speech bubble은 현재 low-motion gate에 포함되지 않습니다. agent 이동 자체를 멈추면 runtime state 표현이 왜곡될 수 있어 의도적으로 제외했습니다.
- decorative layer 전체에 대한 통합 browser smoke는 아직 이번 범위 밖입니다.
