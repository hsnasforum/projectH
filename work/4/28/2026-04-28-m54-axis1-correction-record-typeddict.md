# 2026-04-28 M54 Axis 1 CorrectionRecord TypedDict

## 변경 파일

- `core/contracts.py`
- `storage/correction_store.py`
- `tests/test_correction_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m54-axis1-correction-record-typeddict.md`

## 사용 skill

- `security-gate`: correction record 저장 경로의 타입 계약을 건드리므로 쓰기/저장 동작 변경 여부를 확인했습니다.
- `doc-sync`: 구현된 `CorrectionRecord` 계약을 handoff가 지정한 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

structured correction-memory schema의 첫 단계로 JSON `CorrectionStore.record_correction()`이 반환하는 correction record 필드 계약을 `TypedDict`로 공식화할 필요가 있었습니다. 이번 slice는 기존 저장 동작을 바꾸지 않고 타입 표면과 테스트만 추가했습니다.

## 핵심 변경

- `core/contracts.py`에 `CorrectionRecord(TypedDict, total=False)`를 추가하고 correction record의 22개 필드를 명시했습니다.
- `storage/correction_store.py`에서 `CorrectionRecord`를 import하고 `record_correction()`, `get()`, `_transition()` 반환 타입 annotation을 업데이트했습니다.
- `tests/test_correction_store.py`에 `test_record_correction_returns_typed_fields`를 추가해 핵심 필드와 `applied_preference_ids` 보존, runtime dict 호환성을 확인했습니다.
- `docs/MILESTONES.md`에 M54 Structured Correction Memory Axis 1 항목을 추가했습니다.
- 보안/저장 경계상 실제 JSON write payload, lifecycle transition, approval, session, SQLite store 동작은 변경하지 않았습니다.

## 검증

- `python3 -m py_compile core/contracts.py storage/correction_store.py tests/test_correction_store.py`
  - 통과
- `python3 -m unittest -v tests.test_correction_store`
  - 통과, 26개 테스트 OK
  - 신규 `test_record_correction_returns_typed_fields` 통과
- `git diff --check -- core/contracts.py storage/correction_store.py tests/test_correction_store.py docs/MILESTONES.md`
  - 통과

## 남은 리스크

- `storage/sqlite_store.py`의 `SQLiteCorrectionStore` 타입 표면은 handoff 경계상 Axis 2 대상이라 변경하지 않았습니다.
- frontend, dist, E2E, approval, session_store는 변경하지 않았고 별도 E2E 검증도 실행하지 않았습니다.
