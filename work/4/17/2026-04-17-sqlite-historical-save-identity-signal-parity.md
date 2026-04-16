# sqlite-historical-save-identity-signal-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 `superseded_reject_signal` replay parity가 두 계약 모두 검증됨. 같은 serializer/task-log replay family에서 남은 가장 직접적인 current-risk는 save-side replay helper: JSON-backed 테스트에서는 `historical_save_identity_signal`이 persisted `write_note` history에서 올바르게 replay하고 `approval_granted`만으로는 emit하지 않는 것을 검증하지만, SQLite-backed peer가 없었음.

## 핵심 변경

1. **`test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend`**: SQLite 백엔드에서 save → approve → correction 순서 실행 후:
   - approve 직후: `session_local_memory_signal.save_signal.latest_approval_id` 존재, `historical_save_identity_signal` 미생성 확인
   - correction 후: current `save_signal`에 `latest_save_content_source = original_draft`, `latest_saved_note_path` 유지, `latest_approval_id` 미포함 확인
   - `historical_save_identity_signal.replay_source = task_log_audit`
   - `historical_save_identity_signal.approval_id`, `save_content_source`, `saved_note_path`, `recorded_at` 정합성 확인

2. **`test_historical_save_identity_signal_requires_same_anchor_write_note_not_approval_granted_only_with_sqlite_backend`**: SQLite 백엔드에서 manual `approval_granted` task_log row만 존재하고 matching persisted `write_note`가 없을 때:
   - `historical_save_identity_signal` 미생성 확인 (`assertNotIn`)
   - current `save_signal`은 정상 유지 확인

3. **추가 구현 변경 없음**: 기존 `_build_historical_save_identity_signal_index()`가 `_iter_task_log_records()`를 통해 SQLite task_log를 읽으며, `write_note` action 필터링이 backend와 무관하게 정상 동작. SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_requires_same_anchor_write_note_not_approval_granted_only_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend  # OK
python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py  # clean
git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 `historical_save_identity_signal` replay parity가 두 계약 모두 검증됨: latest same-anchor write_note replay + approval_granted-only exclusion.
- serializer/task-log replay family 전체: `superseded_reject_signal` 2건 + `historical_save_identity_signal` 2건 모두 sqlite 검증 완료.
- browser-level sqlite smoke, reviewed-memory/review-queue 외 axis parity는 이번 슬라이스 scope 밖.
- 구현 변경 없이 테스트만 추가했으므로 기존 동작 회귀 리스크 없음.
