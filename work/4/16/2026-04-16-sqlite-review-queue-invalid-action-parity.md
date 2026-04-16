# sqlite-review-queue-invalid-action-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 review queue `reject` / `defer` happy-path persistence가 검증됨. 같은 review-queue family에서 남은 current-risk는 `submit_candidate_review`의 invalid action error guard: JSON-side regression은 있으나 SQLite 백엔드 parity test가 없었음.

## 핵심 변경

1. **`test_submit_candidate_review_rejects_invalid_action_with_sqlite_backend`**: SQLite 백엔드에서 `submit_candidate_review(..., review_action="bogus")` 호출 시:
   - `WebApiError` 발생 확인
   - `status_code == 400` 확인
   - error message에 `지원하지 않는 review action` 포함 확인

2. **추가 구현 변경 없음**: `submit_candidate_review`의 action validation은 `AggregateHandler` 서비스 레이어에서 처리되며 storage backend와 무관하게 동작. SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_rejects_invalid_action_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py  # clean
git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 review queue family 전체 (`accept` / `reject` / `defer` happy-path + `invalid_action` guard)가 service-level parity로 검증됨.
- content-side blank-note validation, direct SQLite `task_log` table inspection, browser-level sqlite smoke는 이번 슬라이스 scope 밖.
