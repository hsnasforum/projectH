# 2026-04-28 M72 Axis 1 correction validation

## 변경 파일

- `storage/correction_store.py`
- `storage/sqlite_store.py`
- `tests/test_correction_store.py`
- `tests/test_sqlite_store.py`
- `work/4/28/2026-04-28-m72-axis1-correction-validation.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록 형식과 필수 검증 사실 정리에 사용.

## 변경 이유

- `TASK_BACKLOG`에 남은 "physical validation remains" 항목에 맞춰 correction 레코드 읽기 경로에서 malformed 기존 데이터를 조용히 제외하는 최소 검증 계층을 추가했다.
- handoff 경계에 따라 `record_correction()` 쓰기 경로와 `get(correction_id)` 단일 조회 경로는 변경하지 않았다.

## 핵심 변경

- `storage/correction_store.py`에 `_CORRECTION_REQUIRED_FIELDS`와 `_is_valid_correction_record()`를 추가했다.
- `CorrectionStore._scan_all()`이 `correction_id`, `delta_fingerprint`, `status`, `created_at` 필수 필드가 비어 있는 JSON 레코드를 제외하도록 변경했다.
- `SQLiteCorrectionStore.list_recent()`와 `list_filtered()`가 `_row_to_dict()` 결과를 같은 validator로 필터링하도록 변경했다.
- JSON store 테스트에 필수 필드 누락 레코드 제외와 정상 `record_correction()` 레코드 유지 케이스를 추가했다.
- SQLite store 테스트에 직접 삽입한 malformed row가 `list_recent()`에서 제외되는 케이스를 추가했다.

## 검증

- `python3 -m py_compile storage/correction_store.py storage/sqlite_store.py` — PASS
- `python3 -m unittest -v tests.test_correction_store` — PASS, 37 tests
- `python3 -m unittest -v tests.test_sqlite_store` — PASS, 40 tests
- `git diff --check -- storage/correction_store.py storage/sqlite_store.py tests/test_correction_store.py tests/test_sqlite_store.py` — PASS

## 남은 리스크

- handoff가 요구한 시작 브랜치 `feat/m72-axis1-correction-validation` 생성은 `.git/refs`가 읽기 전용이라 실패했고, 작업 트리는 기존 `feat/m71-doc-sync-m61-m70` 브랜치 위에서 변경됐다.
- `get(correction_id)` 단일 조회 경로와 `record_correction()` 쓰기 경로는 이번 슬라이스 범위 밖이라 변경하지 않았다.
- 브라우저/E2E, dist 재빌드, commit/push/PR 생성은 handoff 범위 밖이라 실행하지 않았다.
