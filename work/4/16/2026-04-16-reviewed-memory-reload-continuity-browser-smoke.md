# reviewed-memory reload continuity browser smoke

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill

- 없음

## 변경 이유

stored review-support sanitize의 service regression은 이전 라운드에서 truthful하게 닫혔습니다. 그러나 shipped `검토 메모 적용 후보` aggregate-trigger 표면의 브라우저 reload continuity는 아직 자동화 커버리지가 없었습니다. 이번 라운드는 기존 aggregate-trigger smoke 시나리오에 hard page reload 검증을 추가하여, 저장된 lifecycle state가 reload 후에도 올바르게 렌더링됨을 고정합니다.

## 핵심 변경

1. **기존 시나리오 확장** (`same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다`):
   - conflict-visibility 완료 후 `page.reload({ waitUntil: "networkidle" })` 실행
   - `page.evaluate`로 test session을 다시 로드
   - reload 후 aggregate-trigger box visible 확인, `검토 메모 적용 후보` label 확인
   - `충돌 확인 완료` badge (conflict-visibility record의 canonical_transition_id, conflict_entry_count) 확인
   - `적용 되돌림 완료` badge (transition record의 canonical_transition_id) 확인
   - helper text `충돌 확인이 완료되었습니다.` 확인
   - API payload 재검증: transition record `record_stage = reversed`, conflict-visibility record `record_stage = conflict_visibility_checked`, 동일 canonical_transition_id, 동일 conflict_entry_count
2. **timeout 90초로 조정**: full lifecycle + reload 추가로 인한 시나리오 길이 증가 반영 (실측 50.6초)

## Production 파일 미변경 사유

reload 후 aggregate-trigger UI가 정상 렌더링되어 production 코드 버그 없음. `app/static/app.js` 및 docs 변경 불필요.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate는 separate blocked trigger surface로 렌더링됩니다" --reporter=line` → 1 passed (50.6s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs app/static/app.js docs/NEXT_STEPS.md docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md work/4/16` → clean

## 남은 리스크

- reload continuity는 conflict-checked 최종 상태에서만 검증했습니다. 중간 lifecycle 상태(emitted, applied, stopped 등) 에서의 reload는 별도 시나리오 확장 시 커버 가능하나, 현재 shipped contract의 핵심 reload path는 이번 라운드로 고정됩니다.
- full Playwright suite 미실행: 기존 시나리오 확장이므로 shared browser helper 전체에 대한 regression 가능성은 낮음.
