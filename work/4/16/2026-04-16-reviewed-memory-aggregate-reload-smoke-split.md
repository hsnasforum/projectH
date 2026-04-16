# reviewed-memory-aggregate-reload-smoke-split

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill

- 없음

## 변경 이유

기존 `same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다` 시나리오는 6개 reload continuity point를 모두 포함하면서 `testInfo.setTimeout(240_000)` 까지 늘어남. 실측 1.4m이지만 단일 시나리오 timeout 압박이 커서 fatigue/flake 위험이 있음. 동일 assertion을 유지하면서 두 시나리오로 분할하여 각각 150s timeout으로 줄임.

## 핵심 변경

1. **helper 추가**: `advanceAggregateToActiveEffect(page)` — 두 교정 → emit → apply → confirm을 reload 검증 없이 빠르게 실행하여 active-effect 상태로 진입. `{ sessionId, canonicalTransitionId }` 반환.
2. **시나리오 분할**:
   - `emitted-apply-confirm lifecycle으로 활성화됩니다` (150s): setup → emit → emitted-reload → apply → applied-pending-reload → confirm → active-effect → active-effect-reload
   - `stop-reverse-conflict lifecycle으로 정리됩니다` (150s): helper로 active-effect까지 빠르게 진입 → stop → stopped-reload → reverse → reversed-reload → conflict → conflict-checked-reload
3. **docs 미변경**: README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG는 user-visible behavior contract를 기술하며 테스트 조직 구조는 기술하지 않으므로 변경 불필요.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate" --reporter=line` → 2 passed (1.9m)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean
- full Playwright suite 미실행: 기존 시나리오를 두 개로 분할했을 뿐 shared helper나 다른 시나리오에 영향 없음.

## 남은 리스크

- 두 번째 시나리오가 helper로 active-effect까지 replay하므로 총 실행 시간은 1.4m → 1.9m으로 소폭 증가. 각 시나리오 개별 timeout 압박은 240s → 150s로 의미 있게 감소.
- 두 시나리오가 서로 독립적이므로 향후 병렬 실행 시 추가 시간 절감 가능.
