# 2026-04-23 M18 Axis 1 SQLite correction store

## 변경 파일
- `storage/sqlite_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m18-axis1-sqlite-correction-store.md`

## 사용 skill
- `security-gate`: correction persistence와 migration 변경이 local-first, additive, active wiring 없음 경계를 지키는지 확인했습니다.
- `doc-sync`: M18 Axis 1 shipped infrastructure와 guardrail을 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `finalize-lite`: 지정된 py_compile, unittest, diff whitespace 검증 결과만 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 검증을 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 60 / advisory seq 59 기준 cross-session recurrence 기반을 위해 JSON `CorrectionStore`의 핵심 lookup 경로와 SQLite `corrections` 테이블 간 parity가 필요했습니다.
- 현재 서버의 active `correction_store`를 SQLite로 전환하는 작업은 이번 범위가 아니므로, 저장소 클래스와 JSON-to-SQLite migration만 추가했습니다.

## 핵심 변경
- `storage/sqlite_store.py`에 `SQLiteCorrectionStore`를 추가해 `record_correction`, `get`, `find_by_fingerprint`, `find_by_artifact`, `find_by_session`, `list_recent`를 구현했습니다.
- `record_correction`은 `compute_correction_delta` 결과가 없으면 `None`을 반환하고, 같은 fingerprint/artifact/session/source message 조합은 기존 record를 반환하며, 같은 fingerprint의 기존 record에는 recurrence count와 `last_seen_at`을 갱신합니다.
- `migrate_json_to_sqlite`가 더 이상 correction JSON을 경고로 제외하지 않고, 기존 schema의 `corrections` 테이블에 `INSERT OR IGNORE`로 복사합니다.
- `tests/test_sqlite_store.py`에 `SQLiteCorrectionStore` 단위 테스트 7개를 추가했습니다.
- `docs/MILESTONES.md`에 Milestone 18 Axis 1 정의와 shipped infrastructure를 추가했습니다.

## 검증
- `python3 -m py_compile storage/sqlite_store.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_sqlite_store -v`
  - 통과: `Ran 14 tests in 0.018s`, `OK`
  - 새 `SQLiteCorrectionStore` 테스트 7개 포함
- `git diff --check -- storage/sqlite_store.py docs/MILESTONES.md tests/test_sqlite_store.py`
  - 통과: 출력 없음

## 남은 리스크
- 이번 slice는 backend-only foundation입니다. `app/web.py`나 handler wiring을 바꾸지 않았으므로 runtime server는 여전히 JSON `CorrectionStore`를 기본으로 사용합니다.
- `find_recurring_patterns`와 correction lifecycle transition 메서드는 handoff boundary에 따라 SQLite에 구현하지 않았습니다.
- migration은 로컬 SQLite DB로 correction JSON을 복사하는 write-capable 작업이지만, destructive overwrite가 아니며 `INSERT OR IGNORE`로 재실행 가능합니다. 실제 대량 migration 실행은 이번 검증 범위에 포함하지 않았습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m17-closure-release-gate.md`, `report/gemini/2026-04-23-m18-definition.md`는 이번 round에서 건드리지 않았습니다.
