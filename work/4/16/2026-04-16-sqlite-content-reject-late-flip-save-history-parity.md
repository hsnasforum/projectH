# sqlite-content-reject-late-flip-save-history-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 content reject/reason happy-path + blank-note validation guard가 검증됨. 같은 content family에서 남은 가장 user-facing한 current-risk는 late-flip 계약: original-draft save가 완료된 뒤 `submit_content_verdict(..., "rejected")`를 해도 이미 저장된 노트 파일과 save history가 보존되어야 하는 경로. JSON-side regression은 있으나 SQLite 백엔드 parity test가 없었음.

## 핵심 변경

1. **`test_submit_content_verdict_after_original_draft_save_preserves_saved_history_with_sqlite_backend`**: SQLite 백엔드에서 `save_summary=True` + `approved=True`로 original-draft save 완료 후, 같은 source message에 `content_verdict="rejected"` 제출 시:
   - 저장된 노트 파일이 여전히 존재하고 내용 불변 확인
   - source message에 `saved_note_path` 유지 확인
   - `corrected_outcome.outcome = rejected` 확인
   - `corrected_outcome.saved_note_path = None` 확인 (late reject가 save history를 덮어쓰지 않음)
   - saved-note message가 같은 artifact를 가리키고 `save_content_source = original_draft` 유지 확인

2. **추가 구현 변경 없음**: late-flip save-history 보존 로직은 기존 `ContentHandler` + `SessionStore` 경로에서 storage backend와 무관하게 동작. SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_after_original_draft_save_preserves_saved_history_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py  # clean
git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 content reject late-flip save-history 보존이 service-level parity로 검증됨.
- content family 전체: reject/reason happy-path + blank-note guard + late-flip save-history 모두 sqlite parity 완료.
- review queue family 전체: accept/reject/defer happy-path + invalid_action guard 모두 sqlite parity 완료.
- direct SQLite `task_log` table inspection, `superseded_reject_signal`/audit replay, browser-level sqlite smoke는 이번 슬라이스 scope 밖.
