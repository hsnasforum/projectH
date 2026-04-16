# 2026-04-17 sqlite superseded reject signal parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/17/2026-04-17-sqlite-superseded-reject-signal-parity.md`는 SQLite 백엔드에서도 `superseded_reject_signal`의 두 JSON-side replay 계약이 그대로 성립한다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 focused rerun 결과에 맞는지 다시 확인하고, 같은 serializer/task-log replay family에서 다음 한 슬라이스를 고정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `tests/test_web_app.py`에는 `test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend`와 `test_superseded_reject_signal_omits_ambiguous_note_association_with_sqlite_backend`가 추가되어 있습니다.
  - 첫 번째 테스트는 SQLite 세션에서 reject → reason note → correction 이후에도 현재 `session_local_memory_signal.content_signal`은 `corrected`를 유지하고, 별도 `superseded_reject_signal`만 same-anchor reject outcome/note를 `task_log_audit` 기준으로 replay하는지 확인합니다.
  - 두 번째 테스트는 SQLite 세션에서 reject → correction 뒤 `approval_reject` scope의 ambiguous note를 직접 `task_log`에 삽입해도 `superseded_reject_signal`가 그 note를 붙이지 않고 원래 `content_reject` baseline만 유지하는지 확인합니다.
  - `app/serializers.py`의 `_build_superseded_reject_signal_index()`와 `_normalize_superseded_reject_reason_record()`는 이미 현재 tree에 존재했고, 이번 slice를 위해 추가 구현 변경이 들어간 흔적은 없습니다.
- current dirty tree 기준으로 이번 slice는 사실상 test-only parity 확장으로 읽는 것이 맞습니다.
  - `app/serializers.py`와 `app/web.py`에는 현재 추가 diff가 없었습니다.
  - `storage/sqlite_store.py`에는 earlier sqlite parity hunk가 남아 있지만, 이번 `/work`가 설명한 superseded-reject parity를 위해 새로 바뀐 구현은 아니었습니다.
- focused rerun 결과도 최신 `/work`와 일치했습니다.
  - SQLite superseded-reject parity 두 테스트와 선행 prerequisite인 sqlite reject-reason task-log row parity 테스트가 모두 통과했습니다.
  - `python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py`는 통과했고, `git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`도 출력 없이 끝났습니다.
- 따라서 최신 `/work`는 truthful합니다.
  - SQLite 백엔드에서 `superseded_reject_signal`의 latest same-anchor note replay와 ambiguous note omission까지 직접 검증됐습니다.
  - 다만 adjacent save-side replay helper인 `historical_save_identity_signal`은 아직 SQLite-backed peer가 없습니다.

## 검증
- `git status --short`
  - 결과: rolling `.pipeline` runtime 파일, same-day `/work`/`/verify` 노트, earlier sqlite/helper/controller hunks가 섞인 dirty tree 상태였습니다.
- `git diff -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 현재 diff에는 earlier `storage/sqlite_store.py` hunk와 누적된 `tests/test_web_app.py` sqlite 회귀가 함께 있었지만, superseded-reject parity와 직접 관련된 새 hunk는 `tests/test_web_app.py`에만 추가된 것을 확인했습니다. `app/serializers.py`, `app/web.py`의 새 diff는 없었습니다.
- `rg -n "test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend|test_superseded_reject_signal_omits_ambiguous_note_association_with_sqlite_backend|test_historical_save_identity_signal_replays_latest_same_anchor_write_note_without_overwriting_current_save_signal|test_historical_save_identity_signal_requires_same_anchor_write_note_not_approval_granted_only|_build_superseded_reject_signal_index|_normalize_superseded_reject_reason_record|historical_save_identity_signal" tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 최신 `/work`가 근거로 든 sqlite superseded-reject 테스트 위치, 기존 serializer helper 위치, 그리고 아직 sqlite peer가 없는 JSON-side `historical_save_identity_signal` 테스트 위치를 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_replays_latest_same_anchor_reject_note_without_overwriting_current_signal_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_superseded_reject_signal_omits_ambiguous_note_association_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_content_reason_note_updates_existing_reject_record_and_logs_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 출력 없음
- `python3 -m unittest -v` 전체, Playwright/browser smoke, SQLite-backed `historical_save_identity_signal` parity 테스트는 미실행
  - 이유: 최신 `/work`는 browser-visible contract를 바꾸지 않았고, 이번 검증의 목적은 superseded-reject parity 주장 재확인에 필요한 focused rerun으로 충분했습니다.

## 남은 리스크
- 현재 tree에는 JSON-backed `historical_save_identity_signal` 회귀 두 건만 있고 SQLite-backed peer가 없습니다. 따라서 같은 serializer/task-log replay family에서 남은 가장 작은 current-risk reduction은 save-side replay helper가 SQLite에서도 같은 same-anchor write-note semantics를 유지하는지 직접 고정하는 것입니다.
- 다음 exact slice는 `sqlite-historical-save-identity-signal-parity`가 맞습니다.
  - replay contract 1: latest same-anchor `write_note`를 replay하되 현재 `save_signal`을 덮어쓰지 않음
  - replay contract 2: matching persisted `write_note` 없이 `approval_granted`만 있으면 emit하지 않음
- browser-level sqlite smoke와 broader replay/helper refactor는 모두 그 다음 범위입니다.
