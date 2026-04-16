# reviewed-memory pre-result transitional reload continuity browser smoke bundle

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

active-effect, stopped, reversed, final conflict-checked 네 lifecycle point의 reload continuity는 이전 라운드들에서 이미 닫혔습니다. 남은 동일 family gap은 `emitted_record_only_not_applied`와 `applied_pending_result` 두 pre-result transitional 상태에서 reload 시 상태가 drift하지 않는지입니다. 이번 라운드는 이 두 중간 상태의 reload continuity를 추가하여 shipped reviewed-memory lifecycle의 reload point를 네 개에서 여섯 개로 완성합니다.

## 핵심 변경

1. **`e2e/tests/web-smoke.spec.mjs`**: 기존 aggregate-trigger smoke에 두 개의 hard `page.reload()` 추가.
   - **emitted-state reload** (transition record 발행 직후, apply 실행 이전): reload 후 aggregate-trigger box visible, emitted helper text 유지, payload continuity (`record_stage = emitted_record_only_not_applied`, `applied_at` absent, `apply_result` absent, `reviewed_memory_active_effects` absent or empty), apply button visible/enabled, post-reload follow-up `[검토 메모 활성]` 미포함 확인
   - **applied-pending-state reload** (apply 실행 직후, 결과 확정 이전): reload 후 aggregate-trigger box visible, applied-pending helper text 유지, payload continuity (`record_stage = applied_pending_result`, `applied_at` present, `apply_result` absent, `reviewed_memory_active_effects` absent or empty), `결과 확정` button visible/enabled, post-reload follow-up `[검토 메모 활성]` 미포함 확인
   - timeout 180s → 240s 조정 (실측 1.4m)
2. **docs 4개**: README.md scenario 12, MILESTONES.md, ACCEPTANCE_CRITERIA.md, TASK_BACKLOG.md에서 "four lifecycle points" → "six lifecycle points"로 갱신하고 두 pre-result transitional state를 (1), (2)로 앞에 추가.

## Production 파일 미변경 사유

두 pre-result transitional state 모두 reload 후 aggregate-trigger UI가 정상이고 `[검토 메모 활성]`이 미노출되므로 production 코드 버그 없음. `app/static/app.js` 변경 불필요.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다" --reporter=line` → 1 passed (1.4m)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs app/static/app.js README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean
- full Playwright suite 미실행: 기존 시나리오 확장이므로 shared browser helper 전체에 대한 regression 가능성은 낮음. 동일 시나리오 isolated rerun만으로 충분.

## 남은 리스크

- 여섯 lifecycle point 모두 동일 시나리오 안에서 sequential로 검증되므로 시나리오 타임아웃이 늘어남 (240s). 향후 시나리오 분할이 필요할 수 있으나 현재 실측 1.4m으로 충분한 여유.
- full Playwright suite 미실행: 기존 시나리오 확장이므로 shared browser helper 전체에 대한 regression 가능성은 낮음.
