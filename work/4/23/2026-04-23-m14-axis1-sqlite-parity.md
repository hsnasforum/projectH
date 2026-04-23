# 2026-04-23 M14 Axis 1 SQLite PreferenceStore parity

## 변경 파일
- `storage/sqlite_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m14-axis1-sqlite-parity.md`

## 사용 skill
- `doc-sync`: 구현 변경이 M14 정의와 shipped axis 기록에만 반영되면 되는지 확인했습니다.
- `finalize-lite`: 구현 종료 전 실제 실행한 검증, 문서 동기화 범위, `/work` closeout 준비 상태를 함께 점검했습니다.
- `work-log-closeout`: closeout 형식과 필수 항목에 맞춰 변경 파일, 검증, 남은 리스크를 기록했습니다.

## 변경 이유
- M13 Axis 6에서 JSON-backed `PreferenceStore`는 `cross_session_count >= 3` 후보 자동 활성화를 지원하지만, `SQLitePreferenceStore`는 같은 lifecycle parity가 없었습니다.
- SQLite backend를 사용하는 경우 reviewed candidate source ref가 누적되어도 `cross_session_count`가 증가하지 않아 후보가 threshold에 도달할 수 없었습니다.
- M14 Axis 1 범위는 backend parity이며, 사용자 수준 memory 확장이나 frontend 변경은 포함하지 않습니다.

## 핵심 변경
- `SQLitePreferenceStore`가 `storage.preference_store.AUTO_ACTIVATE_CROSS_SESSION_THRESHOLD`를 재사용하고, import 실패 시 로컬 fallback 값 `3`을 사용하도록 했습니다.
- SQLite update path에서 새 `source_refs.candidate_id`가 추가될 때만 `cross_session_count`를 1 증가시킵니다.
- `_auto_activate_candidate_if_ready()`를 추가해 `status == "candidate"`이고 `cross_session_count >= 3`이면 dict와 SQL row의 `status`, `activated_at`, `updated_at`, `data`를 함께 갱신합니다.
- `ACTIVE`, `REJECTED`, `PAUSED` 상태는 자동 활성화 helper가 변경하지 않도록 유지했습니다.
- `tests/test_sqlite_store.py`에 threshold 미만 유지, threshold 도달 시 활성화, active/rejected 상태 보존 테스트를 추가했습니다.
- `docs/MILESTONES.md`에 M14 정의와 Axis 1 shipped 항목을 추가했습니다.

## 검증
- `python3 -m py_compile storage/sqlite_store.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_sqlite_store -v`
  - 통과: `5 tests`
- `git diff --check -- storage/sqlite_store.py tests/test_sqlite_store.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- 이번 라운드는 handoff acceptance에 맞춰 `tests.test_sqlite_store`만 실행했습니다. 전체 test suite와 browser smoke는 실행하지 않았습니다.
- SQLite의 `record_reviewed_candidate_preference()`는 기존 설계대로 reviewed candidate source ref 추가를 cross-session evidence 증가로 취급합니다. 실제 session id distinct count 재계산으로 바꾸는 작업은 이번 parity slice 범위가 아닙니다.
