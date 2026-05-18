# 2026-04-28 M75 Axis 1 sqlite store decomp

## 변경 파일

- `storage/sqlite_store.py`
- `storage/sqlite/__init__.py`
- `storage/sqlite/database.py`
- `storage/sqlite/session.py`
- `storage/sqlite/task_log.py`
- `storage/sqlite/artifact.py`
- `storage/sqlite/preference.py`
- `storage/sqlite/correction.py`
- `storage/sqlite/migrate.py`
- `work/4/28/2026-04-28-m75-axis1-sqlite-store-decomp.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 결과 정리에 사용.

## 변경 이유

- `storage/sqlite_store.py`에 SQLite database, session, task log, artifact, preference, correction, migration 구현이 모두 섞여 있어 handoff에 따라 `storage/sqlite/` 하위 모듈로 구조만 분리했다.
- 기존 import 호환을 유지해야 하므로 `storage/sqlite_store.py`는 공개 이름을 다시 내보내는 thin wrapper로 남겼다.

## 핵심 변경

- `SQLiteDatabase`, `_now_iso()`, `_new_id()`와 SQLite schema를 `storage/sqlite/database.py`로 분리했다.
- `SQLiteSessionStore`, `SQLiteTaskLogger`, `SQLiteArtifactStore`, `SQLitePreferenceStore`, `SQLiteCorrectionStore`, `migrate_json_to_sqlite()`를 각각 전용 모듈로 이동했다.
- `storage/sqlite/__init__.py`와 `storage/sqlite_store.py`가 기존 공개 이름을 re-export하도록 구성했다.
- 기존 테스트 파일은 수정하지 않았다.
- 동작 변경 없이 M72-M74에서 추가된 `_is_valid_*` read-path validator import도 각 store 모듈에 유지했다.

## 검증

- `python3 -m py_compile storage/sqlite/__init__.py storage/sqlite/database.py storage/sqlite/session.py storage/sqlite/task_log.py storage/sqlite/artifact.py storage/sqlite/preference.py storage/sqlite/correction.py storage/sqlite/migrate.py storage/sqlite_store.py` — PASS
- `python3 -m unittest tests.test_sqlite_store` — PASS, 43 tests
- `python3 -m unittest tests.test_correction_store` — PASS, 37 tests
- `python3 -m unittest tests.test_preference_store` — PASS, 33 tests
- `python3 -m unittest tests.test_artifact_store` — PASS, 16 tests
- `git diff --check -- storage/sqlite_store.py storage/sqlite/` — PASS

## 남은 리스크

- handoff가 요구한 시작 브랜치 `feat/m75-axis1-sqlite-store-decomp` 생성은 `.git/refs`가 읽기 전용이라 실패했고, 작업 트리는 기존 `feat/m74-artifact-tasklog-validation` 브랜치 위에서 변경됐다.
- 순수 구조 분리 범위라 문서, 브라우저/E2E, dist 재빌드는 실행하지 않았다.
- commit/push/PR 생성은 handoff 범위 밖이라 실행하지 않았다.
