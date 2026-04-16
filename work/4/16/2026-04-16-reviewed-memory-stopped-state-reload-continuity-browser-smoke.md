# reviewed-memory stopped-state reload continuity browser smoke bundle

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

active-effect reload continuity와 final conflict-checked reload continuity는 이전 라운드들에서 이미 닫혔습니다. 남은 동일 family risk는 `적용 중단` 후 reload 시 stopped 상태가 유지되는지 — 즉, reload로 인해 중단된 효과가 silently 재활성화되지 않는지입니다. 이번 라운드는 stopped-state reload continuity를 추가하여 shipped reviewed-memory safety contract의 reload gap을 닫습니다.

## 핵심 변경

1. **`e2e/tests/web-smoke.spec.mjs`**: 기존 aggregate-trigger smoke에 `적용 중단` 직후 hard `page.reload()` 추가.
   - reload 후 aggregate-trigger box visible, `적용 중단됨` badge, 중단 helper text 확인
   - payload: `record_stage = stopped`, `result_stage = effect_stopped`, `reviewed_memory_active_effects` absent or empty 확인
   - post-reload follow-up response: `[검토 메모 활성]` 미포함 확인
   - timeout 120s → 150s 조정 (실측 59.4s)
2. **docs 4개**: README.md scenario 12, MILESTONES.md, ACCEPTANCE_CRITERIA.md, TASK_BACKLOG.md에 stopped-state reload continuity 추가. 기존 두 lifecycle point에 세 번째 point로 기술.

## Production 파일 미변경 사유

stopped-state reload 후 aggregate-trigger UI가 정상이고 `[검토 메모 활성]`이 미노출되므로 production 코드 버그 없음. `app/static/app.js` 변경 불필요.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다" --reporter=line` → 1 passed (59.4s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs app/static/app.js README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/16` → clean

## 남은 리스크

- emitted / `applied_pending_result` 중간 상태에서의 reload continuity는 아직 별도 자동화 커버리지 없음. 다만 핵심 사용자 가치 3가지 (active-effect, stopped, final conflict-checked)는 모두 고정됨.
- full Playwright suite 미실행: 기존 시나리오 확장이므로 shared browser helper 전체에 대한 regression 가능성은 낮음.
