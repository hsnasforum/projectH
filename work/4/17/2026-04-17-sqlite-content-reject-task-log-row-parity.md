# sqlite-content-reject-task-log-row-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

SQLite 백엔드에서 content reject/reason family의 service-level parity와 reload persistence는 이미 검증됨. 그러나 `SQLiteTaskLogger`가 실제로 `task_log` 테이블에 올바른 action과 detail을 기록하는지는 직접 확인된 적이 없었음. JSON-side 테스트는 raw `.jsonl` 텍스트 검색으로 task_log 기록을 검증하지만, SQLite-side 테스트는 service payload만 확인하고 task_log row를 검사하지 않았음.

## 핵심 변경

1. **`test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend`** 확장:
   - `service.task_logger.iter_session_records("sqlite-verdict")`로 직접 task_log row 조회
   - `content_verdict_recorded` action row 1건 존재 확인
   - detail 내 `message_id`, `artifact_id`, `artifact_kind`, `source_message_id`, `content_verdict`, `content_reason_record.reason_label` 정합성 검증
   - `corrected_outcome_recorded` action row 1건 존재 확인
   - detail 내 `outcome`, `artifact_id`, `source_message_id`, `content_reason_record.reason_label` 정합성 검증

2. **`test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend`** 확장:
   - `service.task_logger.iter_session_records("sqlite-reason")`로 직접 task_log row 조회
   - `content_reason_note_recorded` action row 1건 존재 확인
   - detail 내 `message_id`, `artifact_id`, `artifact_kind`, `source_message_id`, `reason_scope`, `reason_label`, `reason_note`, `content_reason_record` 정합성 검증
   - 선행 `content_verdict_recorded` row도 동일 세션에 존재하고 `content_verdict = rejected` 확인

3. **추가 구현 변경 없음**: `SQLiteTaskLogger.iter_session_records()`가 이미 parsed detail을 포함한 row를 반환하며, 기존 `FeedbackHandler`의 logging 경로가 SQLite backend에서도 blocker 없이 정상 동작.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_after_original_draft_save_preserves_saved_history_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py  # clean
git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py  # clean
```

## 남은 리스크

- SQLite `task_log` row 내용이 `content_verdict_recorded`, `corrected_outcome_recorded`, `content_reason_note_recorded` 세 action에 대해 직접 검증됨.
- content family 전체: reject/reason happy-path + blank-note guard + late-flip save-history + task_log row parity 모두 sqlite 검증 완료.
- `superseded_reject_signal` / audit replay helper / browser-level sqlite smoke는 이번 슬라이스 scope 밖.
- 구현 변경 없이 테스트만 확장했으므로 기존 동작 회귀 리스크 없음.
