# 2026-04-16 sqlite review queue reject/defer parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-sqlite-review-queue-reject-defer-parity.md`는 SQLite 백엔드에서 shipped review queue `reject` / `defer` 경로가 service-level + reload persistence 기준으로 닫혔다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 rerun 결과에 맞는지 확인하고, 같은 sqlite parity 축에서 다음 한 슬라이스를 자동 확정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `tests/test_web_app.py`에는 `test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend`와 `test_submit_candidate_review_defer_records_and_removes_queue_item_with_sqlite_backend`가 추가되어 있습니다.
  - 두 테스트 모두 `storage_backend="sqlite"`에서 grounded-brief → correction → corrected save → approval → candidate confirmation까지 만든 뒤 `submit_candidate_review(..., review_action="reject" | "defer")`를 호출하고, `review_queue_items` 제거와 `candidate_review_record` 상태를 즉시 확인한 뒤 `get_session_payload(session_id)` reload 후에도 동일 상태가 유지되는지 검증합니다.
  - 이번 슬라이스에서 새 구현 hunk는 보이지 않으며, `/work` 설명대로 `SQLiteSessionStore.record_candidate_review_for_message`의 기존 `SessionStore` 바인딩 위에 sqlite regression 두 건만 추가된 상태입니다.
- 최신 `/work`의 focused rerun 검증도 현재 그대로 통과했습니다.
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend`
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend`
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend`
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_defer_records_and_removes_queue_item_with_sqlite_backend`
  - `python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py`
  - `git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
- 따라서 최신 `/work`는 truthful합니다.
  - SQLite backend에서는 review queue `accept`뿐 아니라 `reject` / `defer`의 queue removal + persisted review state도 service-level + reload 기준으로 verification-backed 상태가 되었습니다.

## 검증
- `git status --short`
  - 결과: dirty tree에는 rolling `.pipeline` runtime 파일, same-day `/work` / `/verify` notes, earlier sqlite helper parity hunk가 남아 있는 `storage/sqlite_store.py`, same-day sqlite regressions가 누적된 `tests/test_web_app.py`, unrelated watcher/controller 파일이 함께 존재
- `git diff --unified=3 -- tests/test_web_app.py`
  - 결과: earlier same-day sqlite parity tests 위에 sqlite review queue reject/defer regression 두 건이 추가된 것 확인
- `rg -n "test_submit_candidate_review_(reject|defer)_records_and_removes_queue_item_with_sqlite_backend|test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend|submit_candidate_review\\(|record_candidate_review_for_message" tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: `/work`가 근거로 든 sqlite tests, `app.web` entrypoint, `SQLiteSessionStore` method binding 위치 확인
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_defer_records_and_removes_queue_item_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: 출력 없음
- full `python3 -m unittest -v`, Playwright/browser smoke, direct SQLite `task_log` table inspection은 미실행
  - 이유: 최신 `/work`는 browser-visible contract를 바꾸지 않았고, 이번 라운드의 목적은 sqlite review queue happy-path parity의 focused service-level 재확인으로 충분했습니다.

## 남은 리스크
- SQLite 백엔드에서 review queue `reject` / `defer` happy path는 닫혔지만, 같은 `submit_candidate_review` family의 invalid-action guard는 아직 sqlite-specific regression이 없습니다.
- direct SQLite `task_log` row contents도 여전히 검증되지 않았습니다. 다만 이는 current shipped behavior보다 audit-depth 리스크에 가깝습니다.
- content-side blank-note validation (`submit_content_reason_note` with blank note)도 sqlite parity 관점에서는 남아 있지만, latest `/work`가 닫은 review queue family의 남은 current-risk reduction을 먼저 끝내는 편이 자동 tie-break 순서에 더 맞습니다.
- 따라서 다음 exact slice는 `sqlite-review-queue-invalid-action-parity`로 고르는 편이 맞습니다.
