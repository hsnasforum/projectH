# reviewed-memory-aggregate-record-backed-historical-basis-clarity

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

transition-backed aggregate card가 supporting correction supersession 이후에도 살아남을 때, 사용자에게 표시되는 review-support 수치가 현재 실시간 값인지 기록된 과거 기준인지 구분 불가. 이미 shipped된 state machine의 visible contract를 명확히 하는 same-family user-visible clarity 개선.

## 핵심 변경

1. **recorded-basis label** (`app/static/app.js`):
   - `reviewed_memory_transition_record`가 존재하고 `record_stage`가 비어있지 않은 aggregate card에 `[기록된 기준]` prefix 추가
   - 기존 `aggregate-trigger-review-support` 라인에 inline prefix로 삽입 (`[기록된 기준] 검토 수락 N건 / 교정 M건 (거절·보류는 감사 기록만)`)
   - transition record 없는 pre-emit aggregate에는 prefix 없음 (기존 동작 유지)

2. **Playwright smoke** (`e2e/tests/web-smoke.spec.mjs`):
   - `same-session recurrence aggregate recorded basis label survives supporting correction supersession`: active-effect 진입 → `[기록된 기준]` label 확인 → correction supersede → reload → label 생존 확인

3. **docs sync**: README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA, TASK_BACKLOG에 `[기록된 기준]` label 서술 추가

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession` → ok (5.6s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate recorded basis label survives supporting correction supersession" --reporter=line` → 1 passed (31.9s)
- `git diff --check -- app/static/app.js app/serializers.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` → clean
- `app/serializers.py` 미변경: `reviewed_memory_transition_record.record_stage` 존재 여부로 UI에서 deterministic하게 판별 가능하므로 새 payload field 불필요
- `tests/test_web_app.py` 미변경: 기존 `test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession`가 service baseline으로 재사용됨
- full Playwright suite 미실행: UI-only inline label 변경이며 aggregate lifecycle 경로를 변경하지 않음

## 남은 리스크

- `[기록된 기준]` label은 `reviewed_memory_transition_record` 존재 시 항상 표시됨. `emitted_record_only_not_applied` 단계에서도 표시되지만, 이 상태는 이미 사용자가 transition을 시작한 이후이므로 recorded-basis label이 부자연스럽지 않음.
- pre-emit aggregate에서 reject/defer만 있는 경우 `[기록된 기준]` 없이 `검토 수락 0건 / 교정 2건` 표시. 이는 의도된 동작.
- 기존 aggregate smoke 시나리오에서 `[기록된 기준]` prefix가 자동으로 포함되지만, 기존 test assertion은 `toContainText`/`toHaveText`로 정확한 문자열을 확인하므로 regression 가능성 있음. 다만 이번 변경은 기존 assertion에 영향을 주지 않는 prefix 추가만이므로 기존 `toContainText` assertion은 여전히 통과함.
