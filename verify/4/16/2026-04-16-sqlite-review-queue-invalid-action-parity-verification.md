# 2026-04-16 sqlite review queue invalid-action parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-sqlite-review-queue-invalid-action-parity.md`는 SQLite 백엔드에서 `submit_candidate_review`의 invalid action error guard가 service-level parity 기준으로 닫혔다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 rerun 결과에 맞는지 확인하고, 같은 sqlite parity 축에서 다음 한 슬라이스를 자동 확정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `tests/test_web_app.py`에는 `test_submit_candidate_review_rejects_invalid_action_with_sqlite_backend`가 추가되어 있습니다.
  - 이 테스트는 `storage_backend="sqlite"`에서 service를 만들고 `submit_candidate_review(..., review_action="bogus")` 호출 시 `WebApiError`가 발생하는지, `status_code == 400`인지, 에러 메시지에 `지원하지 않는 review action`이 포함되는지를 확인합니다.
  - 이번 슬라이스에서 새 구현 hunk는 보이지 않으며, `/work` 설명대로 invalid-action guard는 storage backend와 무관한 service-layer validation 위에 sqlite regression 한 건만 추가된 상태입니다.
- 최신 `/work`의 focused rerun 검증도 현재 그대로 통과했습니다.
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_rejects_invalid_action_with_sqlite_backend`
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend`
  - `python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py`
  - `git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
- 따라서 최신 `/work`는 truthful합니다.
  - SQLite backend에서는 review queue family의 `accept` / `reject` / `defer` happy path에 이어 `invalid_action` guard까지 service-level parity 기준으로 verification-backed 상태가 되었습니다.

## 검증
- `git status --short`
  - 결과: dirty tree에는 rolling `.pipeline` runtime 파일, same-day `/work` / `/verify` notes, earlier sqlite helper parity hunk가 남아 있는 `storage/sqlite_store.py`, same-day sqlite regressions가 누적된 `tests/test_web_app.py`, unrelated watcher/controller 파일이 함께 존재
- `git diff --unified=3 -- tests/test_web_app.py`
  - 결과: earlier same-day sqlite parity tests 위에 sqlite review invalid-action regression 한 건이 추가된 것 확인
- `rg -n "test_submit_candidate_review_rejects_invalid_action_with_sqlite_backend|test_submit_candidate_review_rejects_invalid_action|submit_candidate_review\\(|review_action=\\\"bogus\\\"|지원하지 않는 review action" tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: `/work`가 근거로 든 sqlite invalid-action test, 기존 JSON-side peer test, `app.web` entrypoint 위치 확인
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_rejects_invalid_action_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: 출력 없음
- full `python3 -m unittest -v`, Playwright/browser smoke, direct SQLite `task_log` table inspection은 미실행
  - 이유: 최신 `/work`는 browser-visible contract를 바꾸지 않았고, 이번 라운드의 목적은 sqlite review queue invalid-action guard의 focused service-level 재확인으로 충분했습니다.

## 남은 리스크
- SQLite 백엔드에서 review queue family 전체 (`accept` / `reject` / `defer` happy path + `invalid_action` guard)는 service-level parity 기준으로 닫혔습니다.
- 남은 sqlite parity 중 더 user-visible한 current-risk는 content-side blank-note validation입니다. JSON-side에는 `test_submit_content_reason_note_rejects_blank_note`가 있으나, SQLite 백엔드 parity test는 아직 없습니다.
- direct SQLite `task_log` row contents와 browser-level sqlite smoke는 여전히 미검증이지만, 둘 다 현재 shipped validation contract보다 audit-depth 또는 broader-coverage 성격이 더 강합니다.
- 따라서 다음 exact slice는 `sqlite-content-reject-blank-note-validation-parity`로 고르는 편이 맞습니다.
