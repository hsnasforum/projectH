# 2026-04-28 M57 Axis 2 SQLitePreferenceStore PreferenceRecord annotation

## 변경 파일

- `storage/sqlite_store.py`
- `tests/test_preference_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m57-axis2-sqlite-preference-record-annotations.md`

## 사용 skill

- `security-gate`: SQLite preference store의 로컬 저장 record 표면을 만졌으므로 approval, overwrite/delete, 외부 네트워크, logging 경계가 바뀌지 않았는지 확인했습니다.
- `doc-sync`: handoff가 지정한 `docs/MILESTONES.md` M57 Axis 2 항목만 현재 구현 상태에 맞춰 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M57 Axis 1에서 `PreferenceRecord` TypedDict와 JSON `PreferenceStore` 반환 타입을 정리했지만, SQLite backend의 `SQLitePreferenceStore`는 아직 `dict[str, Any]` 반환 annotation을 유지하고 있었습니다. 이번 slice는 SQLite preference store 반환 타입을 같은 `PreferenceRecord` 표면으로 맞췄습니다.

## 핵심 변경

- `storage/sqlite_store.py`의 core contract import에 `PreferenceRecord`를 추가했습니다.
- `SQLitePreferenceStore`의 `get()`, `activate_preference()`, `pause_preference()`, `reject_preference()`, `update_description()`, `record_reviewed_candidate_preference()` 반환 타입을 `PreferenceRecord | None` 또는 `PreferenceRecord`로 바꿨습니다.
- `SQLitePreferenceStore`의 `get_active_preferences()`와 `list_all()` 반환 타입을 `list[PreferenceRecord]`로 바꿨습니다.
- `tests/test_preference_store.py`에 SQLite `get()` 결과가 `PreferenceRecord` 핵심 필드(`preference_id`, `delta_fingerprint`, `status`)를 포함하는지 확인하는 테스트를 추가했습니다.
- `docs/MILESTONES.md`에 M57 Axis 2 항목을 추가했습니다.

## 검증

- `python3 -m py_compile storage/sqlite_store.py tests/test_preference_store.py`
  - 통과
- `python3 -m unittest -v tests.test_preference_store`
  - 통과, 31개 테스트 OK
- `git diff --check -- storage/sqlite_store.py tests/test_preference_store.py docs/MILESTONES.md`
  - 통과

## 남은 리스크

- 이번 변경은 SQLite preference store 반환 annotation과 해당 단위 테스트에 한정했습니다. SQLite write/read 로직, approval, frontend, dist, E2E는 변경하지 않았습니다.
- `core/contracts.py`와 `storage/preference_store.py`는 Axis 1 완료 파일이라 이번 handoff 경계상 변경하지 않았습니다.
- browser/E2E, 전체 unittest, 별도 정적 타입 검사 도구는 실행하지 않았습니다.
