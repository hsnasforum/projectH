# 2026-04-23 M21 Axis 1 SQLite correction lifecycle parity

## 변경 파일
- `storage/sqlite_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m21-axis1-sqlite-correction-lifecycle.md`

## 사용 skill
- `security-gate`: SQLite correction lifecycle 전이가 로컬 저장소의 status/data를 바꾸는 경로라서 approval 우회나 파괴적 동작 없이 지정 record만 갱신하는지 확인했습니다.
- `doc-sync`: M21 Axis 1 shipped infrastructure 문구를 현재 구현과 테스트 범위에 맞춰 `docs/MILESTONES.md`에 반영했습니다.
- `finalize-lite`: handoff acceptance check만 좁게 재실행하고 Playwright/integration 범위로 넓히지 않았습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 87 기준으로 JSON `CorrectionStore`에는 존재하던 `confirm_correction`, `promote_correction`, `activate_correction`, `stop_correction` lifecycle 메서드가 `SQLiteCorrectionStore`에는 빠져 있었습니다.
- SQLite가 기본 저장소가 된 뒤 correction lifecycle contract가 JSON/SQLite 사이에서 갈라지지 않도록 parity를 맞추기 위해서입니다.

## 핵심 변경
- `SQLiteCorrectionStore._transition()`을 추가해 correction row를 찾고, 없으면 `None`을 반환하도록 했습니다.
- `_transition()`은 `with self._lock` 안에서 `status` 컬럼, `data` JSON blob의 `status`, lifecycle timestamp field, `updated_at`을 함께 갱신하고 commit합니다.
- `confirm_correction`, `promote_correction`, `activate_correction`, `stop_correction` 메서드를 JSON `CorrectionStore` contract와 같은 이름/상태 전이로 추가했습니다.
- `tests/test_sqlite_store.py`에 lifecycle 전이 4건과 missing-id 1건, 총 5개 테스트를 추가했습니다. 전이 테스트는 반환값, `get()` 결과, 원시 SQLite row의 `status` 컬럼과 `data` JSON blob을 함께 확인합니다.
- `docs/MILESTONES.md`에 M21 Axis 1 SQLite correction lifecycle parity shipped infrastructure를 추가했습니다.

## 검증
- `python3 -m py_compile storage/sqlite_store.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_sqlite_store -v`
  - 통과: `Ran 25 tests in 0.081s`, `OK`
- `git diff --check -- storage/sqlite_store.py tests/test_sqlite_store.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- 이번 round는 handoff 경계에 따라 `storage/correction_store.py`, handlers, serializers, Playwright/integration 테스트를 변경하지 않았습니다.
- lifecycle 전이는 JSON store와 동일하게 상태 순서 검증을 추가하지 않습니다. 잘못된 순서 방지는 이번 Axis 1 parity 범위가 아닙니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m20-closure-consolidation.md`, `report/gemini/2026-04-23-m21-definition.md`는 이번 implement round에서 건드리지 않았습니다.
