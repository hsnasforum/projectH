# recurrence-aggregate-synthetic-message-proof-store-builder-fix

## 변경 파일

- `app/serializers.py`
- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 sqlite visible-surface/contract-retention bundle 6건 중 5건이 green이었으나, `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked`의 JSON-side 원본과 sqlite mirror가 모두 `IndexError`로 실패 중이었음. 원인: `_build_recurrence_aggregate_candidates`가 `current_candidate_index`를 `session_local_candidate`에서만 구축하므로, synthetic message fixture가 `candidate_recurrence_key`만 갖고 `session_local_candidate`가 없을 때 모든 member가 stale로 판정되어 aggregate가 0건 반환됨.

## 핵심 변경

1. **`app/serializers.py` `_build_recurrence_aggregate_candidates`**: `current_candidate_index` 구축 시 `session_local_candidate`가 없으면 `candidate_recurrence_key.source_candidate_id` / `source_candidate_updated_at`를 fallback으로 사용. `session_local_candidate`가 존재하면 기존 동작 그대로 우선.

2. **`tests/test_web_app.py`**: sqlite mirror에서 `@unittest.expectedFailure` 제거. 이제 JSON-side 원본과 sqlite mirror 모두 green.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidate_retires_on_superseding_correction_before_emit_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reload_continuity_with_sqlite_backend  # OK
python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py  # clean
git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py  # clean
```

## 남은 리스크

- 수정은 shared path에서 `session_local_candidate` 부재 시 `candidate_recurrence_key`를 fallback으로 사용하는 작은 변경. real session payload에서는 `session_local_candidate`가 항상 있으므로 기존 stale-candidate retirement guard에 영향 없음.
- 이 수정으로 같은 family의 마지막 non-green 계약이 해소됨.
- browser-level sqlite smoke는 이번 슬라이스 scope 밖.
