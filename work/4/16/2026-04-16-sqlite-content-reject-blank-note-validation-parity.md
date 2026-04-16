# sqlite-content-reject-blank-note-validation-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 review queue family 전체 (`accept`/`reject`/`defer` happy-path + `invalid_action` guard)가 검증됨. 같은 sqlite parity 축에서 남은 가장 user-facing한 current-risk는 content-side `submit_content_reason_note` blank note validation guard: JSON-side regression은 있으나 SQLite 백엔드 parity test가 없었음.

## 핵심 변경

1. **`test_submit_content_reason_note_rejects_blank_note_with_sqlite_backend`**: SQLite 백엔드에서 grounded-brief 메시지에 `content_verdict = rejected` 제출 후, `submit_content_reason_note(..., reason_note="   \n  ")` 호출 시:
   - `WebApiError` 발생 확인
   - `status_code == 400` 확인
   - error message에 `거절 메모를 입력해 주세요.` 포함 확인

2. **추가 구현 변경 없음**: blank note validation은 `ContentHandler` 서비스 레이어에서 처리되며 storage backend와 무관하게 동작. SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_reason_note_rejects_blank_note_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py  # clean
git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 content-side validation guard (`blank note`)가 service-level parity로 검증됨.
- review queue family + content reject/reason happy-path + content blank-note guard가 모두 sqlite parity 검증 완료.
- direct SQLite `task_log` table inspection, browser-level sqlite smoke는 이번 슬라이스 scope 밖.
