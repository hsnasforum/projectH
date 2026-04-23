# 2026-04-23 Milestone 13 Axis 5 preference reliability API

## 변경 파일

- `app/handlers/preferences.py`
- `tests/test_web_app.py`

## 사용 skill

- `security-gate`: preference API payload가 local session audit summary를 읽는 변경이라 read-only/local-first/승인 경계를 확인했습니다.
- `finalize-lite`: 구현 후 실제 실행한 검증과 문서 동기화 필요 여부를 좁게 확인했습니다.
- `work-log-closeout`: 구현 라운드 종료 기록을 `/work`에 남겼습니다.

## 변경 이유

- `list_preferences_payload()`가 각 preference record에 `reliability_stats`를 포함하도록 하여, backend API에서 preference별 적용 횟수와 교정 횟수를 볼 수 있게 하기 위함입니다.

## 핵심 변경

- `session_store.get_global_audit_summary()`의 `per_preference_stats`를 읽어 preference payload에 병합했습니다.
- 기존 preference record가 `delta_fingerprint`를 저장하므로 `fingerprint`와 `delta_fingerprint`를 모두 lookup key로 지원했습니다.
- 각 preference record에는 항상 `reliability_stats.applied_count`와 `reliability_stats.corrected_count`가 int로 포함됩니다.
- `SQLiteSessionStore`는 현재 `get_global_audit_summary()` parity가 없어 이번 범위에서는 통계를 0 기본값으로 유지했습니다. 기존 SQLite preference payload flow는 깨지지 않도록 확인했습니다.
- 프론트엔드, `preference_store.py`, `agent_loop.py`, 계약 파일, `.pipeline` control slot은 수정하지 않았습니다.

## 검증

- `python3 -m py_compile app/handlers/preferences.py` → 통과
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_list_preferences_payload_includes_reliability_stats tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend -v` → 3 tests OK
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets tests.test_evaluate_traces -v 2>&1 | tail -5` → 60 tests OK
- `git diff --check -- app/handlers/preferences.py` → 통과
- `git diff --check -- app/handlers/preferences.py tests/test_web_app.py` → 통과

## 남은 리스크

- SQLite backend에서는 session audit summary API parity가 아직 없어 `reliability_stats` 키는 붙지만 실제 per-preference count는 0 기본값입니다. `storage/sqlite_store.py`는 이번 handoff의 변경 금지 파일이라 건드리지 않았습니다.
- UI 표시는 이번 backend-only handoff 범위 밖입니다.
