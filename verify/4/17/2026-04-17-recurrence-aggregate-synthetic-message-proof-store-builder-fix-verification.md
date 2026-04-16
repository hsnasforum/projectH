# 2026-04-17 recurrence aggregate synthetic message proof store builder fix verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/17/2026-04-17-recurrence-aggregate-synthetic-message-proof-store-builder-fix.md`는 shared `_build_recurrence_aggregate_candidates()` seam을 고쳐 synthetic message fixture에서도 aggregate가 형성되도록 했고, 이로써 JSON / SQLite proof-store visibility 테스트가 둘 다 green이 되었다고 주장합니다.
- 이번 verification 라운드는 그 shared fix가 현재 tree와 focused rerun 결과에 맞는지 다시 확인하고, 같은 family에서 다음 exact slice를 one-shot으로 고정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `app/serializers.py`의 `_build_recurrence_aggregate_candidates()`는 `session_local_candidate`가 있으면 기존처럼 `candidate_id` / `updated_at`를 우선 쓰고, 없을 때만 `candidate_recurrence_key.source_candidate_id` / `source_candidate_updated_at`를 fallback으로 읽도록 바뀌어 있습니다.
  - `tests/test_web_app.py`의 `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend`에는 더 이상 `@unittest.expectedFailure`가 없습니다.
- focused rerun 결과도 최신 `/work`와 일치했습니다.
  - `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked`는 이제 `OK`입니다.
  - `test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend`도 `OK`입니다.
  - stale-candidate retirement, visible transition/result/active-effect lifecycle, reload continuity를 지키는 representative sqlite tests도 모두 통과했습니다.
- 이 shared fallback은 현재 설명 범위 안에서만 넓어졌습니다.
  - `session_local_candidate`가 존재하면 기존 stale guard path를 그대로 우선 사용합니다.
  - synthetic fixture처럼 `candidate_recurrence_key`만 있는 경우에만 aggregate member를 stale로 오판하지 않도록 current index를 채워 줍니다.
- docs truth도 현재 구현과 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 모두 reviewed-memory shipped browser boundary와 SQLite opt-in seam을 유지하고 있으며, 이번 fix는 그 shipped aggregate family의 shared serializer seam 보정으로 읽는 것이 맞습니다.
- 따라서 최신 `/work`는 truthful합니다.
  - shared builder seam fix가 실제로 들어가 있습니다.
  - JSON / SQLite proof-store visibility 테스트는 둘 다 green이며, 이전 라운드에서 남아 있던 last non-green contract가 해소됐습니다.

## 검증
- `git status --short`
  - 결과: rolling `.pipeline` runtime 파일, same-day `/work` / `/verify` 노트, earlier sqlite/helper/controller hunks가 섞인 dirty tree였습니다.
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,240p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
  - 결과: current phase / shipped reviewed-memory boundary / sqlite opt-in framing이 최신 `/work` 설명과 충돌하지 않음을 확인했습니다.
- `git diff --stat -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 현재 관련 diff는 `app/serializers.py`, accumulated `tests/test_web_app.py`, earlier `storage/sqlite_store.py` hunk에 걸려 있었고, 최신 `/work`가 말한 shared builder fix가 `app/serializers.py`에 실제로 포함되어 있음을 확인했습니다.
- `nl -ba app/serializers.py | sed -n '3938,3962p'`
  - 결과: `session_local_candidate` 우선 후 `candidate_recurrence_key` fallback이 들어간 exact hunk를 확인했습니다.
- `nl -ba tests/test_web_app.py | sed -n '11088,11118p'`
  - 결과: sqlite proof-store visibility test에서 `@unittest.expectedFailure`가 제거된 현재 상태를 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_payload_keeps_proof_record_store_internal_and_ui_blocked_with_sqlite_backend`
  - 결과: `Ran 1 test` / `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidate_retires_on_superseding_correction_before_emit_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reload_continuity_with_sqlite_backend`
  - 결과: `Ran 3 tests` / `OK`
- `python3 -m py_compile app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 통과
- `git diff --check -- tests/test_web_app.py app/serializers.py storage/sqlite_store.py app/web.py`
  - 결과: 출력 없음
- 전체 `python3 -m unittest -v`, Playwright/browser smoke는 미실행
  - 이유: 이번 `/work`는 shared builder seam과 focused regression test를 다루는 round였고, browser-visible contract 자체를 새로 넓히지 않았으므로 `/work`가 주장한 범위 재확인에는 focused rerun으로 충분했습니다.

## 남은 리스크
- recurrence aggregate family의 service-level SQLite parity와 shared builder seam은 이번 round로 사실상 닫혔습니다.
- 남은 same-family current-risk는 opt-in SQLite backend를 실제 브라우저 shell에서 밟는 user-visible contract입니다. 현재 Playwright smoke는 JSON default path만 직접 부팅해 검증하고 있고, `storage_backend='sqlite'` opt-in browser path는 아직 same-family browser smoke로 닫히지 않았습니다.
- 따라서 다음 exact slice는 shared service parity를 더 쪼개는 것이 아니라, existing reviewed-memory browser smoke path를 재사용해 SQLite opt-in browser contract의 최소 coherent bundle을 직접 확인하는 것이 맞습니다.
