# sqlite-content-reject-reason-trace-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 reviewed-memory lifecycle + reload continuity 검증을 완료함. 남은 SQLite current-risk 중 가장 직접적인 것은 shipped feedback trace 경로 (`submit_content_verdict` + `submit_content_reason_note`)의 검증 부재. `SQLiteSessionStore`에는 이미 `record_rejected_content_verdict_for_message`와 `record_content_reason_note_for_message`가 `SessionStore`에서 바인딩되어 있으나, service-level regression이 없었음.

## 핵심 변경

1. **`test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend`**: SQLite 백엔드에서 grounded-brief 메시지에 `content_verdict = rejected` 제출 후:
   - `corrected_outcome.outcome = rejected`, `artifact_id`, `source_message_id` 정합성 확인
   - `content_reason_record.reason_scope = content_reject`, `reason_label = explicit_content_rejection`, `reason_note = None` 확인
   - `get_session_payload()` reload 후 동일 상태 보존 확인

2. **`test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend`**: SQLite 백엔드에서 reject 후 `submit_content_reason_note` 호출:
   - `content_reason_record.reason_note` 업데이트 확인
   - `corrected_outcome.recorded_at` 불변 확인 (reject 시점 타임스탬프 보존)
   - `get_session_payload()` reload 후 동일 상태 보존 확인

3. **추가 구현 변경 없음**: 이전 라운드에서 바인딩한 `SessionStore` 메서드가 blocker 없이 정상 동작.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py  # clean
git diff --check -- (all specified files)  # clean
```

## 남은 리스크

- SQLite 백엔드에서 `content_verdict = rejected` + `content_reason_note` 경로가 service-level + reload persistence로 검증됨.
- candidate review reject/defer의 SQLite parity는 이번 슬라이스 scope 밖.
- task log 내용 검증은 SQLite `SQLiteTaskLogger`를 통해 기록되며 직접 텍스트 확인은 생략 (JSON 기반 task_log.jsonl이 아닌 SQLite task_log 테이블 사용).
