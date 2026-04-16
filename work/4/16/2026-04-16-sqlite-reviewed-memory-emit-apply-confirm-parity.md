# sqlite-reviewed-memory-emit-apply-confirm-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 grounded-brief serialization 경로와 accepted-reviewed-candidate → preference candidate 저장 경로의 parity를 복원함. 다음 current-risk는 SQLite 백엔드에서 shipped reviewed-memory lifecycle (emit → apply → confirm → active-effect)의 검증 부재였음.

## 핵심 변경

1. **`tests/test_web_app.py`**: `test_recurrence_aggregate_emit_apply_confirm_active_effect_with_sqlite_backend` 추가.
   - `storage_backend='sqlite'`에서 전체 lifecycle 검증:
     - 두 개의 grounded-brief에 동일 corrected text 적용
     - 첫 번째: correction → corrected save → approve → candidate confirm → review accept
     - 두 번째: correction → recurrence aggregate 출현 (`unblocked_all_required`)
     - `emit_aggregate_transition` → `record_stage = emitted_record_only_not_applied`
     - `apply_aggregate_transition` → `record_stage = applied_pending_result`
     - `confirm_aggregate_transition_result` → `record_stage = applied_with_result`, `result_stage = effect_active`
     - `reviewed_memory_active_effects` 1건 존재 확인

2. **추가 구현 변경 없음**: 이전 라운드에서 `SQLiteSessionStore`에 바인딩한 `SessionStore` 메서드들과 aggregate handler의 직접적인 session dict 조작이 그대로 동작하여, 새 sqlite seam blocker가 발견되지 않았음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_emit_apply_confirm_active_effect_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/handlers/aggregate.py app/serializers.py app/web.py  # clean
git diff --check -- (all specified files)  # clean
```

## 남은 리스크

- SQLite 백엔드에서 stop-apply, reversal, conflict-visibility 경로는 이번 슬라이스에서 검증하지 않음 (handoff scope limit).
- aggregate handler의 `session_store._save()` 직접 호출이 SQLite에서도 정상 동작하나, `_save` 호출 전후 session dict 정합성이 SQLite commit timing에 민감할 수 있는 edge case는 미확인.
- Playwright / browser-level 검증은 이번 슬라이스에 포함되지 않음 — service-level regression으로 bounded.
