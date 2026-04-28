# 2026-04-28 M57 Axis 1 PreferenceRecord TypedDict

## 변경 파일

- `core/contracts.py`
- `storage/preference_store.py`
- `tests/test_preference_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m57-axis1-preference-record-typeddict.md`

## 사용 skill

- `security-gate`: 로컬 preference store의 저장 record 표면을 만졌으므로 approval, overwrite/delete, 외부 네트워크, logging 경계가 바뀌지 않았는지 확인했습니다.
- `doc-sync`: handoff가 지정한 `docs/MILESTONES.md` M57 Axis 1 항목만 현재 구현 상태에 맞춰 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M54-M56에서 correction record와 per-preference stats 타입 표면을 정리한 뒤, JSON 기반 `PreferenceStore`의 preference record 반환 타입도 공식 계약으로 묶을 필요가 있었습니다. 이번 slice는 `PreferenceRecord`를 추가하고 `PreferenceStore`의 단일 record/list 반환 annotation을 통일했습니다.

## 핵심 변경

- `core/contracts.py`에 `PreferenceRecord(TypedDict, total=False)`를 추가하고 `PerPreferenceStats`를 `reliability_stats` 필드에 재사용했습니다.
- `storage/preference_store.py`에서 `PreferenceRecord`를 import하고 `_scan_all()`, CRUD, lifecycle, list/query, reviewed-candidate persistence 반환 타입을 `PreferenceRecord` 표면으로 통일했습니다.
- 신규 JSON preference record와 refreshed record에 기본 `reliability_stats: {"applied_count": 0, "corrected_count": 0}`를 보존하도록 했습니다.
- `tests/test_preference_store.py`에 `promote_from_corrections()`가 typed preference 핵심 필드와 기본 `reliability_stats`를 반환하는지 확인하는 테스트를 추가했습니다.
- `docs/MILESTONES.md`에 M57 Preference Type Schema Axis 1 항목을 추가했습니다.

## 검증

- `python3 -m py_compile core/contracts.py storage/preference_store.py`
  - 통과
- `python3 -m unittest -v tests.test_preference_store`
  - 통과, 30개 테스트 OK
- `python3 -m unittest -v tests.test_preference_handler`
  - 통과, 20개 테스트 OK
- `git diff --check -- core/contracts.py storage/preference_store.py tests/test_preference_store.py docs/MILESTONES.md`
  - 통과
- `rg -n -- "-> dict\\[str, Any\\] \\| None|-> list\\[dict\\[str, Any\\]\\]|-> dict\\[str, Any\\]" storage/preference_store.py`
  - 매치 없음

## 남은 리스크

- `storage/sqlite_store.py`의 `SQLitePreferenceStore` 타입 표면은 handoff 경계상 Axis 2 대상이라 변경하지 않았습니다.
- browser/E2E와 전체 unittest는 실행하지 않았습니다. 이번 변경은 backend type/persistence 표면과 단위 테스트에 한정했습니다.
- 별도 정적 타입 검사 도구는 실행하지 않았습니다.
