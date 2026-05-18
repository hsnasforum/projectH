# 2026-04-30 M117 Axis 1 주입 피드백 루프

## 변경 파일

- `core/contracts.py`
- `storage/session_store.py`
- `storage/sqlite/session.py`
- `app/main.py`
- `app/web.py`
- `tests/test_session_store.py`
- `tests/test_sqlite_store.py`
- `work/4/30/2026-04-30-m117-axis1-injection-feedback-loop.md`

## 사용 skill

- `security-gate`: `preference_injected` task log를 전역 감사 요약에 읽기 집계하는 변경이 기존 로컬 로그 경계 안에 머무는지 점검.
- `finalize-lite`: 구현 종료 전 검증 범위, docs 제외 사유, `/work` closeout 준비 상태를 점검.
- `work-log-closeout`: closeout 형식과 필수 섹션을 맞추기 위해 사용.

## 변경 이유

- M115에서 주입된 선호마다 `preference_injected` task log 이벤트가 기록되기 시작했지만, 전역 감사 요약은 `applied_count` / `corrected_count`만 집계하고 있었다.
- M117 Axis 1은 `injected_count`를 같은 `per_preference_stats` 요약에 추가해 주입 횟수와 실제 적용 횟수를 나란히 비교할 기반을 만든다.

## 핵심 변경

- `PerPreferenceStats`에 `injected_count` 필드를 추가했다.
- JSON `SessionStore.get_global_audit_summary()`가 연결된 JSONL task log에서 현재 세션들의 `preference_injected` 이벤트를 읽고, 기존 stats에 있는 `preference_id`의 `injected_count`를 누적한다.
- SQLite `SQLiteSessionStore.get_global_audit_summary()`가 같은 DB의 `task_log` 테이블에서 `preference_injected` 이벤트를 읽어 동일하게 집계한다.
- `preference_id`가 없거나 기존 `per_preference_stats`에 없는 이벤트는 무시해 방어적으로 처리한다.
- JSON app/CLI 경로에서 `SessionStore`가 실제 `settings.task_log_path`를 알 수 있도록 `app/main.py`와 `app/web.py` 초기화 wiring을 추가했다.
- `list_preferences_payload()` 응답 구조, UI/frontend, `_get_active_preferences()` 계열 로직은 수정하지 않았다.

## 검증

- `python3 -m py_compile core/contracts.py storage/session_store.py storage/sqlite/session.py app/main.py app/web.py`
  - 통과.
- `python3 -m unittest -v tests.test_session_store`
  - 통과. 20개 테스트 실행.
- `python3 -m unittest -v tests.test_sqlite_store`
  - 통과. 47개 테스트 실행.
- `python3 -m unittest -v tests.test_preference_store`
  - 통과. 34개 테스트 실행.
- `git diff --check -- core/contracts.py storage/session_store.py storage/sqlite/session.py app/main.py app/web.py tests/test_session_store.py tests/test_sqlite_store.py`
  - 통과.

## 남은 리스크

- 이번 라운드는 Axis 1 backend/audit summary 범위라 docs, UI/frontend, Playwright E2E는 수정하거나 실행하지 않았다.
- `injected_count`는 기존 `per_preference_stats`에 존재하는 preference id에 대해서만 누적한다. 주입 이벤트만 있고 적용/교정 stats가 아직 없는 preference id는 handoff 지시에 따라 무시된다.
