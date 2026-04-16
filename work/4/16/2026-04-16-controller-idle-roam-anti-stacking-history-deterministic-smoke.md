# 2026-04-16 controller idle roam anti-stacking + history penalty deterministic smoke

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
- docs에서 이미 약속한 idle roam의 inter-agent proximity avoidance(anti-stacking)와 `_roamHistory` graduated penalty를 controller smoke가 검증하지 않고 있었습니다.
- 기존 시나리오 6은 bounds/desk-exclusion만 다루고, 이 두 계약은 smoke 밖에 남아 있었습니다.
- 이번 슬라이스는 두 계약 각각에 대해 controller-local read-only test hook + deterministic smoke assertion을 추가합니다.

## 핵심 변경
- `controller/index.html`
  - `window.testAntiStacking(name, otherX, otherY, count)`: 임시 phantom idle agent를 `agents` Map에 추가한 뒤 N회 `_pickIdleTarget()` 호출, 각 pick의 phantom과의 거리 포함하여 반환, 테스트 후 phantom 제거 및 원래 상태 복원
  - `window.testHistoryPenalty(name, historyIndices, count)`: `_roamHistory`를 지정된 인덱스로 사전 세팅한 뒤 N회 `_pickIdleTarget()` 호출, spot-based pick만 `{spotIndex, x, y}`로 반환 (free-walk pick은 `_lastRoamIdx` sentinel로 판별하여 제외), 테스트 후 원래 상태 복원
- `e2e/tests/controller-smoke.spec.mjs`
  - 시나리오 7: `testAntiStacking("Claude", cx, cy, 50)` — walkable 중앙에 phantom 배치 후 50회 pick 중 50px 이내 pick이 15% 미만인지 검증
  - 시나리오 8: `testHistoryPenalty("Claude", [0,1,2,3,4], 120)` — history에 spot 0–4 세팅 후 spot-based pick 중 가장 강하게 페널티 받는 index 0(−150)이 10% 미만으로 선택되는지 검증
- docs 4건: controller smoke 시나리오 목록에 anti-stacking 및 history penalty 커버리지 반영

## 검증
- `make controller-test`
  - 결과: `8 passed (6.7s)`
- `git diff --check -- controller/index.html e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `make e2e-test` full browser suite 생략. 이번 변경은 controller-only UI/smoke이며 `app.web` 시나리오에 영향 없음.

## 남은 리스크
- 이번 smoke는 anti-stacking(proximity avoidance)과 history penalty만 검증합니다. docs에 설명된 나머지 roam 휴리스틱(stale-position timer 10s re-pick, micro-drift, facing-direction glance, free-walk 45% 비율 분포, three-tier wander interval 분포)은 이 deterministic assertion 범위 밖입니다.
- anti-stacking 테스트는 통계적 assertion(15% 미만)을 사용합니다. 극단적으로 작은 walkable 영역이라면 이론적으로 flaky할 수 있으나, 현재 controller 레이아웃에서는 여유 공간이 충분합니다.
- history penalty 테스트도 통계적 assertion(10% 미만)을 사용하며, 45% free-walk 확률에 의해 spot-based pick 수가 줄어들 수 있습니다. 120회 반복으로 최소 15개 이상의 spot-based pick을 확보하도록 assertion을 추가했습니다.
- 모든 test hook은 테스트 전용이나 production에서도 콘솔을 통해 호출 가능합니다. controller는 내부 operator 도구이므로 보안 위험은 낮습니다.
