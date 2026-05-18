# 2026-04-28 M74 Axis 1 artifact tasklog validation

## 변경 파일

- `storage/artifact_store.py`
- `storage/sqlite_store.py`
- `storage/task_log.py`
- `tests/test_artifact_store.py`
- `tests/test_sqlite_store.py`
- `tests/test_task_log.py`
- `work/4/28/2026-04-28-m74-axis1-artifact-tasklog-validation.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 결과 정리에 사용.

## 변경 이유

- M72/M73에서 correction/preference read-path validation을 추가한 흐름을 ArtifactStore와 TaskLogger까지 확장해 malformed 기존 데이터가 읽기 경로에 섞이지 않도록 했다.
- handoff 경계에 따라 artifact `create`, task `log`, artifact `get(artifact_id)` 단일 조회 경로와 `SQLiteTaskLogger`는 변경하지 않았다.

## 핵심 변경

- `storage/artifact_store.py`에 `_ARTIFACT_REQUIRED_FIELDS`와 `_is_valid_artifact_record()`를 추가했다.
- `ArtifactStore.list_by_session()`과 `list_recent()`이 필수 필드가 비어 있는 JSON artifact 레코드를 조용히 제외하도록 변경했다.
- `SQLiteArtifactStore.list_by_session()`과 `list_recent()`에 같은 validator를 적용했고, 반환 레코드에 validator 필수 필드인 `session_id`를 포함했다.
- `TaskLogger.iter_session_records()`가 기존 JSON parse, dict, session 필터에 더해 `ts`와 `action` 누락 레코드를 제외하도록 변경했다.
- JSON/SQLite artifact validation 테스트와 신규 `tests/test_task_log.py` read-path validation 테스트를 추가했다.

## 검증

- `python3 -m py_compile storage/artifact_store.py storage/sqlite_store.py storage/task_log.py` — PASS
- `python3 -m unittest -v tests.test_artifact_store` — PASS, 16 tests
- `python3 -m unittest -v tests.test_sqlite_store` — PASS, 43 tests
- `python3 -m unittest -v tests.test_task_log` — PASS, 3 tests
- `git diff --check -- storage/artifact_store.py storage/sqlite_store.py storage/task_log.py tests/test_artifact_store.py tests/test_sqlite_store.py tests/test_task_log.py` — PASS

## 남은 리스크

- handoff가 요구한 시작 브랜치 `feat/m74-axis1-artifact-tasklog-validation` 생성은 `.git/refs`가 읽기 전용이라 실패했고, 작업 트리는 기존 `feat/m73-preference-validation` 브랜치 위에서 변경됐다.
- artifact `get(artifact_id)` 단일 조회 경로와 쓰기 경로는 이번 슬라이스 범위 밖이라 변경하지 않았다.
- `SQLiteTaskLogger`는 handoff 설명대로 SQL 스키마의 `NOT NULL` 보장을 전제로 변경하지 않았다.
- 브라우저/E2E, dist 재빌드, commit/push/PR 생성은 handoff 범위 밖이라 실행하지 않았다.
