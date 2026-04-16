# reviewed-memory-aggregate-review-support-visibility-after-reject-defer

## 변경 파일

- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

aggregate card가 source-message `reject` / `defer` review outcome과 공존할 때, 사용자에게 accepted review support 상태가 보이지 않아 aggregate가 왜 여전히 존재하는지, reject/defer가 aggregate에 어떤 영향을 주는지 불분명함. same-family user-visible clarity improvement.

## 핵심 변경

1. **aggregate card review-support line** (`app/static/app.js`):
   - 각 aggregate card에 `data-testid="aggregate-trigger-review-support"` 요소 추가
   - `supporting_review_refs` (accept-only) 길이와 `recurrence_count`로 `검토 수락 N건 / 교정 M건 (거절·보류는 감사 기록만)` 표시
   - 기존 identity summary와 planning target 사이에 배치

2. **Playwright smoke** (`e2e/tests/web-smoke.spec.mjs`):
   - `review-queue reject-defer aggregate support visibility`: 두 교정 → 첫째 reject, 둘째 defer → aggregate card visible → `검토 수락 0건 / 교정 2건 (거절·보류는 감사 기록만)` 확인 → payload에 `supporting_review_refs` 없음 확인

3. **docs sync**: README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA, TASK_BACKLOG에 aggregate card의 visible review-support line 서술 추가

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs` → ok (2.8s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review-queue reject-defer aggregate support visibility" --reporter=line` → 1 passed (27.9s)
- `git diff --check -- app/static/app.js app/serializers.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` → clean
- `app/serializers.py` 미변경: 기존 `supporting_review_refs` (accept-only)와 `recurrence_count` payload가 이미 충분하여 새 serializer field 불필요
- `tests/test_web_app.py` 미변경: 기존 `test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs`가 acceptance-only support baseline으로 재사용됨
- full Playwright suite 미실행: UI-only 변경이며 aggregate card rendering에 국한. 기존 aggregate lifecycle 경로는 변경되지 않음.

## 남은 리스크

- review-support line은 항상 표시되므로 accept가 0건인 경우에도 보임. 이는 의도된 동작으로, reject/defer가 aggregate support에 포함되지 않는다는 계약을 사용자에게 명시적으로 전달.
- `app/handlers/aggregate.py` 미변경: 새 workflow state나 eligibility 변경 없음.
- 기존 aggregate lifecycle smoke (emitted-apply-confirm, stop-reverse-conflict, stale-retire, lifecycle-survives-supersession)는 이번 변경에 영향받지 않으나, review-support line이 추가되어 해당 시나리오에서도 자동으로 표시됨.
