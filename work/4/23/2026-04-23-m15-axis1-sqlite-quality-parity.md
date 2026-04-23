# 2026-04-23 M15 Axis 1 SQLite quality parity

## 변경 파일
- `storage/preference_store.py`
- `storage/sqlite_store.py`
- `app/handlers/aggregate.py`
- `tests/test_preference_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m15-axis1-sqlite-quality-parity.md`

## 사용 skill
- `doc-sync`: M15 정의와 Axis 1 shipped 기록을 `docs/MILESTONES.md`에 현재 구현 기준으로 반영했습니다.
- `finalize-lite`: handoff acceptance 검증과 추가 focused 확인 결과, 남은 미검증 범위를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 통과/실패 결과를 `/work` 형식에 맞춰 기록했습니다.

## 변경 이유
- handoff는 advisory seq 32 기준 M15 Axis 1 SQLite quality parity를 요청했습니다.
- M14 Axis 2에서 correction promotion 경로는 `avg_similarity_score`를 저장했지만, reviewed-candidate accept 경로인 `record_reviewed_candidate_preference()`는 JSON/SQLite 양쪽 모두 score를 받지 않았습니다.
- `list_preferences_payload()`는 이미 `avg_similarity_score` 기반 `quality_info`를 계산하므로, accept 경로에서 score를 저장하면 추가 preferences handler 변경 없이 quality 표시가 이어집니다.

## 핵심 변경
- JSON `PreferenceStore.record_reviewed_candidate_preference()`에 optional `avg_similarity_score` 파라미터를 추가하고, create path에서 저장하도록 했습니다.
- JSON update path는 새 score가 `None`이 아닐 때만 `avg_similarity_score`를 갱신하고, 새 값이 `None`이면 기존 score를 보존합니다.
- SQLite `SQLitePreferenceStore.record_reviewed_candidate_preference()`도 같은 signature와 create/update 저장 정책을 갖도록 맞췄습니다.
- `AggregateHandlerMixin.submit_candidate_review()` accept branch가 source message `artifact_id`로 `correction_store.find_by_artifact()`를 조회해 평균 `similarity_score`를 계산한 뒤 preference store로 전달합니다.
- JSON/SQLite 단위 테스트에 score 저장과 `None` update 보존 케이스를 각각 추가했습니다.
- `docs/MILESTONES.md`에 M15 정의와 Axis 1 shipped 항목을 추가했습니다.

## 검증
- `python3 -m py_compile storage/preference_store.py storage/sqlite_store.py app/handlers/aggregate.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_preference_store tests.test_sqlite_store -v`
  - 통과: `31 tests`
- `git diff --check -- storage/preference_store.py storage/sqlite_store.py app/handlers/aggregate.py docs/MILESTONES.md`
  - 통과: 출력 없음
- `git diff --check -- storage/preference_store.py storage/sqlite_store.py app/handlers/aggregate.py docs/MILESTONES.md tests/test_preference_store.py tests/test_sqlite_store.py`
  - 통과: 출력 없음
- 추가 확인: `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate -v`
  - 실패: 해당 테스트가 `corrections_dir`를 temp로 고정하지 않아 repo-local `data/corrections`를 읽고, 기존 correction evidence에 의해 preference가 `active`로 auto-activation되어 `candidate_count == 0`이 되었습니다. 이번 handoff acceptance 범위 밖 fixture 격리 문제로 판단해 production/test 수정은 하지 않았습니다.

## 남은 리스크
- 전체 test suite와 Playwright browser smoke는 실행하지 않았습니다.
- aggregate accept 경로는 focused 웹 테스트에서 repo-local fixture 오염으로 통과 확인을 못 했습니다. 다만 handoff acceptance의 storage parity tests와 compile checks는 통과했습니다.
- `avg_similarity_score` 평균 계산은 handoff 지시대로 `aggregate.py`에 inline 구현했습니다. 동일 평균 계산 중복을 공유 helper로 정리하는 작업은 이번 slice 범위가 아닙니다.
