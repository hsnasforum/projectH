STATUS: verified
WORK: work/5/20/2026-05-20-receipt-matching-active-round-guard.md
CONTROL_SEQ: 2034

# 검증 기록

## 요약

`#2034`가 실행되지 않은 직접 원인은 active round 표면이 이미 닫힌 verify job을 `RECEIPT_PENDING`처럼 다시 선택할 수 있는 receipt matching 버그였습니다.
이번 변경은 job별 receipt 파일을 확인하도록 고쳐, 최신 receipt가 다른 job이어도 이미 닫힌 job을 pending으로 되살리지 않도록 했습니다.

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/archive/2026-05-20/implement_handoff.20260520-202150-fulfilled-by-receipt-fix.md`
- `.pipeline/archive/2026-05-20/implement_handoff.20260520-202150-fulfilled-by-receipt-fix.md.sha256`
- `work/5/20/2026-05-20-receipt-matching-active-round-guard.md`
- `verify/5/20/2026-05-20-receipt-matching-active-round-guard.md`

## 확인한 대상

- `pipeline_runtime/supervisor.py`
  - `_build_active_round()`가 matching receipt 판정에 최신 receipt 하나만 쓰지 않고, 대상 `job_id` / `round` receipt 파일까지 확인하는지 확인했습니다.
  - `VERIFY_DONE` liveness ranking과 최종 `CLOSED` / `RECEIPT_PENDING` 판정이 같은 receipt helper를 사용하는지 확인했습니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - 최신 receipt가 다른 job이어도 기존 receipt 파일이 있으면 closed job을 `CLOSED`로 남기는 회귀 테스트를 확인했습니다.
  - stale `OPERATOR_WAIT` turn-state가 active `implement_handoff.md`와 active `VERIFY_PENDING` round를 가리지 않는 `#2034` dispatcher-shape 회귀 테스트를 확인했습니다.
- `.pipeline`
  - 직접 충족한 `.pipeline/implement_handoff.md#2034`를 archive로 이동했고, active/stale control slot이 비어 있음을 확인했습니다.

## 실행한 검증

- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_uses_receipt_file_when_latest_receipt_is_other_job tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_prefers_receipt_pending_over_stale_closed tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_done_without_receipt_stays_receipt_pending tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_active_verify_round_when_stale_operator_turn_state_is_cleared tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_ignores_stale_operator_turn_state_when_non_operator_control_is_active tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_codex_task_hint_during_operator_wait`
  - 결과: PASS. 6개 테스트가 모두 통과했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `python3 -m pipeline_runtime.cli status . --json`
  - 수정 전 확인 결과: runtime은 `STOPPED`, `active_round`는 `null`이었지만 compat control slot에는 `.pipeline/implement_handoff.md#2034`가 남아 있었습니다.
- `parse_control_slots(Path(".pipeline"))`
  - archive 후 결과: active 없음, stale 없음.

## 실행하지 않은 검증

- Playwright/e2e, 전체 unittest, long soak, socket-bound smoke
  - 이유: 이번 변경은 browser-visible behavior가 아니라 supervisor receipt matching과 status surface 회귀 방지입니다.
- commit, push, PR, merge, release
  - 이유: publication boundary이며 이번 사용자 요청 범위 밖입니다.

## 판정

- 사용자가 지적한 “실행 안 됨” 상태는 사실이었습니다. `#2034` handoff가 active로 남았지만 실제 구현 라운드가 시작되지 않았고, 이전 closed verify job의 receipt 판정이 active round 표면을 왜곡했습니다.
- 이번 변경 후 receipt가 있는 이전 job은 최신 receipt가 아니어도 `CLOSED`로 판정됩니다.
- `#2034`가 요구한 dispatcher-shaped 회귀 테스트도 추가되어, stale operator turn-state 정리 후에도 active verify round / recovering surface가 유지됩니다.

## 남은 리스크

- 이번 검증은 좁은 supervisor 단위 검증입니다. 전체 runtime soak는 실행하지 않았습니다.
- 워크트리에는 이전 라운드에서 누적된 다른 dirty 변경이 남아 있어, 넓은 release 판단은 별도 통합 검증이 필요합니다.
