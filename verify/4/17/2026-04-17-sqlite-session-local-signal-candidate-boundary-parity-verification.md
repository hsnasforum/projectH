# 2026-04-17 sqlite session-local signal candidate boundary parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/17/2026-04-17-sqlite-session-local-signal-candidate-boundary-parity.md`는 SQLite 백엔드에서도 grounded-brief source-message의 `session_local_memory_signal` / `session_local_candidate` / `candidate_recurrence_key` boundary semantics 다섯 건이 JSON과 동일하게 유지된다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 focused rerun 결과에 맞는지 다시 확인하고, 같은 SQLite parity 흐름에서 다음 한 슬라이스를 exact하게 고정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `tests/test_web_app.py`에는 아래 다섯 SQLite peer가 추가되어 있습니다.
    - `test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes_with_sqlite_backend`
    - `test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals_with_sqlite_backend`
    - `test_session_local_candidate_uses_current_save_signal_only_for_support_with_sqlite_backend`
    - `test_session_local_candidate_omits_same_text_pair_even_if_corrected_outcome_exists_with_sqlite_backend`
    - `test_session_local_candidate_omits_accepted_as_is_only_save_path_with_sqlite_backend`
  - 각 테스트 본문도 `/work` 설명과 맞습니다.
    - `session_local_memory_signal`의 content / approval / save 축 분리 유지
    - explicit corrected pair가 있어야만 `session_local_candidate` / `candidate_recurrence_key` 생성
    - current `save_signal`은 supporting evidence일 뿐이며 `historical_save_identity_signal`은 candidate basis가 아님
    - same-text pair와 accepted-as-is-only save path에서는 candidate/key 미생성
- current dirty tree 기준으로 이번 slice는 사실상 test-only parity 확장으로 읽는 것이 맞습니다.
  - 이번 검증 범위에서 새로 확인된 관련 diff는 `tests/test_web_app.py`의 sqlite peer 추가입니다.
  - `app/serializers.py`와 `app/web.py`에는 이번 slice를 위해 새로 바뀐 구현 diff가 없었습니다.
  - `storage/sqlite_store.py`에는 earlier sqlite parity hunk가 남아 있지만, 이번 `/work`가 설명한 source-message boundary parity를 위해 새로 들어간 구현은 아니었습니다.
- focused rerun 결과도 최신 `/work`와 일치했습니다.
  - 위 다섯 SQLite boundary 테스트와 선행 prerequisite인 sqlite historical-save replay 테스트가 모두 통과했습니다.
  - `python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py`는 통과했고, `git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`도 출력 없이 끝났습니다.
- 따라서 최신 `/work`는 truthful합니다.
  - SQLite 백엔드에서 source-message signal/candidate boundary contracts 다섯 건이 직접 검증됐습니다.
  - 이로써 serializer/task-log replay adjunct 4건과 source-message boundary 5건을 합친 SQLite parity 묶음은 truthfully 닫혔습니다.

## 검증
- `git status --short`
  - 결과: rolling `.pipeline` runtime 파일, same-day `/work` / `/verify` 노트, earlier sqlite/helper/controller hunks가 섞인 dirty tree 상태였습니다.
- `git diff -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 현재 diff에는 earlier `storage/sqlite_store.py` hunk와 누적된 `tests/test_web_app.py` sqlite 회귀가 함께 있었지만, 이번 `/work`가 설명한 최신 boundary parity와 직접 대응되는 새 테스트는 `tests/test_web_app.py`에만 있음을 다시 확인했습니다.
- `rg -n "test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes_with_sqlite_backend|test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals_with_sqlite_backend|test_session_local_candidate_uses_current_save_signal_only_for_support_with_sqlite_backend|test_session_local_candidate_omits_same_text_pair_even_if_corrected_outcome_exists_with_sqlite_backend|test_session_local_candidate_omits_accepted_as_is_only_save_path_with_sqlite_backend|test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend" tests/test_web_app.py`
  - 결과: 최신 `/work`가 근거로 든 다섯 SQLite boundary 테스트와 sqlite historical-save prerequisite 위치를 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_local_candidate_uses_current_save_signal_only_for_support_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_local_candidate_omits_same_text_pair_even_if_corrected_outcome_exists_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_local_candidate_omits_accepted_as_is_only_save_path_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 출력 없음
- `python3 -m unittest -v` 전체, Playwright/browser smoke, reviewed-memory aggregate SQLite parity 번들은 미실행
  - 이유: 최신 `/work`는 browser-visible contract를 바꾸지 않았고, 이번 검증의 목적은 source-message boundary parity 주장 재확인에 필요한 focused rerun으로 충분했습니다.

## 남은 리스크
- source-message signal/candidate boundary family은 SQLite parity 기준으로 닫혔지만, 현재 shipped reviewed-memory aggregate surface의 formation/support boundary contracts에는 아직 JSON-only 테스트가 남아 있습니다.
- 특히 아래 JSON-side aggregate 계약들은 아직 SQLite peer가 없습니다.
  - `test_recurrence_aggregate_candidates_require_two_distinct_source_messages_and_ignore_same_anchor_replays`
  - `test_recurrence_aggregate_candidates_keep_candidate_review_as_support_only`
  - `test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs`
  - `test_recurrence_aggregate_candidates_do_not_materialize_from_save_support_or_historical_adjunct_only`
  - `test_recurrence_aggregate_precondition_blocked_stays_fixed_when_capability_unblocked`
- 기존 SQLite lifecycle 테스트(`emit/apply/confirm`, `stop/reverse/conflict`, `reload continuity`)는 이미 존재하므로, 다음 exact slice는 더 깊은 contract-retention micro-slice보다 위 다섯 formation/support boundary를 한 번에 닫는 bounded bundle인 `sqlite-recurrence-aggregate-formation-support-boundary-parity`가 맞습니다.
