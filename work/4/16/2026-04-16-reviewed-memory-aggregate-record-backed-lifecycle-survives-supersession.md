# reviewed-memory-aggregate-record-backed-lifecycle-survives-supporting-correction-supersession

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

seq 205의 stale-retire guard가 pre-emit aggregate를 정확하게 제거하지만, emit → apply → confirm 이후에도 supporting correction이 supersede되면 aggregate card를 함께 숨겨서 shipped stop / reverse / conflict control loop가 동작하지 않는 regression 발생. active effect가 orphan되면 사용자가 중단이나 되돌리기를 할 수 없음.

## 핵심 변경

1. **record-backed aggregate reconstruction** (`app/serializers.py`, `_build_recurrence_aggregate_candidates`):
   - `emitted_transition_records`에서 record-backed fingerprint set 구축
   - main loop: 2+ member가 있고 record-backed fingerprint라면 stale check 건너뜀
   - second pass: member count < 2로 main loop에서 탈락한 record-backed fingerprint에 대해 stored transition record의 `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs`로 synthetic aggregate 재구성
   - 재구성된 aggregate에 모든 기존 contract/capability/transition-record builder 적용

2. **transition record builder bypass** (`app/serializers.py`, `_build_recurrence_aggregate_reviewed_memory_transition_record`):
   - stored record의 `record_stage`가 `emitted_record_only_not_applied`를 지났으면 (applied/stopped/reversed 등) capability gate 건너뜀
   - emitted-only 상태이거나 stored record가 없는 경우 기존 capability/audit contract check 유지

3. **focused service regression** (`tests/test_web_app.py`):
   - `test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession`: emit → apply → confirm 후 supporting correction supersede → aggregate card 유지, transition_record 유지, active_effects 유지, 이후 stop까지 정상 동작 검증

4. **Playwright smoke** (`e2e/tests/web-smoke.spec.mjs`):
   - `same-session recurrence aggregate active lifecycle survives supporting correction supersession`: active-effect 상태에서 API로 correction supersede → payload에 aggregate/transition_record/active_effects 유지 → UI에서 card visible → stop 버튼 동작 확인

5. **docs sync**: README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA, TASK_BACKLOG에 record-backed lifecycle aggregate가 supersession에서 살아남는다는 서술 추가

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidate_retires_on_superseding_correction_before_emit` → ok
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession` → ok
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate stale candidate retires before apply start" --reporter=line` → 1 passed (22.2s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate active lifecycle survives supporting correction supersession" --reporter=line` → 1 passed (35.1s)
- `git diff --check -- app/serializers.py app/handlers/aggregate.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` → clean
- 기존 lifecycle test 3종 regression 확인: `test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle`, `test_recurrence_aggregate_contract_refs_retained_through_lifecycle`, `test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle` → 3 ok
- full Playwright suite 미실행: serializer 변경이 record-backed aggregate reconstruction과 transition record capability gate에 국한되며, 기존 lifecycle 경로의 동작은 unit test 3종으로 확인함. 이번 라운드는 기존 shipped contract를 유지하면서 regression만 수정하므로 isolated rerun이 가장 좁은 truthful check.

## 남은 리스크

- record-backed aggregate의 `supporting_source_message_refs`와 `supporting_candidate_refs`는 stored transition record의 원본 snapshot을 사용함. 현재 메시지 상태와 일치하지 않을 수 있지만, lifecycle control surface (stop/reverse/conflict)의 가시성이 우선이므로 의도된 동작.
- second pass에서 contract builder를 반복 호출하는 코드가 main loop와 중복됨. 향후 리팩터링에서 공통 helper로 추출 가능하지만 현재 round에서는 기능 변경 없이 scope를 줄이는 편이 안전함.
- `app/handlers/aggregate.py` 미변경: handler는 session 저장소에서 stored transition record를 직접 찾으므로 serializer-only reconstruction으로 충분함.
- `app/static/app.js` 미변경: 기존 aggregate rendering 로직이 `recurrence_aggregate_candidates` 배열 유무로 card visibility를 판단하므로 추가 변경 불필요.
- reject/defer UI coexistence parity는 이번 slice 범위 밖.
