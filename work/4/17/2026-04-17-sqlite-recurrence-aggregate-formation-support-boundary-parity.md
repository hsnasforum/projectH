# sqlite-recurrence-aggregate-formation-support-boundary-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 source-message serialization family 전체가 검증 완료됨 (replay adjunct 4건 + signal/candidate boundary 5건). 같은 reviewed-memory stack에서 남은 가장 직접적인 current-risk는 `recurrence_aggregate_candidates` formation/support boundary semantics: JSON-only 테스트 5건에 대한 SQLite peer가 없었음. 이 계약들은 사용자가 이미 접근 가능한 `검토 메모 적용 후보` 경로에 영향을 주므로 current-risk reduction이 명확함.

## 핵심 변경

1. **`test_recurrence_aggregate_candidates_require_two_distinct_source_messages_and_ignore_same_anchor_replays_with_sqlite_backend`**: SQLite 백엔드에서 두 개의 distinct source-message에 같은 corrected_text를 적용한 뒤 aggregate가 생성되고, 세 번째 다른 correction은 같은 fingerprint가 아닌 별도 aggregate를 형성하지 않음을 확인. `supporting_source_message_refs`, `supporting_candidate_refs` 정합성 확인. `supporting_review_refs` 미포함 확인.

2. **`test_recurrence_aggregate_candidates_keep_candidate_review_as_support_only_with_sqlite_backend`**: SQLite 백엔드에서 첫 번째 candidate에 `accept` review 후 두 번째 correction 시 aggregate에 `supporting_review_refs`가 accept review만 포함되고 support-only로 남는지 확인.

3. **`test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs_with_sqlite_backend`**: SQLite 백엔드에서 첫 번째 candidate `reject`, 두 번째 candidate `defer` review 후 aggregate에 `supporting_review_refs`가 포함되지 않음을 확인.

4. **`test_recurrence_aggregate_candidates_do_not_materialize_from_save_support_or_historical_adjunct_only_with_sqlite_backend`**: SQLite 백엔드에서 correction + save + 다시 correction (historical adjunct 발생) + accepted_as_is save-only 경로가 aggregate를 생성하지 않음을 확인.

5. **`test_recurrence_aggregate_precondition_blocked_stays_fixed_when_capability_unblocked_with_sqlite_backend`**: SQLite 백엔드에서 `reviewed_memory_precondition_status.overall_status = blocked_all_required`, `reviewed_memory_unblock_contract.unblock_status = blocked_all_required`가 `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`와 분리되어 유지됨을 확인.

6. **추가 구현 변경 없음**: 기존 aggregate formation/serialization 경로가 storage backend와 무관하게 정상 동작. SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_require_two_distinct_source_messages_and_ignore_same_anchor_replays_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_keep_candidate_review_as_support_only_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_do_not_materialize_from_save_support_or_historical_adjunct_only_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_precondition_blocked_stays_fixed_when_capability_unblocked_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_emit_apply_confirm_active_effect_with_sqlite_backend  # OK
python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py  # clean
git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 `recurrence_aggregate_candidates` formation/support boundary가 5건 모두 검증됨.
- reviewed-memory stack sqlite parity 누적: replay adjunct 4건 + signal/candidate boundary 5건 + aggregate formation/support boundary 5건 + aggregate lifecycle 3건 = 17건.
- stored transition-record sanitization, contract-ref retention, deeper lifecycle retention 등은 이번 슬라이스 scope 밖.
- browser-level sqlite smoke는 이번 슬라이스 scope 밖.
- 구현 변경 없이 테스트만 추가했으므로 기존 동작 회귀 리스크 없음.
