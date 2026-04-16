# 2026-04-16 sqlite content reject late-flip save-history parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-sqlite-content-reject-late-flip-save-history-parity.md`는 SQLite 백엔드에서도 original-draft 저장 뒤 늦은 `content_verdict = rejected`가 기존 note 파일과 save history를 덮어쓰지 않는다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 focused rerun 결과에 맞는지 확인하고, 같은 sqlite content reject family에서 남은 다음 한 슬라이스를 고정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `tests/test_web_app.py`에는 `test_submit_content_verdict_after_original_draft_save_preserves_saved_history_with_sqlite_backend`가 추가되어 있습니다.
  - 이 테스트는 `storage_backend="sqlite"`에서 `save_summary=True`와 `approved=True`로 original-draft save를 완료한 뒤, 같은 source message에 `submit_content_verdict(..., content_verdict="rejected")`를 호출합니다.
  - 이어서 저장된 note 파일이 계속 존재하고 body가 바뀌지 않는지, source message가 `saved_note_path`를 유지하는지, `corrected_outcome.outcome == "rejected"`인지, `corrected_outcome.saved_note_path is None`인지, saved-note message가 같은 `artifact_id`와 `save_content_source = original_draft`를 유지하는지를 확인합니다.
  - 현재 tree 기준으로 이번 슬라이스에서 추가로 확인되는 범위는 sqlite regression 한 건이며, late-flip save-history 보존 동작 자체는 기존 content/save trace 경로를 그대로 재사용합니다.
- 최신 `/work`의 focused rerun 검증도 현재 그대로 통과했습니다.
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_after_original_draft_save_preserves_saved_history_with_sqlite_backend`
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend`
  - `python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py`
  - `git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
- 따라서 최신 `/work`는 truthful합니다.
  - SQLite 백엔드에서 content reject/reason family는 happy path, blank-note guard, late-flip save-history까지 service-level parity 기준으로 닫혔습니다.

## 검증
- `git status --short`
  - 결과: dirty tree에는 rolling `.pipeline` runtime 파일, same-day `/work` / `/verify` notes, earlier sqlite helper hunk가 남아 있는 `storage/sqlite_store.py`, same-day sqlite regressions가 누적된 `tests/test_web_app.py`, unrelated watcher/controller 파일이 함께 존재
- `git diff -- tests/test_web_app.py`
  - 결과: 기존 JSON-side late-flip peer 옆에 sqlite late-flip save-history regression이 추가된 것 확인
- `rg -n "test_submit_content_verdict_after_original_draft_save_preserves_saved_history_with_sqlite_backend|test_submit_content_verdict_after_original_draft_save_preserves_saved_history|test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend|save_content_source|saved_note_path" tests/test_web_app.py`
  - 결과: `/work`가 근거로 든 sqlite late-flip test와 `saved_note_path` / `save_content_source` 관련 단언 위치 확인
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_after_original_draft_save_preserves_saved_history_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: 출력 없음
- full `python3 -m unittest -v`, Playwright/browser smoke, direct SQLite `task_log` row inspection, `superseded_reject_signal` replay 검증은 미실행
  - 이유: 최신 `/work`는 browser-visible contract를 바꾸지 않았고, 이번 라운드의 목적은 sqlite late-flip save-history contract의 focused service-level 재확인으로 충분했습니다.

## 남은 리스크
- SQLite 백엔드에서 content reject/reason family의 service-level parity는 닫혔지만, audit-depth parity는 아직 직접 닫히지 않았습니다. 현재 sqlite 쪽 `...and_logs_with_sqlite_backend` 테스트들은 persisted reload 상태를 확인할 뿐, `task_log` row 내용을 직접 보지 않습니다.
- `storage/sqlite_store.py`에는 이미 `SQLiteTaskLogger.iter_session_records(session_id)`가 있으므로, 같은 family에서 남은 가장 작은 current-risk reduction은 `content_verdict_recorded`와 `content_reason_note_recorded`가 실제 SQLite `task_log` 행으로 남는지 직접 고정하는 것입니다.
- `superseded_reject_signal`/audit replay helper와 browser-level sqlite smoke는 여전히 남아 있지만, 둘 다 direct task-log row parity보다 한 단계 뒤의 audit-depth 또는 broader browser 범위입니다.
- 따라서 다음 exact slice는 `sqlite-content-reject-task-log-row-parity`가 맞습니다.
