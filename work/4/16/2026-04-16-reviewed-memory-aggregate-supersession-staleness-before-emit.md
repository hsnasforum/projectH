# reviewed-memory-aggregate-supersession-staleness-before-emit

## 변경 파일

- `app/serializers.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

`검토 메모 적용 후보` aggregate가 transition emit 전에 superseded correction을 포함한 채 남아 있으면, 더 이상 유효하지 않은 교정 범위를 대상으로 적용이 시작될 수 있음. same-family current-risk reduction으로 Gemini arbitration (seq 204)에서 선정.

## 핵심 변경

1. **serializer explicit staleness validation** (`app/serializers.py`):
   - `_build_recurrence_aggregate_candidates`에 `current_candidate_index` 구축 단계 추가: 각 message의 `(artifact_id, source_message_id)` → current `(candidate_id, updated_at)` 매핑
   - aggregate 구성 직전에 각 member의 `candidate_id` + `candidate_updated_at`가 해당 anchor의 current session_local_candidate와 일치하는지 검증
   - 불일치 시 해당 aggregate를 `recurrence_aggregate_candidates`에서 완전히 제거 (stale badge 없이 retire)

2. **focused service regression** (`tests/test_web_app.py`):
   - `test_recurrence_aggregate_candidate_retires_on_superseding_correction_before_emit`: 두 교정으로 aggregate 생성 → 한쪽 교정을 다른 텍스트로 supersede → aggregate가 사라지는지 검증

3. **Playwright smoke** (`e2e/tests/web-smoke.spec.mjs`):
   - `same-session recurrence aggregate stale candidate retires before apply start`: 브라우저에서 aggregate card 표시 → API로 한쪽 교정 supersede → payload에 aggregate 없음 → UI에서 card hidden 확인

4. **docs sync**: README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA, TASK_BACKLOG에 aggregate가 current-version only이며 superseding correction 시 transition emit 전에 retire된다는 서술 추가

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidate_retires_on_superseding_correction_before_emit` → ok (5.6s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate stale candidate retires before apply start" --reporter=line` → 1 passed (23.4s)
- `git diff --check -- app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` → clean
- full Playwright suite 미실행: production code 변경은 serializer-only safety net이며 기존 aggregate lifecycle 경로를 변경하지 않으므로 isolated rerun이 가장 좁은 truthful check

## 남은 리스크

- explicit staleness validation은 현재 코드에서 이미 자연적으로 retire되는 동작의 safety net임 (recurrence key가 current session_local_candidate에서 매번 재계산되므로 fingerprint 변경 시 자연 retire). 향후 candidate resolution 로직이 변경되면 이 safety net이 실제 보호 역할을 할 수 있음.
- `app/static/app.js` 미변경: aggregate가 사라질 때 빈 상태 처리는 기존 `showElement(aggregateTriggerBox, aggregateItems.length > 0)` 로직이 이미 처리함.
- reject/defer UI coexistence parity는 이번 slice 범위 밖이며 다음 same-family 후보로 남아 있음.
