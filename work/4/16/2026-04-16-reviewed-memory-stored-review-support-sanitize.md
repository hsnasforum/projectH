# reviewed-memory stored review-support sanitize bundle

## 변경 파일

- `core/contracts.py`
- `app/serializers.py`
- `app/handlers/aggregate.py`
- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 aggregate live-path `supporting_review_refs`를 accept-only로 제한했지만, 이미 저장된 `reviewed_memory_emitted_transition_records`와 `reviewed_memory_conflict_visibility_record`에는 pre-fix reject/defer review ref가 남아 있어 reload 시 그대로 노출될 수 있었습니다. 이번 라운드는 write-time과 read-time 모두에서 같은 accept-only 규칙을 적용하는 shared sanitizer를 추가하여, 저장된 기록에서도 reject/defer support ref가 재노출되지 않도록 합니다.

## 핵심 변경

1. **`core/contracts.py`**: `sanitize_supporting_review_refs()` 공유 함수 추가. `review_action == "accept"`인 ref만 반환, reject/defer는 필터링.
2. **`app/handlers/aggregate.py`**: transition record 발행(line 269)과 conflict-visibility record 발행(line 656)에서 기존 inline 복사 대신 `sanitize_supporting_review_refs()` 사용.
3. **`app/serializers.py`**: `_build_recurrence_aggregate_reviewed_memory_transition_record()`와 `_build_recurrence_aggregate_reviewed_memory_conflict_visibility_record()`에서 stored record 반환 직전 `sanitize_supporting_review_refs()` 적용. reject/defer ref가 있으면 제거, 빈 list면 key 자체 제거.
4. **`tests/test_web_app.py`**: `test_stored_transition_record_reject_defer_review_refs_sanitized_on_reload` 신규 추가. 정상 aggregate 구성 후 stored transition record에 reject ref 수동 주입 → reload 시 reject ref 미노출 검증.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs` → OK
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_stored_transition_record_reject_defer_review_refs_sanitized_on_reload` → OK
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_keep_candidate_review_as_support_only` → OK
- `python3 -m unittest -v tests.test_contracts` → 45 tests OK
- `git diff --check -- app/handlers/aggregate.py app/serializers.py core/contracts.py tests/test_web_app.py work/4/16` → clean

## Docs 미변경 사유

이전 라운드에서 이미 root docs 4개에 "accept-only support, reject/defer audit-only" 규칙을 명시했습니다. 이번 라운드는 저장된 기록의 read-time 정합성만 보강하는 것이므로, docs에서 이미 accept-only로 기술된 규칙은 별도 갱신 불필요합니다.

## 남은 리스크

- `app/serializers.py`의 다른 downstream method들(`_build_recurrence_aggregate_reviewed_memory_applied_effect_target`, `_build_recurrence_aggregate_reviewed_memory_reversible_effect_handle` 등)도 `supporting_review_refs`를 전달하지만, 이들은 상위에서 이미 sanitize된 aggregate를 입력으로 받으므로 별도 sanitize 불필요합니다.
- `storage/session_store.py`는 변경하지 않았습니다. 저장 시점의 raw JSON은 그대로 유지되며, read-time sanitize로 충분합니다.
