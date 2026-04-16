# 2026-04-16 controller office agent movement fatigue polish

## 변경 파일
- `controller/index.html`
- `e2e/tests/controller-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- controller Office View에 이미 부분적으로 구현된 agent fatigue/coffee 루프, fatigued movement slowdown, drone delivery trigger, monitor matrix/hologram이 있으나, sidebar에서 이들의 상태를 관찰할 수 있는 DOM 기반 계약이 없었습니다.
- 이번 슬라이스는 fatigue 상태를 sidebar agent card에 노출하는 하나의 안정적인 observable contract를 추가하고, 그에 대한 smoke 커버리지를 확보합니다.

## 핵심 변경
- `controller/index.html`
  - `Agent` 클래스에 `get fatigueState()` getter 추가: `coffee` / `fatigued` / `''` 반환
  - `.agent-fatigue` CSS 스타일 추가 (fatigued = 노랑, coffee = 초록)
  - `renderAgentCards()`에서 각 agent card에 `data-agent`, `data-fatigue` 속성 부여
  - fatigue 상태가 있을 때 `.agent-fatigue` 텍스트 표시 (`💦 피로 누적` / `☕ 커피 충전 중`)
- `e2e/tests/controller-smoke.spec.mjs`
  - 새 시나리오: working agent의 sidebar card가 `data-agent` + `data-fatigue` 속성을 가지며, fatigue threshold 이전에는 `.agent-fatigue` indicator가 없음을 검증
  - API를 stub하여 하나의 working agent를 반환하도록 route 설정
- docs 3건: controller smoke 시나리오 목록에 `data-fatigue` 계약 추가

## 검증
- `make controller-test`
  - 결과: `3 passed (3.6s)`
- `git diff --check -- controller/index.html e2e/tests/controller-smoke.spec.mjs`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `make e2e-test` full browser suite 생략. 이번 변경은 controller-only UI/smoke이며 `app.web` 시나리오에 영향 없음.

## 남은 리스크
- fatigue indicator는 폴링 주기(3초 기본)에 따라 sidebar에 반영됩니다. canvas 위 fatigue 애니메이션과 sidebar 텍스트 사이에 최대 폴링 간격만큼의 지연이 있을 수 있습니다.
- smoke test는 fatigue threshold(15초) 이전의 상태만 검증합니다. threshold 이후 `fatigued`→`coffee` 전환의 정밀한 timing 테스트는 이번 범위 밖입니다.
- drone delivery trigger(`spawnDrone`)는 working 상태 진입 시에만 발동하며, 이번 슬라이스에서 별도 변경 없습니다.
