# sqlite-reviewed-candidate-persistence-path-parity

## 변경 파일

- `storage/sqlite_store.py`
- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 추가한 accepted-reviewed-candidate → local preference candidate 경로가 JSON 기본 백엔드에서는 정상 동작하나, SQLite 백엔드에서는 `SQLiteSessionStore`에 `build_session_local_memory_signal`, `record_candidate_confirmation_for_message`, `record_candidate_review_for_message`, `record_correction_for_message`, `record_corrected_outcome_for_artifact` 등 핵심 data-processing 메서드가 누락되어 grounded-brief serialization 경로 자체가 동작하지 않았음.

## 핵심 변경

1. **`storage/sqlite_store.py` — 메서드 재사용**: `SessionStore`의 data-processing 메서드를 attribute assignment로 `SQLiteSessionStore`에 바인딩. 두 store가 동일한 session dict 형식을 사용하므로 로직을 공유할 수 있음. 바인딩 대상:
   - normalization helpers (`_normalize_message`, `_normalize_multiline_text`, `_normalize_approval_record`, `_normalize_corrected_outcome`, `_normalize_content_reason_record`, `_normalize_candidate_confirmation_record`, `_normalize_candidate_review_record`, `_normalize_original_response_snapshot`, `_normalize_source_message_anchor`, `_is_matching_anchor`, etc.)
   - session signal builder (`build_session_local_memory_signal`, `_latest_approval_reason_record_for_anchor`, `_latest_save_signal_for_anchor`)
   - candidate/review record methods (`record_candidate_confirmation_for_message`, `record_candidate_review_for_message`)
   - correction/outcome methods (`record_correction_for_message`, `record_corrected_outcome_for_artifact`, `record_rejected_content_verdict_for_message`, `record_content_reason_note_for_message`)
   - approval normalization (`add_pending_approval`)
   - artifact lookup (`find_artifact_source_message`)

2. **`storage/sqlite_store.py` — `_now()`, `_lock` 추가**: 바인딩된 메서드가 요구하는 `self._now()`과 `self._lock` (threading.RLock) 제공.

3. **`storage/sqlite_store.py` — `append_message`, `update_last_message`, `update_message` 정규화**: 기존 simplified 구현을 `_normalize_message()`를 호출하도록 수정하여 `source_message_id`, `original_response_snapshot`, `corrected_outcome` 등이 정상 직렬화됨.

4. **`tests/test_web_app.py`**: `test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend` 추가 — SQLite 백엔드에서 grounded-brief → correction → corrected save → candidate confirm → review accept → `list_preferences_payload()` 전체 경로 검증.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend  # OK
python3 -m py_compile storage/sqlite_store.py app/serializers.py app/web.py  # clean
git diff --check -- (all changed files)  # clean
```

## 남은 리스크

- attribute assignment 방식은 `SessionStore`에 새 helper가 추가될 때 `SQLiteSessionStore` 바인딩도 함께 추가해야 하는 수동 동기 부담이 있음. 장기적으로는 mixin 추출이 더 안전하나 이번 슬라이스에서는 파일 구조 변경 최소화를 우선.
- SQLite 백엔드 전체 E2E 경로(예: aggregate transition, stop-apply, reversal, conflict-visibility)는 이번 슬라이스에서 검증하지 않음 — 해당 경로는 JSON 백엔드 기준 이미 검증되었고, 기반 메서드 공유를 통해 동일하게 동작할 것으로 예상.
- 기존 SQLite 전용 simplified `record_correction_for_message`, `record_corrected_outcome_for_artifact`, `find_artifact_source_message`, `add_pending_approval` 구현이 SessionStore 버전으로 교체됨 — JSON store와 동일 semantics를 보장하지만, 기존 SQLite 전용 동작에 의존하던 코드가 있다면 영향 가능 (현재까지 발견되지 않음).
