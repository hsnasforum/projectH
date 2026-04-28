# 2026-04-28 M54 Axis 2 SQLiteCorrectionStore CorrectionRecord 타입 표면

## 변경 파일

- `storage/sqlite_store.py`
- `tests/test_correction_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m54-axis2-sqlite-correction-record-typeddict.md`

## 사용 skill

- `security-gate`: SQLite correction record 저장 경로의 타입 표면을 바꾸므로 저장 동작 변경 여부와 로컬 저장 경계를 확인했습니다.
- `doc-sync`: 구현된 SQLiteCorrectionStore 타입 통일 범위를 handoff가 지정한 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M54 Axis 1에서 JSON `CorrectionStore` 반환 타입이 `CorrectionRecord`로 정리되었지만, SQLite backend의 `SQLiteCorrectionStore`는 여전히 `dict[str, Any]` 반환 annotation을 사용하고 있었습니다. 이번 slice는 SQLite correction store의 public 반환 타입 표면을 `CorrectionRecord` 계약과 맞추는 데 한정했습니다.

## 핵심 변경

- `storage/sqlite_store.py`에서 `CorrectionRecord`를 import했습니다.
- `SQLiteCorrectionStore.record_correction()`과 `get()` 반환 타입을 `CorrectionRecord | None`으로 업데이트했습니다.
- `find_by_fingerprint()`, `find_by_artifact()`, `find_by_session()`, `list_recent()`, `list_incomplete_corrections()` 반환 타입을 `list[CorrectionRecord]`로 업데이트했습니다.
- `tests/test_correction_store.py`에 `test_sqlite_record_correction_returns_typed_fields`를 추가해 SQLite record의 핵심 필드, `applied_preference_ids`, runtime dict 호환성을 확인했습니다.
- `docs/MILESTONES.md`에 M54 Axis 2 항목을 추가했습니다.

## 검증

- `python3 -m py_compile storage/sqlite_store.py tests/test_correction_store.py`
  - 통과
- `python3 -m unittest -v tests.test_correction_store`
  - 통과, 27개 테스트 OK
  - 신규 `test_sqlite_record_correction_returns_typed_fields` 통과
- `git diff --check -- storage/sqlite_store.py tests/test_correction_store.py docs/MILESTONES.md`
  - 통과

## 남은 리스크

- 이번 변경은 타입 annotation과 테스트만 다뤘고 SQLite 저장 payload, migration, lifecycle transition 동작은 변경하지 않았습니다.
- `core/contracts.py`, `storage/correction_store.py`, frontend, dist, E2E, approval, session_store는 handoff 경계에 따라 변경하지 않았습니다.
