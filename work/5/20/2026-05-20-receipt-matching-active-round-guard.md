# 2026-05-20 receipt matching active round guard

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/archive/2026-05-20/implement_handoff.20260520-202150-fulfilled-by-receipt-fix.md`
- `.pipeline/archive/2026-05-20/implement_handoff.20260520-202150-fulfilled-by-receipt-fix.md.sha256`
- `work/5/20/2026-05-20-receipt-matching-active-round-guard.md`

## 사용 skill

- `finalize-lite`: 좁은 테스트, 문서 동기화 필요성, closeout 준비 상태를 점검하기 위해 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검사, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2034`가 실제로 실행되지 않은 이유를 확인하던 중, 이미 receipt가 있는 이전 `VERIFY_DONE` job이 `RECEIPT_PENDING`처럼 다시 떠오르는 경로를 확인했습니다.
- 기존 `_build_active_round()`는 전체 receipts 디렉터리에서 최신 receipt 하나만 matching receipt로 보았습니다.
- 같은 run에 여러 verify receipt가 있으면, 최신 receipt가 다른 job의 것일 때 더 오래된 closed job의 receipt 파일을 무시해 active round / automation health 표면을 왜곡할 수 있었습니다.

## 핵심 변경

- `RuntimeSupervisor._receipt_closes_job_round()`를 추가해 `last_receipt`뿐 아니라 해당 `job_id` / `round`의 receipt 파일을 직접 확인하도록 했습니다.
- `_build_active_round()`의 liveness ranking과 `VERIFY_DONE` 상태 판정이 같은 helper를 사용하도록 정리했습니다.
- 최신 receipt가 다른 job이어도 기존 job receipt 파일이 있으면 `CLOSED`로 판정하는 회귀 테스트를 추가했습니다.
- `#2034` handoff가 요구한 stale `OPERATOR_WAIT` + active `implement_handoff.md` + `VERIFY_PENDING` 조합 회귀 테스트를 추가해 active verify round가 유지되고 `operator_boundary` progress가 재노출되지 않음을 확인했습니다.
- 직접 충족한 `.pipeline/implement_handoff.md#2034`는 재실행을 막기 위해 archive 경로로 이동하고 sha256 sidecar를 남겼습니다.

## 검증

- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_uses_receipt_file_when_latest_receipt_is_other_job tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_prefers_receipt_pending_over_stale_closed tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_done_without_receipt_stays_receipt_pending tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_active_verify_round_when_stale_operator_turn_state_is_cleared tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_ignores_stale_operator_turn_state_when_non_operator_control_is_active tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_codex_task_hint_during_operator_wait`
  - 결과: PASS. 6개 테스트가 모두 통과했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `parse_control_slots(Path(".pipeline"))`
  - 결과: `{"active": None, "stale": []}`. 충족된 `#2034` control slot이 active로 남아 있지 않음을 확인했습니다.

## 남은 리스크

- Playwright/e2e, 전체 unittest, long soak, socket-bound smoke는 실행하지 않았습니다. 이번 변경은 supervisor active-round / status surface의 좁은 회귀 방지입니다.
- commit, push, PR, merge, release는 실행하지 않았습니다. 현재 범위는 local runtime 복구와 회귀 테스트입니다.
- `pipeline_runtime/supervisor.py`와 `tests/test_pipeline_runtime_supervisor.py`에는 이번 라운드 이전부터 있던 runtime/local-socket/task-hint 관련 dirty 변경이 함께 남아 있습니다. 이번 라운드는 receipt matching과 stale operator turn-state dispatcher shape만 좁게 다뤘습니다.
