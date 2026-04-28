# 2026-04-28 M65 Axis 1 SQLite CorrectionStore Parity

## 변경 파일
- `storage/sqlite_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m65-axis1-sqlite-correction-store-parity.md`

## 사용 skill
- `security-gate`: SQLite correction 상태 갱신 경로가 write-capable 동작이라 기존 `CORRECTION_STATUS_TRANSITIONS` 가드 재사용과 로컬 저장소 경계를 확인했습니다.
- `doc-sync`: SQLite parity 완료 사실을 `docs/MILESTONES.md`에 현재 구현 범위만 반영했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M64 Axis 1에서 JSON `CorrectionStore`에는 `_scan_all()`과 `confirm_by_fingerprint()` 기반의 summary/confirm-pattern 경로가 준비되었습니다.
- 기본 SQLite 백엔드의 `SQLiteCorrectionStore`에는 두 메서드가 없어 `/api/corrections/summary`와 `/api/corrections/confirm-pattern`에서 `AttributeError`가 날 수 있었습니다.

## 핵심 변경
- `SQLiteCorrectionStore._scan_all()`을 추가해 SQLite `corrections` 전체 레코드를 `created_at` 순서로 반환합니다.
- `SQLiteCorrectionStore.confirm_by_fingerprint()`를 추가해 JSON store와 동일하게 `find_by_fingerprint()` 후 기존 `confirm_correction()` 전이 가드를 순차 재사용합니다.
- `tests/test_sqlite_store.py`에 `_scan_all()` 전체 조회와 fingerprint batch confirm 테스트를 추가했습니다.
- `docs/MILESTONES.md`에 M65 Axis 1 SQLite parity 항목을 추가했습니다.
- `CORRECTION_STATUS_TRANSITIONS`, backend route, frontend, dist, E2E는 변경하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile storage/sqlite_store.py`
- 통과: `python3 -m unittest -v tests.test_sqlite_store` (32 tests)
- 통과: `git diff --check -- storage/sqlite_store.py tests/test_sqlite_store.py docs/MILESTONES.md`

## 남은 리스크
- 이번 변경은 SQLite correction store parity에 한정되어 전체 unittest, 전체 Playwright, 장기 soak는 실행하지 않았습니다.
- frontend / dist / E2E는 handoff상 불필요한 backend-only 범위라 실행하거나 수정하지 않았습니다.
- commit, push, branch/PR publish는 수행하지 않았습니다.
