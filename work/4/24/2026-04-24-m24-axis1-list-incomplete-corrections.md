# 2026-04-24 M24 Axis 1 list incomplete corrections

## 변경 파일
- `storage/correction_store.py`
- `storage/sqlite_store.py`
- `scripts/audit_traces.py`
- `tests/test_correction_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m24-axis1-list-incomplete-corrections.md`

## 사용 skill
- `doc-sync`: M24 정의와 Axis 1 shipped entry를 현재 구현 사실에 맞춰 `docs/MILESTONES.md`에 반영했습니다.
- `finalize-lite`: handoff acceptance 기준의 좁은 검증만 실행하고 `/work` closeout을 실제 결과 기준으로 정리했습니다.

## 변경 이유
- advisory recovery seq 100과 implement handoff seq 101은 correction lifecycle의 미완료 상태(`RECORDED`, `CONFIRMED`, `PROMOTED`)를 수동 스캔 없이 조회할 수 있게 하는 observability slice를 요구했습니다.
- 지금까지는 correction이 lifecycle에 진입한 뒤 `ACTIVE` 또는 `STOPPED`까지 도달하지 못한 record를 JSON/SQLite 어느 경로에서도 직접 질의할 수 없었고, `scripts/audit_traces.py`에서도 그 수를 표면화하지 못했습니다.
- 이번 라운드는 correction lifecycle health를 read-only로 관찰 가능하게 만드는 bounded storage + audit script slice입니다.

## 핵심 변경
- `storage/correction_store.py`
  - `list_incomplete_corrections()`를 추가했습니다.
  - JSON store는 `_scan_all()` 결과에서 `RECORDED`, `CONFIRMED`, `PROMOTED` 상태만 필터링합니다.
- `storage/sqlite_store.py`
  - `SQLiteCorrectionStore.list_incomplete_corrections()`를 추가했습니다.
  - SQLite store는 `WHERE status IN (?, ?, ?)` 질의로 같은 세 상태만 조회하고 `created_at ASC` 순으로 반환합니다.
- `scripts/audit_traces.py`
  - `CorrectionStore()`를 사용해 미완료 correction 수를 집계하고 출력합니다.
  - 출력은 최대 5건까지만 `correction_id`, `status`, `created`를 보여 주고, 초과분은 `… and N more`로 잘라냅니다.
- `tests/test_correction_store.py`
  - JSON store에서 non-terminal record만 반환하는지 검증하는 신규 테스트 1건을 추가했습니다.
- `tests/test_sqlite_store.py`
  - SQLite store에서 non-terminal record만 반환하는지 검증하는 신규 테스트 1건을 추가했습니다.
- `docs/MILESTONES.md`
  - `Milestone 24: Correction Lifecycle Observability` 정의와 Axis 1 shipped entry를 추가했습니다.

## 검증
- `python3 -m py_compile storage/correction_store.py storage/sqlite_store.py scripts/audit_traces.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_correction_store tests.test_sqlite_store -v`
  - 통과: `Ran 51 tests in 0.138s`, `OK`
  - 신규 테스트 포함:
    - `test_list_incomplete_corrections_returns_only_non_terminal_records` (`tests.test_correction_store`)
    - `test_list_incomplete_corrections_returns_only_non_terminal_records` (`tests.test_sqlite_store`)
- `git diff --check -- storage/correction_store.py storage/sqlite_store.py scripts/audit_traces.py tests/test_correction_store.py tests/test_sqlite_store.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- handoff boundary 목록에는 test 파일이 빠져 있었지만 acceptance가 store별 신규 unit test 2건을 명시하고 있어, 그 요구를 맞추기 위해 최소 테스트 파일 2개를 함께 수정했습니다.
- `scripts/audit_traces.py`는 handoff 지시대로 JSON `CorrectionStore` 기본 경로(`data/corrections`)만 사용합니다. SQLite parity는 store 메서드 수준에서만 확보됐고, script 자체는 SQLite DB를 직접 읽지 않습니다.
- 이번 라운드는 storage + script observability slice만 다뤘으므로 browser/Playwright 검증은 재실행하지 않았습니다.
- 작업 시작 시점에 이미 존재하던 unrelated dirty/untracked 상태(`pipeline_runtime/operator_autonomy.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `watcher_prompt_assembly.py`, 일부 `report/gemini/*`, `work/4/23/*`)는 건드리지 않았습니다.
