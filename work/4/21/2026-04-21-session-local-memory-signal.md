# 2026-04-21 session-local memory signal

## 변경 파일
- `core/contracts.py`
- `storage/session_store.py`
- `app/serializers.py`
- `app/static/app.js`
- `tests/test_web_app.py`
- `tests/test_smoke.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `work/4/21/2026-04-21-session-local-memory-signal.md`

## 사용 skill
- `security-gate`: 저장된 세션 payload에 read-only projection만 추가되고, 승인/쓰기/overwrite 경계가 바뀌지 않는지 확인했습니다.
- `doc-sync`: `session_local_memory_signal`의 실제 shape와 노출 조건을 제품/아키텍처/수용기준/backlog 문서에 맞췄습니다.
- `release-check`: 실행한 검증과 미실행/환경 실패 범위를 분리했습니다.
- `finalize-lite`: 구현 종료 전 focused verification, 문서 동기화, `/work` closeout 준비 상태를 점검했습니다.
- `work-log-closeout`: 변경 파일, 검증 결과, 남은 리스크를 이 persistent `/work` 기록으로 남겼습니다.

## 변경 이유
- seq 727 handoff는 grounded-brief source message에 첫 read-only `session_local_memory_signal` projection을 현재 persisted session state에서만 계산하도록 요구했습니다.
- 기존 구현은 source message마다 기본 `content_signal`을 항상 노출했기 때문에, "관련 신호가 없으면 top-level field absent"인 handoff 계약과 맞지 않았습니다.
- 이번 변경은 새 store, 새 write endpoint, 새 approval surface 없이 기존 correction/content reason/approval reason/save linkage만 읽어 optional projection으로 노출합니다.

## 핵심 변경
- `SESSION_LOCAL_MEMORY_SIGNAL_VERSION = session_local_memory_signal_v1`을 공용 계약으로 추가하고, signal payload에 `signal_version`, `derived_at`, `artifact_id`, `source_message_id`를 고정했습니다.
- `storage/session_store.py`는 correction/content/approval/save 중 하나라도 있을 때만 `session_local_memory_signal`을 반환합니다. 아무 신호가 없는 grounded-brief source message에서는 serializer가 field를 생략합니다.
- corrected outcome이 현재 `corrected`일 때는 `correction_signal.corrected_outcome`과 `has_corrected_text`를 노출하고, `content_reason_record`는 별도 `content_signal`로만 노출합니다.
- completed save linkage는 `save_signal`에 유지하되 `latest_saved_at`을 추가해 `derived_at` 계산 근거로 씁니다. task-log replay나 cross-session merge는 추가하지 않았습니다.
- `session_local_candidate`와 UI signal ref label은 `session_local_memory_signal.correction_signal`을 primary basis로 사용하도록 조정했습니다.
- `superseded_reject_signal`과 `historical_save_identity_signal`은 현재 signal을 덮어쓰지 않고 기존 separate adjunct로 유지했습니다.

## 검증
- `python3 -m py_compile core/contracts.py storage/session_store.py app/serializers.py tests/test_web_app.py tests/test_smoke.py` → 통과
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes tests.test_web_app.WebAppServiceTest.test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals tests.test_web_app.WebAppServiceTest.test_session_local_candidate_omits_accepted_as_is_only_save_path tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal` → 5 tests OK
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_session_local_candidate_omits_accepted_as_is_only_save_path_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend` → 5 tests OK
- `python3 -m unittest tests.test_smoke.SmokeTest.test_session_local_memory_signal_keeps_latest_save_linkage_but_omits_stale_reject_note` → 1 test OK
- `python3 -m unittest tests.test_smoke.AgentLoopSmokeTest.test_session_local_memory_signal_keeps_latest_save_linkage_but_omits_stale_reject_note` → 실패, 테스트 클래스명 지정 착오(`AgentLoopSmokeTest` 없음)
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_summarize_file_returns_session_and_runtime tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_original_response_snapshot_for_legacy_grounded_brief` → 2 tests OK
- `python3 -m unittest tests.test_smoke.SmokeTest.test_candidate_recurrence_key_helper_uses_explicit_pair_only_and_keeps_fingerprint_stable tests.test_smoke.SmokeTest.test_recurrence_aggregate_candidates_helper_requires_exact_identity_and_distinct_anchors` → 2 tests OK
- `python3 -m unittest tests.test_web_app` → 314 tests 실행, 10 errors. 모두 `LocalOnlyHTTPServer(("127.0.0.1", 0), service)`에서 sandbox socket 생성이 막힌 `PermissionError: [Errno 1] Operation not permitted`였고, signal 관련 assertion 실패는 없었습니다.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes tests.test_web_app.WebAppServiceTest.test_source_message_session_local_memory_signal_separates_content_approval_and_save_axes_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals tests.test_web_app.WebAppServiceTest.test_session_local_candidate_requires_explicit_corrected_pair_and_stays_separate_from_signals_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal tests.test_web_app.WebAppServiceTest.test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_session_local_candidate_omits_accepted_as_is_only_save_path tests.test_web_app.WebAppServiceTest.test_session_local_candidate_omits_accepted_as_is_only_save_path_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_handle_chat_summarize_file_returns_session_and_runtime` → 11 tests OK
- `python3 -m unittest tests.test_smoke.SmokeTest.test_session_local_memory_signal_keeps_latest_save_linkage_but_omits_stale_reject_note tests.test_smoke.SmokeTest.test_candidate_recurrence_key_helper_uses_explicit_pair_only_and_keeps_fingerprint_stable tests.test_smoke.SmokeTest.test_recurrence_aggregate_candidates_helper_requires_exact_identity_and_distinct_anchors` → 3 tests OK
- `git diff --check -- core/contracts.py storage/session_store.py app/serializers.py app/static/app.js tests/test_web_app.py tests/test_smoke.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md work/4/21/2026-04-21-session-local-memory-signal.md` → 통과

## 남은 리스크
- 전체 `tests.test_web_app`는 sandbox의 socket 생성 제한 때문에 완전 통과를 확인하지 못했습니다. socket을 쓰지 않는 focused service/serializer 경로는 통과했습니다.
- Playwright는 실행하지 않았습니다. 이번 변경은 browser-visible 카드 레이아웃이 아니라 session payload와 candidate signal-ref label의 텍스트 매핑에 한정했습니다.
- 작업 전부터 `.pipeline/README.md`, pipeline runtime/watch 관련 파일, 이전 `/work` 및 `report/gemini` 파일이 dirty/untracked 상태였습니다. 이번 라운드는 해당 파일들을 되돌리거나 정리하지 않았습니다.
- commit, push, branch/PR publish, `.pipeline/gemini_request.md`, `.pipeline/operator_request.md` 작성은 수행하지 않았습니다.
