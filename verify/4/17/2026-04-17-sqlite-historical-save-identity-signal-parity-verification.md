# 2026-04-17 sqlite historical save identity signal parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/17/2026-04-17-sqlite-historical-save-identity-signal-parity.md`는 SQLite 백엔드에서도 `historical_save_identity_signal`의 두 JSON-side replay 계약이 그대로 성립한다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 focused rerun 결과에 맞는지 다시 확인하고, 같은 grounded-brief source-message serialization family에서 다음 한 슬라이스를 정확히 고정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `tests/test_web_app.py`에는 `test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend`와 `test_historical_save_identity_signal_requires_same_anchor_write_note_not_approval_granted_only_with_sqlite_backend`가 추가되어 있습니다.
  - 첫 번째 테스트는 SQLite 세션에서 persisted original-draft save 뒤 correction이 발생한 후에도 current `session_local_memory_signal.save_signal`은 유지되고, 별도 `historical_save_identity_signal`만 earlier `write_note` identity를 `task_log_audit` 기준으로 replay하는지 확인합니다.
  - 두 번째 테스트는 SQLite 세션에서 manual `approval_granted` row만 있고 matching persisted `write_note`가 없을 때 `historical_save_identity_signal`이 생기지 않는지 확인합니다.
  - `app/serializers.py`의 `_build_historical_save_identity_signal_index()`와 `_resolve_historical_save_identity_signal_for_message()`는 이미 현재 tree에 존재했고, 이번 slice를 위해 추가 구현 변경이 들어간 흔적은 없습니다.
- current dirty tree 기준으로 이번 slice는 사실상 test-only parity 확장으로 읽는 것이 맞습니다.
  - `app/serializers.py`와 `app/web.py`에는 현재 추가 diff가 없었습니다.
  - `storage/sqlite_store.py`에는 earlier sqlite parity hunk가 남아 있지만, 이번 `/work`가 설명한 historical-save replay parity를 위해 새로 바뀐 구현은 아니었습니다.
- focused rerun 결과도 최신 `/work`와 일치했습니다.
  - SQLite historical-save parity 두 테스트와 선행 prerequisite인 sqlite superseded-reject replay 테스트가 모두 통과했습니다.
  - `python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py`는 통과했고, `git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`도 출력 없이 끝났습니다.
- 따라서 최신 `/work`는 truthful합니다.
  - SQLite 백엔드에서 `historical_save_identity_signal`의 latest same-anchor `write_note` replay와 `approval_granted`-only exclusion까지 직접 검증됐습니다.
  - 이로써 serializer/task-log replay adjunct family인 `superseded_reject_signal` 2건 + `historical_save_identity_signal` 2건은 SQLite parity 기준으로 닫혔습니다.

## 검증
- `git status --short`
  - 결과: rolling `.pipeline` runtime 파일, same-day `/work`/`/verify` 노트, earlier sqlite/helper/controller hunks가 섞인 dirty tree 상태였습니다.
- `git diff -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 현재 diff에는 earlier `storage/sqlite_store.py` hunk와 누적된 `tests/test_web_app.py` sqlite 회귀가 함께 있었지만, historical-save parity와 직접 관련된 새 hunk는 `tests/test_web_app.py`에만 추가된 것을 확인했습니다. `app/serializers.py`, `app/web.py`의 새 diff는 없었습니다.
- `rg -n "test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend|test_historical_save_identity_signal_requires_same_anchor_write_note_not_approval_granted_only_with_sqlite_backend|_build_historical_save_identity_signal_index|_resolve_historical_save_identity_signal_for_message" tests/test_web_app.py app/serializers.py`
  - 결과: 최신 `/work`가 근거로 든 sqlite historical-save 테스트 위치와 기존 serializer helper 위치를 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_requires_same_anchor_write_note_not_approval_granted_only_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 출력 없음
- `python3 -m unittest -v` 전체, Playwright/browser smoke, SQLite-backed source-message signal/candidate boundary parity 테스트는 미실행
  - 이유: 최신 `/work`는 browser-visible contract를 바꾸지 않았고, 이번 검증의 목적은 historical-save replay parity 주장 재확인에 필요한 focused rerun으로 충분했습니다.

## 남은 리스크
- serializer/task-log replay adjunct family 자체는 SQLite parity 기준으로 닫혔지만, grounded-brief source-message signal/candidate boundary contracts에는 아직 SQLite-backed peer가 비어 있습니다.
- 특히 아래 JSON-side 경계 테스트들은 현재 SQLite peer가 없습니다.
  - `test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes`
  - `test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals`
  - `test_session_local_candidate_uses_current_save_signal_only_for_support`
  - `test_session_local_candidate_omits_same_text_pair_even_if_corrected_outcome_exists`
  - `test_session_local_candidate_omits_accepted_as_is_only_save_path`
- 따라서 다음 exact slice는 또 하나의 단건 parity보다, 위 다섯 계약을 한 번에 닫는 bounded bundle인 `sqlite-session-local-signal-candidate-boundary-parity`가 맞습니다.
- browser-level sqlite smoke, reviewed-memory/review-queue parity, broader SQLite cleanup는 모두 그 다음 범위입니다.
