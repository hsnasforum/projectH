# 2026-04-17 sqlite content reject task-log row parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/17/2026-04-17-sqlite-content-reject-task-log-row-parity.md`는 SQLite 백엔드에서도 content reject/reason family의 task-log row 내용이 직접 검증됐다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 focused rerun 결과에 맞는지 다시 확인하고, 같은 family에서 남은 다음 한 슬라이스를 정확히 고정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `tests/test_web_app.py`에는 `test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend`와 `test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend`가 존재하고, 각각 `service.task_logger.iter_session_records(...)`로 SQLite `task_log` row를 직접 조회합니다.
  - verdict 쪽은 `content_verdict_recorded`와 `corrected_outcome_recorded` row의 `message_id`, `artifact_id`, `artifact_kind`, `source_message_id`, `content_verdict`, `content_reason_record.reason_label` 정합성을 확인합니다.
  - reason-note 쪽은 `content_reason_note_recorded` row의 `reason_scope`, `reason_label`, `reason_note`, `content_reason_record`를 직접 확인하고, 같은 세션의 선행 `content_verdict_recorded` row 존재도 다시 확인합니다.
  - `storage/sqlite_store.py`의 `SQLiteTaskLogger.iter_session_records()`는 이미 parsed `detail`을 돌려주고 있었고, 이번 `/work`가 말한 대로 추가 구현 변경 없이 기존 helper를 재사용하는 구조입니다.
- focused rerun 결과도 최신 `/work`와 일치합니다.
  - SQLite row parity 두 테스트와 직전 same-family prerequisite인 late-flip save-history sqlite 회귀가 모두 통과했습니다.
  - `python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py`는 통과했고, `git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`도 출력 없이 끝났습니다.
- 따라서 최신 `/work`는 truthful합니다.
  - SQLite 백엔드에서 content reject/reason family는 blank-note guard, late-flip save-history, reject/reason task-log row parity까지 service/serialization 전 단계 기준으로 닫혔습니다.
  - 다만 `superseded_reject_signal`의 task-log replay parity는 아직 SQLite 쪽 peer가 없습니다.

## 검증
- `git status --short`
  - 결과: rolling `.pipeline` runtime 파일, same-day `/work`/`/verify` 노트, earlier sqlite/helper/controller hunks가 섞인 dirty tree 상태였습니다.
- `git diff -- tests/test_web_app.py`
  - 결과: `tests/test_web_app.py` 전체는 같은 날 누적 sqlite 회귀들 때문에 크게 더러웠지만, 이번 `/work`가 설명한 task-log row parity 테스트 확장 hunk가 현재 diff 안에 포함되어 있음을 확인했습니다.
- `rg -n "test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend|test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend|iter_session_records\\(|content_verdict_recorded|corrected_outcome_recorded|content_reason_note_recorded" tests/test_web_app.py storage/sqlite_store.py`
  - 결과: 최신 `/work`가 근거로 든 sqlite 테스트 위치와 `SQLiteTaskLogger.iter_session_records()` 위치를 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_records_rejected_outcome_and_logs_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_verdict_after_original_draft_save_preserves_saved_history_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m py_compile storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py storage/sqlite_store.py app/web.py app/serializers.py`
  - 결과: 출력 없음
- `python3 -m unittest -v` 전체, Playwright/browser smoke, SQLite-backed `superseded_reject_signal` parity 테스트는 미실행
  - 이유: 최신 `/work`는 테스트 확장만 다뤘고 browser-visible contract를 바꾸지 않았으며, 이번 검증의 목적은 row parity 주장 재확인에 필요한 focused rerun으로 충분했습니다.

## 남은 리스크
- 현재 tree에는 JSON-backed `superseded_reject_signal` 회귀만 있고 SQLite-backed peer가 없습니다. 따라서 같은 content family에서 남은 가장 작은 current-risk reduction은 task-log replay helper가 SQLite에서도 같은 same-anchor reject replay semantics를 유지하는지 직접 고정하는 것입니다.
- `app/serializers.py`는 이미 `task_logger.iter_session_records()`를 통해 `superseded_reject_signal`를 조립하므로, 다음 exact slice는 `sqlite-superseded-reject-signal-parity`가 맞습니다.
- `historical_save_identity_signal`, browser-level sqlite smoke, broader replay/helper refactor는 모두 그 다음 범위입니다.
