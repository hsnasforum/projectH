# 2026-04-18 active_round 선택에 live verify / receipt-close 우선

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `superpowers:using-superpowers`: 구현 lane 진입 전에 skill 경계와 handoff 규약을 그대로 따르기 위해 사용했습니다.

## 변경 이유
- 같은 날 shared-file owner boundary 라운드(`work/4/18/2026-04-18-state-dir-shared-files-owner-boundary.md` + matching `/verify`)가 `STATE_DIR_SHARED_FILES`로 autonomy/turn pseudo-entry를 job iteration에서 제거해 주었습니다.
- 그 다음 same-family current-risk는 `pipeline_runtime/supervisor.py::_build_active_round()`가 real job 사이에서 `updated_at`/`last_activity_at` 중심으로 한 줄 정렬만 하고 있다는 점이었습니다. 그래서 실제로는 older인 `VERIFY_PENDING`/`VERIFY_RUNNING` 또는 receipt close 대기 중인 `VERIFY_DONE` round가 있어도, 다른 이유로 timestamp가 더 큰 stale 실제 job(예: CLOSED round, 다른 이유로 touch된 job)이 `active_round` surface에서 이길 수 있었습니다.
- thin-client 입장에서는 이 stale 선택이 lane/turn/round surface에 바로 드러나서, launcher/controller가 current live verify 또는 receipt-close 진행을 놓친 것처럼 보이게 만드는 drift였습니다.

## 핵심 변경
- `_build_active_round(...)`의 정렬 키를 단순 timestamp tuple에서 liveness bucket 우선 + timestamp tie-break으로 바꿨습니다.
  - bucket 2: `status in {"VERIFY_PENDING", "VERIFY_RUNNING"}` — 실제 live verify round.
  - bucket 1: `status == "VERIFY_DONE"`이면서 `last_receipt`의 `(job_id, round)`와 아직 매칭되지 않은 receipt-close 대기 round.
  - bucket 0: 그 외(CLOSED VERIFY_DONE, `NEW_ARTIFACT`, `STABILIZING`, 미지 상태 등).
  - 같은 bucket 안에서는 기존처럼 `updated_at -> last_activity_at -> job_id` 순으로 tie-break 합니다. 그래서 VERIFY_RUNNING vs VERIFY_PENDING 같은 기존 두-live-job 비교는 영향을 받지 않고, 오직 live/receipt-pending vs CLOSED/기타 stale 비교에서만 우선순위가 달라집니다.
- 이 ranking은 이후의 기존 분기(turn-based verify suppression, duplicate-control handling, stale-operator gating, `degraded_reason` 필터링 등)가 읽는 `active_round` 구조를 바꾸지 않아서, 같은 caller들이 그대로 `state`/`completion_stage`/`note`를 사용할 수 있도록 남겨 뒀습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 두 개의 focused regression을 추가했습니다.
  - `test_build_active_round_prefers_live_verify_over_stale_real_job`: 같은 state_dir에 `VERIFY_DONE` CLOSED(higher `updated_at`)과 `VERIFY_PENDING` live(lower `updated_at`)가 같이 있을 때 `_build_active_round`가 live verify job을 골라 `state="VERIFY_PENDING"`을 반환하는지 고정합니다.
  - `test_build_active_round_prefers_receipt_pending_over_stale_closed`: `VERIFY_DONE` CLOSED(매칭 receipt 있음, `updated_at=500`)과 `VERIFY_DONE` receipt-pending(매칭 receipt 없음, `updated_at=100`)가 섞여 있을 때 receipt-pending job을 골라 `state="RECEIPT_PENDING"`을 반환하는지 고정합니다.
- `.pipeline/README.md`는 그대로 두었습니다. 현재 문구(“`RECEIPT_PENDING` round가 남아 있어도 current turn이 더 이상 `CODEX_VERIFY`/`CODEX_FOLLOWUP`가 아니면 launcher/runtime이 이를 곧바로 active lane으로 올리지 않는다”, `STATE_DIR_SHARED_FILES` 소유권 조항 등)는 이번 변경으로 untruthful 해지지 않으며, 수정 범위를 좁히기 위해 doc sweep은 보류했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py tests/test_turn_arbitration.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_prefers_live_verify_over_stale_real_job tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_prefers_receipt_pending_over_stale_closed tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_skips_autonomy_state_pseudo_job`
  - 결과: `Ran 3 tests`, `OK` (새 회귀 2개 + 이전 autonomy pseudo-entry 회귀 1개 모두 통과)
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration`
  - 결과: `Ran 75 tests`, `FAILED (failures=6, errors=1)`
  - baseline(변경 전) 집합과 동일한 실패 family(`test_verify_done_without_receipt_stays_receipt_pending` ERROR + `test_manifest_mismatch_blocks_receipt_and_marks_degraded`, `test_write_status_marks_runtime_degraded_on_active_lane_auth_failure`, `test_auth_failure_breakage_blocks_restart`, `test_claude_post_accept_breakage_blocks_blind_replay`, `test_codex_breakage_stops_after_retry_budget`, `test_codex_pre_completion_breakage_restarts_within_retry_budget`)가 그대로 재현됐습니다. 이번 라운드 범위 밖의 degraded/restart/receipt 계약 실패 집합과 일치하므로 scope를 넓히지 않았습니다.
  - baseline 자체도 변경 직전에 동일 test들만 실패함을 확인했습니다(`git stash` 후 `Ran 65 tests`, `FAILED (failures=6, errors=1)`로 같은 이름 집합 재확인).
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py tests/test_turn_arbitration.py .pipeline/README.md`
  - 결과: 통과
- controller/browser smoke와 launcher live replay는 이번 라운드에 돌리지 않았습니다. 이유: 이번 변경은 `active_round` 선택 규칙과 그 thin-client surface에 한정되고, browser-visible 계약(selector, 시나리오 수, gate 의미)을 바꾸지 않았기 때문입니다.

## 남은 리스크
- liveness ranking은 `VERIFY_PENDING`/`VERIFY_RUNNING` 와 receipt-close 대기만 상위 bucket으로 잡습니다. `NEW_ARTIFACT`/`STABILIZING` 같은 verify 이전 단계가 CLOSED round보다 timestamp가 뒤쳐져 있는 희귀 상황에서는 기존처럼 CLOSED round가 이길 수 있습니다. 현재는 실제 drift 증거가 없어서 이번 범위에 포함하지 않았습니다.
- 이번에 추가한 두 회귀는 `_build_active_round`를 직접 호출하는 unit scope 테스트입니다. 전체 status surface에서 같은 case를 재현하는 full `_write_status` 레벨 회귀는 기존 baseline의 6 failure + 1 error 계열이 먼저 닫힌 뒤에 겹쳐 두는 편이 맞습니다.
- live tmux runtime replay로 실제 stale `VERIFY_PENDING`/`VERIFY_DONE` 선택이 surface에 얼마나 자주 드러났는지는 다음 supervisor slice에서 다시 확인하는 편이 맞습니다. 이번 라운드는 pseudo-job 제거 이후 남은 ranking drift를 정리하는 것에만 집중했습니다.
