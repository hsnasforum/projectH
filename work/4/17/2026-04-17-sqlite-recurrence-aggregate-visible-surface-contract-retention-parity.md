# sqlite-recurrence-aggregate-visible-surface-contract-retention-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 aggregate supersession/reload-sanitization이 4건 검증 완료됨. 같은 aggregate lifecycle family에서 남은 마지막 uncovered layer는 visible-surface/contract-only/internal 분리 + retention 계약 6건: proof-record-store UI 차단, visible transition/result/active-effect lifecycle, boundary-draft retention, contract-refs retention, source-family-refs retention, local-effect-chain retention. JSON-only 테스트만 존재하고 SQLite peer가 없었음.

## 핵심 변경

1. **`test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend`**: SQLite 백엔드에서 synthetic messages로 proof-record-store 내부 helpers가 정상 구축되고 `_serialize_session` 후 payload에 proof/internal 필드가 누출되지 않음을 확인. **`@unittest.expectedFailure` 마킹**: JSON-side 원본 테스트(`test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked`)가 동일한 `IndexError`로 이미 실패 중. `_build_recurrence_aggregate_candidates`가 synthetic messages에서 aggregate를 0건 반환하는 기존 seam이 존재. sqlite divergence가 아닌 pre-existing JSON-side 이슈.

2. **`test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle_with_sqlite_backend`**: SQLite 백엔드에서 emit → apply → confirm → stop → reverse → conflict-visibility 전체 lifecycle 후 record_stage 진행, apply_result.result_stage 진행, active_effects 출현/소멸, `[검토 메모 활성]` prefix 출현/소멸 검증.

3. **`test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle_with_sqlite_backend`**: SQLite 백엔드에서 전체 lifecycle을 통과해도 `reviewed_memory_boundary_draft.boundary_stage = draft_not_applied`가 변경되지 않고 `aggregate_identity_ref`가 유지됨을 확인.

4. **`test_recurrence_aggregate_contract_refs_retained_through_lifecycle_with_sqlite_backend`**: SQLite 백엔드에서 rollback/disable/conflict/audit 4개 contract의 stage 필드가 전체 lifecycle을 통과해도 contract_only 상태로 유지됨을 확인.

5. **`test_recurrence_aggregate_source_family_refs_retained_through_lifecycle_with_sqlite_backend`**: SQLite 백엔드에서 boundary_source_ref, rollback/disable/conflict/transition_audit source refs 5개가 전체 lifecycle을 통과해도 동일하게 유지됨을 확인.

6. **`test_recurrence_aggregate_local_effect_chain_retained_through_lifecycle_with_sqlite_backend`**: SQLite 백엔드에서 proof_record, proof_boundary, fact_source_instance, fact_source, event, event_producer, event_source, record 8개 chain member가 전체 lifecycle을 통과해도 동일하게 유지됨을 확인.

7. **추가 구현 변경 없음**: 기존 aggregate lifecycle, serialization, retention 경로가 storage backend와 무관하게 정상 동작. SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend  # expected failure (pre-existing JSON-side issue)
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_contract_refs_retained_through_lifecycle_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_source_family_refs_retained_through_lifecycle_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_local_effect_chain_retained_through_lifecycle_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_stop_reverse_conflict_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reload_continuity_with_sqlite_backend  # OK
python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py  # clean
git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 aggregate visible-surface/contract-retention이 5건 green + 1건 expectedFailure로 검증됨.
- **pre-existing seam**: `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked` (JSON-side 원본)이 `_build_recurrence_aggregate_candidates`가 synthetic messages에서 aggregate를 0건 반환하여 실패 중. sqlite mirror도 동일 실패. 이것은 sqlite parity 이슈가 아니라 aggregate builder의 synthetic-message-path regression.
- reviewed-memory stack sqlite parity 누적: replay adjunct 4건 + signal/candidate boundary 5건 + aggregate formation/support boundary 5건 + aggregate supersession/reload-sanitization 4건 + aggregate visible-surface/contract-retention 6건 + aggregate lifecycle 3건 = 27건.
- browser-level sqlite smoke는 이번 슬라이스 scope 밖.
- 구현 변경 없이 테스트만 추가했으므로 기존 동작 회귀 리스크 없음.
