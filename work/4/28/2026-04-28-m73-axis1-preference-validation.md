# 2026-04-28 M73 Axis 1 preference validation

## 변경 파일

- `storage/preference_store.py`
- `storage/sqlite_store.py`
- `tests/test_preference_store.py`
- `tests/test_sqlite_store.py`
- `work/4/28/2026-04-28-m73-axis1-preference-validation.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 결과 정리에 사용.

## 변경 이유

- M72 correction read-path validation 패턴을 PreferenceStore로 확장해 malformed preference 레코드가 prompt/context 읽기 경로에 섞이지 않도록 했다.
- handoff 경계에 따라 `record_reviewed_candidate_preference`, `promote_from_corrections`, `get(preference_id)` 단일 조회 경로는 변경하지 않았다.

## 핵심 변경

- `storage/preference_store.py`에 `_PREFERENCE_REQUIRED_FIELDS`와 `_is_valid_preference_record()`를 추가했다.
- `PreferenceStore._scan_all()`의 기존 `preference_id` 최소 필터를 필수 필드 기반 validator로 교체했다.
- `SQLitePreferenceStore.get_active_preferences()`와 `list_all()`이 `_row/data` 변환 후 같은 validator로 malformed row를 제외하도록 변경했다.
- JSON preference 테스트에 필수 필드 누락 레코드 제외와 정상 `record_reviewed_candidate_preference()` 레코드 유지 케이스를 추가했다.
- SQLite preference 테스트에 직접 삽입한 malformed active row가 `get_active_preferences()`에서 제외되는 케이스를 추가했다.

## 검증

- `python3 -m py_compile storage/preference_store.py storage/sqlite_store.py` — PASS
- `python3 -m unittest -v tests.test_preference_store` — PASS, 33 tests
- `python3 -m unittest -v tests.test_sqlite_store` — PASS, 41 tests
- `git diff --check -- storage/preference_store.py storage/sqlite_store.py tests/test_preference_store.py tests/test_sqlite_store.py` — PASS

## 남은 리스크

- handoff가 요구한 시작 브랜치 `feat/m73-axis1-preference-validation` 생성은 `.git/refs`가 읽기 전용이라 실패했고, 작업 트리는 기존 `feat/m72-correction-validation` 브랜치 위에서 변경됐다.
- `get(preference_id)` 단일 조회 경로와 preference 쓰기 경로는 이번 슬라이스 범위 밖이라 변경하지 않았다.
- 브라우저/E2E, dist 재빌드, commit/push/PR 생성은 handoff 범위 밖이라 실행하지 않았다.
