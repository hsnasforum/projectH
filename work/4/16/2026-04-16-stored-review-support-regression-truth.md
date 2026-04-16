# stored review-support regression truth bundle

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 sanitize 구현(core/contracts.py helper + handler/serializer wiring)은 코드 레벨에서 올바르지만, `test_stored_transition_record_reject_defer_review_refs_sanitized_on_reload`가 `emit_aggregate_transition()`을 호출하지 않아 `reviewed_memory_emitted_transition_records`가 실제로 생성되지 않았습니다. 따라서 stored record 경로의 sanitize 검증이 false-green이었습니다. 이번 라운드는 regression을 truthful하게 만들어 shipped reviewed-memory reload contract의 자동화 커버리지 gap을 닫습니다.

## 핵심 변경

1. **`test_stored_transition_record_reject_defer_review_refs_sanitized_on_reload` 수정**: `emit_aggregate_transition()` 호출 추가 → stored `reviewed_memory_emitted_transition_records` 실제 생성 → reject ref 주입 후 reload 시 transition record가 존재하고(`assertIsNotNone`) reject ref가 제거됨을 검증. 기존의 `if ... is not None` soft guard를 `assertIsNotNone` hard assertion으로 교체.
2. **`test_stored_conflict_visibility_record_reject_defer_review_refs_sanitized_on_reload` 신규 추가**: full lifecycle(emit → apply → confirm → stop → reverse → conflict-visibility) 실행 → stored conflict-visibility record 실제 생성 → reject/defer ref 주입 후 reload 시 conflict-visibility record가 존재하고 reject/defer ref가 제거됨을 검증.

## Production 파일 미변경 사유

수정된 regression이 모두 pass하므로, `core/contracts.py`/`app/serializers.py`/`app/handlers/aggregate.py`의 기존 sanitize 구현이 올바름을 확인했습니다. 이번 라운드는 false-green regression gap만 닫는 test-only 변경입니다.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_stored_transition_record_reject_defer_review_refs_sanitized_on_reload` → OK
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_stored_conflict_visibility_record_reject_defer_review_refs_sanitized_on_reload` → OK
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs` → OK
- `git diff --check -- tests/test_web_app.py app/handlers/aggregate.py app/serializers.py core/contracts.py work/4/16` → clean

## 남은 리스크

- stored review-support sanitize 경로는 이제 transition record와 conflict-visibility record 모두 truthful regression으로 커버됩니다.
- apply/stop-apply/reversal 중간 단계의 stored record에 대한 reject/defer ref 주입 테스트는 추가하지 않았으나, 이들 중간 단계는 transition_action이 `future_reviewed_memory_apply`이므로 이미 transition record sanitize 경로에 포함됩니다.
