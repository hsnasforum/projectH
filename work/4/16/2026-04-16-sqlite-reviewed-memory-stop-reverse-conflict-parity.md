# sqlite-reviewed-memory-stop-reverse-conflict-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 reviewed-memory emit → apply → confirm → active-effect 진입 경로를 검증함. 남은 same-family current-risk는 post-confirm lifecycle (stop-apply, reversal, conflict-visibility)의 SQLite 검증 부재.

## 핵심 변경

1. **`tests/test_web_app.py`**: `test_recurrence_aggregate_stop_reverse_conflict_with_sqlite_backend` 추가.
   - `storage_backend='sqlite'`에서 post-confirm lifecycle 검증:
     - 두 개의 grounded-brief 동일 교정 → aggregate 출현 → emit → apply → confirm (setup)
     - `stop_apply_aggregate_transition` → `record_stage = stopped`, `result_stage = effect_stopped`, `reviewed_memory_active_effects` 제거 확인
     - `reverse_aggregate_transition` → `record_stage = reversed`, `result_stage = effect_reversed`, active effects 여전히 비어있음 확인
     - `check_aggregate_conflict_visibility` → `ok = True`, conflict_visibility_record가 있을 때 `record_stage = conflict_visibility_checked` 확인

2. **추가 구현 변경 없음**: 이전 라운드에서 바인딩한 `SessionStore` 메서드와 aggregate handler의 직접 session dict 조작이 post-confirm lifecycle에서도 SQLite blocker 없이 정상 동작.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_emit_apply_confirm_active_effect_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_stop_reverse_conflict_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/handlers/aggregate.py app/serializers.py app/web.py  # clean
git diff --check -- (all specified files)  # clean
```

## 남은 리스크

- SQLite 백엔드 전체 reviewed-memory lifecycle (emit → apply → confirm → stop → reverse → conflict)이 service-level에서 검증 완료됨. Playwright / browser-level 검증은 미포함 — 이번 슬라이스 scope 밖.
- reload continuity (페이지 새로고침 후 aggregate-trigger UI 복원)는 SQLite 전용으로 검증하지 않음 — JSON 백엔드 기준 기존 Playwright smoke에서 커버됨.
- SQLite 백엔드에서 reviewed-memory와 preference persistence가 모두 검증되었으므로, 남은 SQLite parity gap은 주로 non-reviewed-memory 경로(예: content_verdict, content_reason_note 등)에 해당.
