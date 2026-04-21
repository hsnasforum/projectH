# 2026-04-21 sqlite store adoption list test

## 변경 파일
- `tests/test_sqlite_store.py`
- `work/4/21/2026-04-21-sqlite-store-adoption-list-test.md`

## 사용 skill
- `work-log-closeout`: handoff 수행 후 실제 변경 파일, 실행한 검증, 남은 수치 불일치 리스크를 한국어 closeout 형식으로 정리했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 606은 `SQLiteSessionStore`의 public-method adoption list를 `tests/test_sqlite_store.py`에 고정하라고 지시했습니다.
- seq 605 처방은 8개 메서드가 빠져 `NotImplementedError` stub을 추가해야 한다고 보았지만, 실제로는 `storage/sqlite_store.py`의 class-attribute delegation 패턴으로 public methods가 이미 연결되어 있었습니다.
- seq 605 불일치 원인은 verify lane이 `def` 선언만 grep하면서 class-attribute delegation 패턴을 놓친 것으로 정리했습니다.

## 핵심 변경
- `tests/test_sqlite_store.py`를 새로 만들고 `TestSQLiteSessionStoreAdoptionList` 1개 클래스와 `test_adoption_list_all_methods_accessible` 1개 테스트 메서드를 추가했습니다.
- `REQUIRED_METHODS`에는 handoff가 지정한 22개 public method를 그대로 넣었고, 각 method는 `with self.subTest(method=name)` 안에서 `hasattr(SQLiteSessionStore, name)`만 확인합니다.
- `storage/sqlite_store.py`는 수정하지 않았습니다. 선행 dirty worktree에는 `_compact_summary_hint_for_persist = staticmethod(_SS._compact_summary_hint_for_persist)` 1줄 delegation이 이미 존재합니다.
- `tests/test_pipeline_runtime_supervisor.py`도 수정하지 않았습니다. 현재 파일에는 선행 변경으로 `test_classify_operator_candidate_defaults_decision_class_per_visible_mode`와 `test_classify_operator_candidate_payload_stability`가 모두 존재합니다.
- handoff는 supervisor suite를 105개로 예상했지만, 실제 현재 작업트리에서는 106개가 실행되었습니다. 이 라운드의 변경은 `tests/test_sqlite_store.py` 추가뿐이라 supervisor count 증가는 선행 변경 상태의 수치 불일치로 기록합니다.

## 검증
- `python3 -m unittest tests.test_sqlite_store`
  - `Ran 1 test in 0.001s`
  - `OK`
  - subTests로 22개 required method 접근성을 확인했습니다.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 106 tests in 1.035s`
  - `OK`
  - handoff 예상 `105/105 OK`와 달리 현재 작업트리 실측은 `106/106 OK`입니다.
- `python3 -m py_compile storage/sqlite_store.py`
  - 출력 없음, `rc=0`
- `git diff --check -- tests/test_sqlite_store.py`
  - 출력 없음, `rc=0`

## 남은 리스크
- supervisor regression count가 handoff 예상 105개와 다르게 106개입니다. `tests/test_pipeline_runtime_supervisor.py`는 이 라운드에서 건드리지 않았고, 현재 선행 변경에는 `test_classify_operator_candidate_*` 테스트가 2개 존재합니다.
- `git diff --check -- tests/test_sqlite_store.py`는 handoff 지시 그대로 실행해 통과했지만, 새 파일이 아직 untracked 상태라 diff 출력 자체는 없었습니다.
- AXIS-DISPATCHER-TRACE-BACKFILL, AXIS-G6, AXIS-G4 end-to-end live runtime은 handoff가 명시한 대로 verify-lane 범위이며 이번 implement 작업에서는 다루지 않았습니다.
