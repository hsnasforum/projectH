# 2026-04-23 M21 Axis 2 durable global reject persistence

## 변경 파일
- `storage/preference_store.py`
- `storage/sqlite_store.py`
- `app/handlers/aggregate.py`
- `tests/test_preference_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m21-axis2-durable-global-reject.md`

## 사용 skill
- `security-gate`: global reject가 로컬 preference 저장소에 REJECTED record를 쓰는 경로라서 write 범위가 fingerprint preference record에만 머무는지 확인했습니다.
- `doc-sync`: M21 Axis 2 shipped infrastructure를 현재 구현 사실에 맞춰 `docs/MILESTONES.md`에 반영했습니다.
- `finalize-lite`: handoff acceptance check만 실행하고 Playwright/browser 범위로 넓히지 않았습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- advisory seq 89와 implement handoff seq 90 기준으로 global review candidate를 reject해도 preference store에 fingerprint record가 남지 않아 같은 global candidate가 세션 로드마다 다시 나타날 수 있었습니다.
- `_build_review_queue_items`는 이미 같은 fingerprint의 preference record가 있으면 global candidate를 제외하므로, global reject를 REJECTED preference로 남겨 기존 dedup 경로를 재사용하기 위해서입니다.

## 핵심 변경
- JSON `PreferenceStore.record_reviewed_candidate_preference()`에 optional `status=` 인자를 추가하고, 새 record와 기존 record 갱신 모두에서 REJECTED status와 `rejected_at`을 저장하도록 했습니다.
- `SQLitePreferenceStore.record_reviewed_candidate_preference()`에도 같은 optional `status=` 인자를 추가해 `status` 컬럼과 `data` JSON blob이 REJECTED 상태를 반영하도록 했습니다.
- global path의 `submit_candidate_review()`에서 `review_action == reject`이면 해당 fingerprint를 REJECTED preference로 기록하도록 했습니다.
- JSON preference store와 SQLite preference store에 REJECTED status 생성/조회 단위 테스트를 각각 1개씩 추가했습니다.
- `docs/MILESTONES.md`의 M21 shipped infrastructure에 Axis 2 durable global reject persistence를 추가했습니다.

## 검증
- `python3 -m py_compile storage/preference_store.py storage/sqlite_store.py app/handlers/aggregate.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_preference_store -v`
  - 통과: `Ran 29 tests in 0.096s`, `OK`
- `python3 -m unittest tests.test_sqlite_store -v`
  - 통과: `Ran 26 tests in 0.083s`, `OK`
- `git diff --check -- storage/preference_store.py storage/sqlite_store.py app/handlers/aggregate.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- 이번 round는 handoff 경계에 따라 `app/serializers.py`와 Playwright/browser smoke를 변경하지 않았습니다.
- global reject의 브라우저 통합 검증은 shared fingerprint를 여러 세션에 의도적으로 만들어야 하므로 M21 Axis 3 smoke gate 범위로 남겼습니다.
- `record_reviewed_candidate_preference()`의 `status=` 값 검증은 추가하지 않았습니다. handoff 기준대로 caller가 유효한 `PreferenceStatus`를 넘기는 얇은 저장소 contract를 유지했습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m20-closure-consolidation.md`, `report/gemini/2026-04-23-m21-axis2-reject-scope.md`, `report/gemini/2026-04-23-m21-definition.md`는 이번 implement round에서 건드리지 않았습니다.
