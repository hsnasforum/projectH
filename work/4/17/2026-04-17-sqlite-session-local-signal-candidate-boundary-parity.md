# sqlite-session-local-signal-candidate-boundary-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 serializer/task-log replay adjunct family 전체가 검증 완료됨 (`superseded_reject_signal` 2건 + `historical_save_identity_signal` 2건). 같은 serialization family에서 남은 가장 직접적인 current-risk는 grounded-brief source-message의 `session_local_memory_signal` / `session_local_candidate` / `candidate_recurrence_key` boundary semantics: JSON-only 테스트 5건에 대한 SQLite peer가 없었음. 하나의 coherent boundary family이므로 한 번에 닫음.

## 핵심 변경

1. **`test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes_with_sqlite_backend`**: SQLite 백엔드에서 save request → approval reject → correction → corrected save → approve 전체 lifecycle 후:
   - 초기: content_signal만 존재, approval_signal/save_signal 미생성
   - approval reject 후: approval_signal 출현, save_signal 미생성
   - corrected save approve 후: content/approval/save 세 축 모두 존재, 각각 독립 유지

2. **`test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals_with_sqlite_backend`**: SQLite 백엔드에서 초기/reject 후에는 candidate/recurrence_key 미생성, correction 후에만 출현하고 전체 candidate field 정합성 검증

3. **`test_session_local_candidate_uses_current_save_signal_only_for_support_with_sqlite_backend`**: SQLite 백엔드에서 correction → save → approve 후 save_signal이 supporting_evidence로만 참조되고 다시 correction 하면 save_signal 지원 해제, `historical_save_identity_signal`이 candidate basis가 되지 않음 확인

4. **`test_session_local_candidate_omits_same_text_pair_even_if_corrected_outcome_exists_with_sqlite_backend`**: SQLite 백엔드에서 corrected_text == original text일 때 candidate/recurrence_key 미생성 확인

5. **`test_session_local_candidate_omits_accepted_as_is_only_save_path_with_sqlite_backend`**: SQLite 백엔드에서 accepted_as_is만 있고 correction이 없을 때 candidate/recurrence_key 미생성 확인

6. **추가 구현 변경 없음**: 기존 serializer의 signal/candidate/recurrence_key 생성 경로가 storage backend와 무관하게 정상 동작. SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_local_candidate_uses_current_save_signal_only_for_support_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_local_candidate_omits_same_text_pair_even_if_corrected_outcome_exists_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_local_candidate_omits_accepted_as_is_only_save_path_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend  # OK
python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py  # clean
git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 source-message signal/candidate/recurrence_key boundary semantics가 5건 모두 검증됨.
- serializer/task-log replay + signal/candidate boundary family 전체 sqlite parity 완료: replay adjunct 4건 + boundary 5건 = 9건.
- browser-level sqlite smoke, review queue/reviewed-memory aggregate 외 axis parity는 이번 슬라이스 scope 밖.
- 구현 변경 없이 테스트만 추가했으므로 기존 동작 회귀 리스크 없음.
