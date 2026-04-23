# 2026-04-23 M19 Axis 2 discovery integrity

## 변경 파일
- `storage/sqlite_store.py`
- `app/serializers.py`
- `app/handlers/aggregate.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m19-axis2-discovery-integrity.md`

## 사용 skill
- `security-gate`: global candidate discovery와 accept description 기록 경로가 local persistence와 task-log 경계를 벗어나지 않는지 확인했습니다.
- `doc-sync`: M19 Axis 2 shipped infrastructure를 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `finalize-lite`: handoff가 지정한 py_compile, sqlite unittest, diff whitespace 검증만 실행했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 검증을 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 72 / advisory seq 71 기준 global recurrence 후보가 같은 세션 안의 반복만으로 뜨면 안 되고, 이미 드러난 preference/session-local 문장과도 중복되지 않아야 했습니다.
- global candidate accept path는 session-local accept path처럼 사용자가 편집한 statement를 description으로 존중해야 했습니다.

## 핵심 변경
- `SQLiteCorrectionStore.find_recurring_patterns()`의 global path만 `COUNT(DISTINCT session_id) >= 2`로 변경했습니다. `session_id` filter path의 `COUNT(*) >= 2`는 그대로 유지했습니다.
- `_build_review_queue_items` global candidate block이 preference descriptions와 session-local statements를 lowercase/trim 기준으로 비교해 statement-level 중복을 거릅니다.
- global candidates의 `quality_info`를 pattern corrections의 `similarity_score` 평균과 `is_high_quality()` 결과로 채웁니다.
- global accept path가 `statement_override`를 description으로 우선 사용하고, 없을 때만 기존 replacement/fingerprint fallback을 사용합니다.
- `tests/test_sqlite_store.py`에 같은 session 반복은 global recurrence로 보지 않지만 session-scoped recurrence로는 유지되는 regression test를 추가했습니다.

## 검증
- `python3 -m py_compile storage/sqlite_store.py app/serializers.py app/handlers/aggregate.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_sqlite_store -v`
  - 통과: `Ran 18 tests in 0.023s`, `OK`
  - handoff 예상은 17개였지만 현재 suite에는 기존 snippet test까지 포함되어 18개가 실행됐습니다.
- `git diff --check -- storage/sqlite_store.py app/serializers.py app/handlers/aggregate.py docs/MILESTONES.md tests/test_sqlite_store.py`
  - 통과: 출력 없음

## 남은 리스크
- `preference_store.list_all(limit=200)` prefetch는 try/except로 감싸 session-local queue 렌더를 막지 않게 했습니다. 별도 성능 계측은 이번 handoff 범위가 아니어서 실행하지 않았습니다.
- 이번 slice는 browser-visible UI 변경이 없어 handoff boundary대로 Playwright를 실행하지 않았습니다.
- statement dedupe는 trim/lowercase 기준의 단순 비교입니다. 의미적으로 같은 문장이나 번역/형태소 차이는 다음 slice 범위입니다.
- `storage/preference_store.py`, `storage/correction_store.py`, frontend 파일은 handoff boundary에 따라 변경하지 않았습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m19-axis2-integrity-scope.md`는 이번 round에서 건드리지 않았습니다.
