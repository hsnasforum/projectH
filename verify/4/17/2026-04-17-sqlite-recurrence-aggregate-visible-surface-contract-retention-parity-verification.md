# 2026-04-17 sqlite recurrence aggregate visible surface contract retention parity verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/17/2026-04-17-sqlite-recurrence-aggregate-visible-surface-contract-retention-parity.md`는 reviewed-memory aggregate visible-surface / contract-retention의 남은 SQLite parity 여섯 건이 추가되었고, 그중 proof-record-store visibility 건만 pre-existing JSON-side seam 때문에 `expectedFailure`라고 설명합니다.
- 이번 verification 라운드는 그 설명이 현재 tree와 focused rerun 결과에 맞는지 다시 확인하고, 같은 family에서 다음 exact slice를 하나로 좁히는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `tests/test_web_app.py`에는 아래 여섯 SQLite peer가 실제로 존재합니다.
    - `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend`
    - `test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle_with_sqlite_backend`
    - `test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle_with_sqlite_backend`
    - `test_recurrence_aggregate_contract_refs_retained_through_lifecycle_with_sqlite_backend`
    - `test_recurrence_aggregate_source_family_refs_retained_through_lifecycle_with_sqlite_backend`
    - `test_recurrence_aggregate_local_effect_chain_retained_through_lifecycle_with_sqlite_backend`
- `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend`는 `/work` 설명대로 `@unittest.expectedFailure`가 붙어 있고, JSON-side 원본 `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked`도 현재 실제로 `IndexError`로 실패합니다.
  - 재실행 결과 원본 JSON 테스트는 `service._build_recurrence_aggregate_candidates(messages)[0]`에서 `IndexError: list index out of range`로 깨졌습니다.
  - 현재 코드상으로는 `app/serializers.py`의 `_build_recurrence_aggregate_candidates()`가 `current_candidate_index`를 `session_local_candidate`에서만 만들기 때문에, `candidate_recurrence_key`만 가진 synthetic message fixture에서는 aggregate가 비어 버리는 경로로 보입니다.
- 나머지 다섯 새 SQLite 테스트와 기존 prerequisite 둘은 모두 통과했습니다.
  - visible transition/result/active-effect lifecycle
  - boundary draft retention
  - contract ref retention
  - source-family ref retention
  - local-effect-chain retention
  - sqlite stop/reverse/conflict
  - sqlite reload continuity
- 현재 dirty tree 기준으로 이번 slice는 test-only parity 확장으로 읽는 것이 맞습니다.
  - `git diff --stat -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py` 결과 현재 관련 diff는 누적된 `tests/test_web_app.py`와 earlier `storage/sqlite_store.py` hunk에만 걸려 있었고, 이번 `/work` 설명대로 새 구현 diff는 없었습니다.
- docs truth도 현재 주장과 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 모두 reviewed-memory shipped boundary를 aggregate apply/result/active-effect, stop/reversal/conflict visibility까지 유지하고 있습니다.
  - 이번 round는 그 shipped lifecycle 위의 SQLite parity와 payload/internal separation truth를 확인하는 범위로 읽는 것이 맞습니다.
- 따라서 최신 `/work`는 truthful합니다.
  - visible-surface / contract-retention SQLite peer 여섯 건이 실제로 추가되어 있습니다.
  - 그중 한 건이 아직 green이 아닌 이유도 sqlite divergence가 아니라 shared JSON-side builder seam이라는 설명과 일치합니다.

## 검증
- `git status --short`
  - 결과: rolling `.pipeline` runtime 파일, same-day `/work` / `/verify` 노트, earlier sqlite/helper/controller hunks가 섞인 dirty tree였습니다.
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,240p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
  - 결과: reviewed-memory의 shipped browser boundary와 현재 phase framing이 최신 `/work` 설명과 충돌하지 않음을 확인했습니다.
- `git diff --stat -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 현재 diff는 `tests/test_web_app.py`와 earlier `storage/sqlite_store.py` hunk에만 걸려 있었고, 이번 `/work`는 test-only parity 확장으로 읽는 것이 맞았습니다.
- `rg -n "test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend|test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle_with_sqlite_backend|test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle_with_sqlite_backend|test_recurrence_aggregate_contract_refs_retained_through_lifecycle_with_sqlite_backend|test_recurrence_aggregate_source_family_refs_retained_through_lifecycle_with_sqlite_backend|test_recurrence_aggregate_local_effect_chain_retained_through_lifecycle_with_sqlite_backend|test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked\\(" tests/test_web_app.py`
  - 결과: JSON 원본 6건과 SQLite peer 6건의 위치를 모두 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked`
  - 결과: `ERROR`
  - 핵심 오류: `IndexError: list index out of range`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend`
  - 결과: `OK (expected failures=1)`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_contract_refs_retained_through_lifecycle_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_source_family_refs_retained_through_lifecycle_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_local_effect_chain_retained_through_lifecycle_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_stop_reverse_conflict_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reload_continuity_with_sqlite_backend`
  - 결과: `Ran 7 tests` / `OK`
- `python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 출력 없음
- `python3 -m unittest -v` 전체, Playwright/browser smoke는 미실행
  - 이유: 이번 `/work`는 browser-visible contract를 바꾸지 않았고, verification 목적은 visible-surface / contract-retention parity와 pre-existing shared seam 사실 여부를 좁게 재확인하는 것으로 충분했습니다.

## 남은 리스크
- visible-surface / contract-retention의 SQLite parity 공백 자체는 사실상 닫혔습니다. 지금 남은 same-family current-risk는 sqlite 누락이 아니라 shared aggregate builder의 synthetic-message-path regression입니다.
- 현재 failing contract는 `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked` 한 건이며, sqlite peer도 동일 경로를 따라 `expectedFailure`로만 묶여 있습니다.
- 따라서 다음 exact slice는 또 다른 parity 추가가 아니라, `app/serializers.py`의 `_build_recurrence_aggregate_candidates()`가 `candidate_recurrence_key`만 가진 synthetic message fixture에서도 truthful하게 aggregate를 형성하도록 shared builder seam을 고쳐 JSON/SQLite proof-store visibility 테스트를 둘 다 green으로 만드는 것이 맞습니다.
- 그 변경에서도 stale candidate retirement, record-backed lifecycle survival, proof/local-effect helper의 internal-only payload boundary는 그대로 유지되어야 합니다.
- browser-level sqlite smoke는 이번 slice 밖입니다.
