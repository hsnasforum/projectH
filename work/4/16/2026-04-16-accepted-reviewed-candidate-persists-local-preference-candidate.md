# accepted-reviewed-candidate-persists-local-preference-candidate

## 변경 파일

- `app/handlers/aggregate.py`
- `storage/preference_store.py`
- `storage/sqlite_store.py`
- `tests/test_web_app.py`
- `tests/test_preference_store.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

검토 수락된 reviewed candidate가 세션 밖의 durable local preference store에 기록되지 않아 cross-session 재활용의 첫 걸음이 없었음. 기존 `PreferenceStore` / `SQLitePreferenceStore`를 재사용하여 새 persistence family를 만들지 않고 하나의 additive ingestion path를 추가.

## 핵심 변경

1. **`storage/preference_store.py`**: `record_reviewed_candidate_preference()` 메서드 추가. `delta_fingerprint` 기준으로 idempotent — 동일 fingerprint는 refresh, 다른 `candidate_id`는 `reviewed_candidate_source_refs`에 append. status는 `candidate`로 고정.
2. **`storage/sqlite_store.py`**: `SQLitePreferenceStore`에 동일 `record_reviewed_candidate_preference()` 추가. `delta_fingerprint` UNIQUE 제약을 활용하여 기존 레코드 감지.
3. **`app/handlers/aggregate.py`**: `submit_candidate_review()`에서 `review_action == "accept"` 이후 `candidate_recurrence_key`의 `normalized_delta_fingerprint`를 통해 `self.preference_store.record_reviewed_candidate_preference()` 호출. `preference_candidate_recorded` audit event 추가.
4. **테스트**: `test_submit_candidate_review_accept_persists_local_preference_candidate` (test_web_app) — 전체 grounded-brief → correction → save → confirm → review accept 흐름 후 `list_preferences_payload()`에 preference candidate 1건 확인. `test_record_reviewed_candidate_preference_creates_and_idempotent` (test_preference_store) — 생성, 동일 candidate_id 중복 방지, 다른 candidate_id append 검증.
5. **문서**: PRODUCT_SPEC, ARCHITECTURE, ACCEPTANCE_CRITERIA, TASK_BACKLOG에 새 ingestion path 반영. ACCEPTANCE_CRITERIA task log action 목록에 `preference_candidate_recorded` 추가.

## 검증

```
python3 -m unittest -v tests.test_preference_store  # 16 passed
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate  # 1 passed
git diff --check -- (all changed files)  # clean
```

## 남은 리스크

- 새로 기록된 preference candidate는 `status = candidate`이며 auto-activate 되지 않음. cross-session application, prompt injection, UI 패널은 이후 슬라이스.
- SQLite seam에 대한 focused regression 테스트는 이번 슬라이스에 포함하지 않음 (SQLite 코드 구조 변경은 additive insert/update만이므로 기존 schema와 호환).
- `reject` / `defer` review action에서는 preference candidate를 기록하지 않음 — 의도된 동작.
