# reviewed-memory reversal-state reload continuity browser smoke bundle

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

active-effect, stopped, final conflict-checked 세 lifecycle point의 reload continuity는 이전 라운드들에서 이미 닫혔습니다. 남은 동일 family risk는 `적용 되돌리기` 후 conflict-visibility 이전의 reversed 상태에서 reload 시 상태가 drift하지 않는지입니다. 이번 라운드는 reversal-state reload continuity를 추가하여 shipped reviewed-memory lifecycle의 네 번째(마지막) 사용자 가시 reload point를 고정합니다.

## 핵심 변경

1. **`e2e/tests/web-smoke.spec.mjs`**: 기존 aggregate-trigger smoke에 `적용 되돌리기` 직후 (conflict-check 이전) hard `page.reload()` 추가.
   - reload 후 aggregate-trigger box visible, `적용 되돌림 완료` badge, 되돌림 helper text 확인
   - payload: `record_stage = reversed`, `result_stage = effect_reversed`, `reviewed_memory_active_effects` absent or empty 확인
   - post-reload follow-up response: `[검토 메모 활성]` 미포함 확인
   - timeout 150s → 180s 조정 (실측 1.1m)
2. **docs 4개**: README.md scenario 12, MILESTONES.md, ACCEPTANCE_CRITERIA.md, TASK_BACKLOG.md에 reversal-state reload continuity 추가. 네 lifecycle point에서의 reload continuity로 기술.

## Production 파일 미변경 사유

reversal-state reload 후 aggregate-trigger UI가 정상이고 `[검토 메모 활성]`이 미노출되므로 production 코드 버그 없음. `app/static/app.js` 변경 불필요.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다" --reporter=line` → 1 passed (1.1m)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs app/static/app.js README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/16` → clean

## 남은 리스크

- emitted / `applied_pending_result` 중간 상태에서의 reload continuity는 아직 별도 자동화 커버리지 없음. 다만 이들은 짧은 transitional operator 상태이며, 핵심 사용자 가치 4가지 (active-effect, stopped, reversed, final conflict-checked)는 모두 고정됨.
- full Playwright suite 미실행: 기존 시나리오 확장이므로 shared browser helper 전체에 대한 regression 가능성은 낮음.
