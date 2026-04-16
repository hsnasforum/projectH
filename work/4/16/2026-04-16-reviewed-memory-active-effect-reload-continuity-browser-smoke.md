# reviewed-memory active-effect reload continuity browser smoke bundle

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 final `reversed` + `conflict_visibility_checked` 상태 후 hard page reload continuity smoke와 docs parity를 닫았습니다. 그러나 사용자에게 가장 중요한 active-effect 상태(`결과 확정` 후, stop/reversal 이전)에서의 reload continuity는 아직 자동화 커버리지가 없었습니다. 이번 라운드는 active-effect reload를 추가하여, shipped reviewed-memory의 핵심 사용자 가치인 "reload 후에도 교정 패턴이 계속 적용되는지"를 고정합니다.

## 핵심 변경

1. **`e2e/tests/web-smoke.spec.mjs`**: 기존 aggregate-trigger smoke에 `결과 확정` + active effect 직후 hard `page.reload()` 추가.
   - reload 후 aggregate-trigger box visible, 결과 확정 완료 badge, 활성화 helper text 확인
   - payload: `record_stage = applied_with_result`, `result_stage = effect_active`, `reviewed_memory_active_effects` 존재 확인
   - post-reload follow-up response: `[검토 메모 활성]` prefix + operator 사유 텍스트 확인
   - timeout 90s → 120s 조정 (실측 1.1m)
2. **docs 4개**: README.md scenario 12, MILESTONES.md, ACCEPTANCE_CRITERIA.md, TASK_BACKLOG.md에 active-effect reload continuity 검증 기술 추가. 기존 final-state reload과 함께 두 lifecycle point에서의 reload continuity로 기술.

## Production 파일 미변경 사유

active-effect reload 후 aggregate-trigger UI 및 `[검토 메모 활성]` 응답이 정상이므로 production 코드 버그 없음. `app/static/app.js` 변경 불필요.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다" --reporter=line` → 1 passed (1.1m)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs app/static/app.js README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/16` → clean

## 남은 리스크

- emitted / `applied_pending_result` / stopped 중간 상태에서의 reload continuity는 아직 별도 자동화 커버리지 없음. 다만 이들은 짧은 transitional operator 상태이며, 핵심 사용자 가치인 active-effect와 final conflict-checked 상태는 이번 라운드로 모두 고정됨.
- full Playwright suite 미실행: 기존 시나리오 확장이므로 shared browser helper 전체에 대한 regression 가능성은 낮음.
