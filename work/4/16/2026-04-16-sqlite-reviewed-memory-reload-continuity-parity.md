# sqlite-reviewed-memory-reload-continuity-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 reviewed-memory 전체 service-level lifecycle (emit → apply → confirm → stop → reverse → conflict)을 검증함. 남은 same-family current-risk는 각 lifecycle 단계 이후 SQLite에서 세션을 다시 읽고 재직렬화했을 때 persisted state가 정확히 보존되는지 (reload continuity)의 검증 부재.

## 핵심 변경

1. **`tests/test_web_app.py`**: `test_recurrence_aggregate_reload_continuity_with_sqlite_backend` 추가.
   - `storage_backend='sqlite'`에서 full lifecycle의 각 단계 이후 `service.get_session_payload(session_id)` 호출로 SQLite re-read + re-serialize 검증:
     - emit 후 reload: `reviewed_memory_transition_record.record_stage = emitted_record_only_not_applied`, active effects 없음
     - apply 후 reload: `record_stage = applied_pending_result`, active effects 없음
     - confirm 후 reload: `record_stage = applied_with_result`, `apply_result.result_stage = effect_active`, `reviewed_memory_active_effects` 1건
     - stop 후 reload: active effects 제거 확인
     - reverse 후 reload: `record_stage = reversed`, `result_stage = effect_reversed`, active effects 없음
     - conflict-visibility 후 reload: `reviewed_memory_conflict_visibility_record.record_stage = conflict_visibility_checked` (있는 경우)

2. **추가 구현 변경 없음**: `get_session_payload`는 `session_store.get_session()` + `_serialize_session()`을 호출하며, 이전 라운드에서 바인딩한 `SessionStore` 메서드와 SQLite의 JSON blob 저장/복원이 정상 동작하여 blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_stop_reverse_conflict_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reload_continuity_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/handlers/aggregate.py app/serializers.py app/web.py  # clean
git diff --check -- (all specified files)  # clean
```

## 남은 리스크

- Playwright / browser-level reload 검증은 이번 슬라이스에 미포함 — service-level `get_session_payload()` 재직렬화로 bounded.
- SQLite 백엔드에서 reviewed-memory 전체 lifecycle + reload continuity가 검증 완료됨. 남은 SQLite parity gap은 non-reviewed-memory 경로 (content_verdict, content_reason_note 등)에 해당.
