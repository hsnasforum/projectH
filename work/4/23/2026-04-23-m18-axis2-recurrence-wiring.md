# 2026-04-23 M18 Axis 2 recurrence wiring

## 변경 파일
- `storage/sqlite_store.py`
- `app/web.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m18-axis2-recurrence-wiring.md`

## 사용 skill
- `security-gate`: sqlite backend에서 correction persistence가 JSON fallback에서 SQLite로 전환되는 경계를 확인했습니다. 변경은 로컬 DB backend 내부 wiring이며 승인/외부 네트워크/브라우저 계약은 바꾸지 않았습니다.
- `doc-sync`: M18 Axis 2 shipped infrastructure를 `docs/MILESTONES.md`에 좁게 반영했습니다.
- `finalize-lite`: handoff가 지정한 py_compile, unittest, diff whitespace 검증만 실행하고 Playwright는 실행하지 않았습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 검증을 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 63 / advisory seq 62 기준 SQLite correction store가 핵심 lookup parity를 넘어서 recurrence discovery와 sqlite backend runtime wiring까지 담당해야 했습니다.
- cross-session recurrence 탐색은 전체 correction row를 Python에서 모아 그룹화하지 않고 SQL `GROUP BY`로 좁혀야 했습니다.

## 핵심 변경
- `SQLiteCorrectionStore.find_recurring_patterns()`를 추가해 `delta_fingerprint`별 `COUNT(*) >= 2` 그룹만 SQL `GROUP BY ... HAVING`으로 찾습니다.
- `session_id`가 주어진 경우 해당 session 안에서만 반복 fingerprint를 세고, 반환 shape은 JSON `CorrectionStore`의 `find_recurring_patterns()` 계약과 맞췄습니다.
- `app/web.py`의 `storage_backend == "sqlite"` 분기에서 `SQLiteCorrectionStore(db)`를 active `correction_store`로 연결했습니다.
- JSON backend 분기의 `CorrectionStore`와 `storage/correction_store.py`는 변경하지 않았습니다.
- `tests/test_sqlite_store.py`에 전체 recurrence detection과 session filter 테스트 2개를 추가했습니다.
- `docs/MILESTONES.md`에 M18 Axis 2 shipped infrastructure를 추가했습니다.

## 검증
- `python3 -m py_compile storage/sqlite_store.py app/web.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_sqlite_store -v`
  - 통과: `Ran 16 tests in 0.022s`, `OK`
  - 새 `find_recurring_patterns` 테스트 2개 포함
- `git diff --check -- storage/sqlite_store.py app/web.py docs/MILESTONES.md tests/test_sqlite_store.py`
  - 통과: 출력 없음

## 남은 리스크
- 이번 slice는 backend-only wiring입니다. handoff boundary대로 Playwright는 실행하지 않았고, 브라우저-facing API나 UI 계약은 변경하지 않았습니다.
- sqlite backend를 실제 runtime으로 켜면 correction 기록은 SQLite에 저장됩니다. 기존 JSON correction 파일을 SQLite로 옮기는 작업은 Axis 1 migration 경로에 의존하며, 이번 round에서 대량 migration을 실행하지 않았습니다.
- SQLite correction lifecycle transition 메서드는 아직 없습니다. 이번 handoff는 recurrence indexing과 server wiring까지만 요구했습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m18-axis2-indexing-scope.md`는 이번 round에서 건드리지 않았습니다.
