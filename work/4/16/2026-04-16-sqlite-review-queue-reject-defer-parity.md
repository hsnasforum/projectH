# sqlite-review-queue-reject-defer-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 content verdict reject + reason note 경로가 service-level + reload persistence 기준으로 검증됨. 같은 sqlite parity 축에서 남은 가장 user-visible한 current-risk는 shipped review queue `reject` / `defer` 경로: JSON-side regression은 있으나 SQLite 백엔드 parity test가 없었음.

## 핵심 변경

1. **`test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend`**: SQLite 백엔드에서 candidate confirmation 후 review queue item이 생기고, `submit_candidate_review(..., review_action="reject")` 호출 후:
   - `candidate_review_record.review_action = reject`, `review_status = rejected` 확인
   - `review_queue_items` 비어 있음 확인
   - `get_session_payload()` reload 후 queue item 제거 유지, `candidate_review_record` 동일 상태 보존 확인

2. **`test_submit_candidate_review_defer_records_and_removes_queue_item_with_sqlite_backend`**: SQLite 백엔드에서 동일 흐름으로 `review_action="defer"` 호출 후:
   - `candidate_review_record.review_action = defer`, `review_status = deferred` 확인
   - `review_queue_items` 비어 있음 확인
   - `get_session_payload()` reload 후 queue item 제거 유지, `candidate_review_record` 동일 상태 보존 확인

3. **추가 구현 변경 없음**: `SQLiteSessionStore.record_candidate_review_for_message`는 이미 `SessionStore`에서 바인딩되어 있어 blocker 없이 정상 동작.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_defer_records_and_removes_queue_item_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py  # clean
git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 review queue `reject` / `defer` 경로가 service-level + reload persistence로 검증됨.
- `accept` 경로는 이전 라운드에서 이미 검증 완료.
- invalid-action parity, reviewed-memory aggregate sqlite parity, browser-level sqlite smoke는 이번 슬라이스 scope 밖.
- direct SQLite `task_log` 테이블 row 내용 검증은 별도 audit-depth 리스크로 남아 있음.
