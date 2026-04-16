# sqlite-recurrence-aggregate-supersession-reload-sanitization-parity

## 변경 파일

- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

이전 라운드에서 SQLite 백엔드의 aggregate formation/support boundary가 5건 검증 완료됨. 같은 aggregate integrity family에서 남은 가장 직접적인 current-risk는 aggregate 현재 버전 관리와 reload 무결성: pre-emit aggregate 퇴출, record-backed lifecycle의 supporting-correction supersession 생존, 그리고 저장된 transition/conflict record에서 reject/defer review ref sanitization이 JSON-only 테스트만 존재하고 SQLite peer가 없었음.

## 핵심 변경

1. **`test_recurrence_aggregate_candidate_retires_on_superseding_correction_before_emit_with_sqlite_backend`**: SQLite 백엔드에서 두 개 correction으로 aggregate 형성 후, 첫 번째 correction을 다른 텍스트로 supersede하면 emit 전 aggregate가 퇴출됨을 확인.

2. **`test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession_with_sqlite_backend`**: SQLite 백엔드에서 emit → apply → confirm으로 record-backed lifecycle 진입 후, supporting correction을 supersede해도 aggregate와 active effect가 생존하고, 이후 stop까지 정상 진행됨을 확인.

3. **`test_stored_transition_record_reject_defer_review_refs_sanitized_on_reload_with_sqlite_backend`**: SQLite 백엔드에서 emit 후 저장된 transition record에 reject ref를 수동 삽입한 뒤 reload하면, 저장된 record에서 reject/defer ref가 제거되고 accept ref만 남으며 live aggregate `supporting_review_refs`도 accept-only로 유지됨을 확인.

4. **`test_stored_conflict_visibility_record_reject_defer_review_refs_sanitized_on_reload_with_sqlite_backend`**: SQLite 백엔드에서 full lifecycle (emit → apply → confirm → stop → reverse → conflict-visibility) 후 저장된 conflict-visibility record에 reject/defer ref를 삽입한 뒤 reload하면 sanitization이 동일하게 적용됨을 확인.

5. **추가 구현 변경 없음**: 기존 aggregate supersession 판단, lifecycle 생존 로직, transition/conflict record sanitization 경로가 storage backend와 무관하게 정상 동작. `SQLiteSessionStore._save()` 및 reload 경로에서 SQLite seam blocker 없음.

## 검증

```
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidate_retires_on_superseding_correction_before_emit_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_stored_transition_record_reject_defer_review_refs_sanitized_on_reload_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_stored_conflict_visibility_record_reject_defer_review_refs_sanitized_on_reload_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_stop_reverse_conflict_with_sqlite_backend  # OK
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reload_continuity_with_sqlite_backend  # OK
python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py  # clean
git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py  # clean
```

## 남은 리스크

- SQLite 백엔드에서 aggregate supersession/reload-sanitization이 4건 모두 검증됨.
- reviewed-memory stack sqlite parity 누적: replay adjunct 4건 + signal/candidate boundary 5건 + aggregate formation/support boundary 5건 + aggregate supersession/reload-sanitization 4건 + aggregate lifecycle 3건 = 21건.
- proof-record-store internal/UI-blocked checks, boundary-draft retention, contract-ref retention, source-family retention, local-effect-chain retention, browser-level sqlite smoke는 이번 슬라이스 scope 밖.
- 구현 변경 없이 테스트만 추가했으므로 기존 동작 회귀 리스크 없음.
