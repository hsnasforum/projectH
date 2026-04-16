# 2026-04-16 controller deterministic fatigue transition smoke via state injection

## 변경 파일
- `controller/index.html`
- `e2e/tests/controller-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 슬라이스에서 agent fatigue observability 계약(`data-fatigue` 속성, `.agent-fatigue` indicator)이 sidebar에 도입되었으나, `fatigued`와 `coffee` 상태 전환을 smoke에서 검증하려면 실시간 15초 대기가 필요하여 brittle한 테스트만 가능했습니다.
- 이번 슬라이스는 controller-local `window.setAgentFatigue(name, value)` 테스트 전용 hook을 노출하고, 이를 통해 `fatigued`/`coffee` 상태 전환을 deterministic하게 주입·검증하는 smoke 시나리오 2건을 추가합니다.

## 핵심 변경
- `controller/index.html`
  - `window.setAgentFatigue(name, value)` 함수 추가 (line ~1152)
  - `value === 'fatigued'`: `agent.fatigue = 15`, `agent._atCoffee = false`
  - `value === 'coffee'`: `agent._atCoffee = true`, `agent.fatigue = 0`
  - `value === ''` (reset): 둘 다 초기화
  - 주입 후 `runtimeData.lanes`로 `renderAgentCards()` 재호출하여 sidebar 즉시 반영
  - 기존 fatigue/coffee 렌더링 경로를 그대로 재사용, 테스트 전용 별도 렌더 경로 없음
- `e2e/tests/controller-smoke.spec.mjs`
  - 시나리오 4: `setAgentFatigue("Claude", "fatigued")` → `data-fatigue="fatigued"` + `💦 피로 누적` 검증
  - 시나리오 5: `setAgentFatigue("Claude", "coffee")` → `data-fatigue="coffee"` + `☕ 커피 충전 중` 검증
- docs 4건: controller smoke 시나리오 목록에 deterministic fatigue/coffee transition 커버리지 반영

## 검증
- `make controller-test`
  - 결과: `5 passed (4.9s)`
- `git diff --check -- controller/index.html e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `make e2e-test` full browser suite 생략. 이번 변경은 controller-only UI/smoke이며 `app.web` 시나리오에 영향 없음.

## 남은 리스크
- `window.setAgentFatigue`는 테스트 전용 hook이나 production에서도 콘솔을 통해 호출 가능합니다. controller는 내부 operator 도구이므로 보안 위험은 낮습니다.
- hook은 agent가 이미 `agents` Map에 존재해야 동작합니다. 폴링 전에 호출하면 no-op입니다.
- fatigue 애니메이션(canvas 위 땀 파티클, 속도 감소)은 hook으로 주입한 상태에서도 정상 동작하나, smoke에서는 sidebar DOM 계약만 검증합니다.
