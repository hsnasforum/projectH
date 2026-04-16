# sqlite-superseded-reject-signal-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 content reject/reason family에 대해 service-level parity, reload persistence, 직접 task_log row 검증까지 모두 완료됨. 같은 family에서 남은 가장 직접적인 current-risk는 replay parity: JSON-backed 테스트에서는 `superseded_reject_signal`이 later correction 이후 이전 reject outcome/note를 올바르게 replay하고 ambiguous note association을 제외하는 것을 검증하지만, SQLite-backed peer가 없었음.

## 핵심 변경

1. **`test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend`**: SQLite 백엔드에서 reject → reason note → correction 순서 실행 후:
   - `session_local_memory_signal.content_signal.latest_corrected_outcome.outcome = corrected` 유지
   - `session_local_memory_signal.content_signal`에 `content_reason_record` 미포함 확인
   - `superseded_reject_signal.replay_source = task_log_audit`
   - `superseded_reject_signal.corrected_outcome.outcome = rejected`, `recorded_at` 원본 일치
   - `superseded_reject_signal.content_reason_record.reason_note = "초기 결론이 문서 문맥과 다릅니다."` (latest same-anchor note replay)
   - `superseded_reject_signal.content_reason_record.recorded_at` = reason note 기록 시점 일치

2. **`test_superseded_reject_signal_omits_ambiguous_note_association_with_sqlite_backend`**: SQLite 백엔드에서 reject → correction 후 `approval_reject` scope의 non-content reason note를 task_log에 직접 삽입:
   - `superseded_reject_signal.content_reason_record.reason_scope = content_reject` (원본 reject의 초기 reason 유지)
   - `superseded_reject_signal.content_reason_record.reason_note = None` (ambiguous note 제외)

3. **추가 구현 변경 없음**: 기존 `_build_superseded_reject_signal_index()`가 `_iter_task_log_records()`를 통해 SQLite task_log를 읽으며, `_normalize_superseded_reject_reason_record()`가 non-content scope를 정상적으로 필터링. SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_omits_ambiguous_note_association_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend  # OK
python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py  # clean
git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 `superseded_reject_signal` replay parity가 두 계약 모두 검증됨: latest same-anchor reject note replay + ambiguous note omission.
- content family 전체: reject/reason happy-path + blank-note guard + late-flip save-history + task_log row parity + superseded replay 모두 sqlite 검증 완료.
- `historical_save_identity_signal` sqlite parity, browser-level sqlite smoke는 이번 슬라이스 scope 밖.
- 구현 변경 없이 테스트만 추가했으므로 기존 동작 회귀 리스크 없음.
