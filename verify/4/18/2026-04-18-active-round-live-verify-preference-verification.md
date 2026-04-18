# 2026-04-18 active_round live verify / receipt-close 우선 검증

## 변경 파일
- `verify/4/18/2026-04-18-active-round-live-verify-preference-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-active-round-live-verify-preference.md`가 `pipeline_runtime/supervisor.py::_build_active_round()`의 stale real-job timestamp drift를 liveness bucket 우선순위로 줄였다고 주장하므로, 현재 트리와 최소 회귀 재실행으로 그 주장이 실제로 맞는지 다시 확인해야 했습니다.
- 직전 same-family `/verify`는 `verify/4/18/2026-04-18-state-dir-shared-files-owner-boundary-verification.md`였고, latest `/work`를 직접 참조하는 canonical verify note가 아직 없었으므로 새 `/verify`를 먼저 남긴 뒤에만 next control slot을 열 수 있었습니다.

## 핵심 변경
- 현재 `pipeline_runtime/supervisor.py`의 `_build_active_round(...)`는 단순 `updated_at` / `last_activity_at` 정렬 대신 liveness bucket을 먼저 봅니다. `VERIFY_PENDING` / `VERIFY_RUNNING`은 최상위, receipt가 아직 닫히지 않은 `VERIFY_DONE`은 그다음, CLOSED/기타 stale real job은 마지막으로 밀려 latest `/work`의 핵심 구현 주장이 현재 코드와 일치함을 확인했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에는 latest `/work`가 설명한 회귀 2개(`test_build_active_round_prefers_live_verify_over_stale_real_job`, `test_build_active_round_prefers_receipt_pending_over_stale_closed`)와 prior shared-file 회귀(`test_build_active_round_skips_autonomy_state_pseudo_job`)가 실제로 들어 있고, 재실행 시 모두 통과했습니다.
- full regression을 다시 돌리면 `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration`는 여전히 `Ran 75 tests`, `FAILED (failures=6, errors=1)`입니다. 이번 verify에서도 남은 실패 이름 집합은 `/work`가 적은 것과 같았습니다.
- 다만 `/work`에 적힌 "baseline 자체도 `git stash` 후 같은 실패 집합을 확인했다"는 보조 문장은 이번 verify에서 다시 실행하지 않았습니다. 현재 작업 트리가 넓게 dirty한 상태라 unrelated 변경을 stash하는 것은 이 verify 라운드의 안전한 범위를 넘기기 때문입니다. 따라서 이번 `/verify`는 current-tree truth만 independently 확인하고, 그 stash 기반 비교 문장은 미재검증 보조 맥락으로만 남깁니다.
- 다음 same-family current-risk reduction은 `_write_status()`가 runtime이 `STOPPED`가 되면 `RECEIPT_PENDING` active_round까지 같이 지워 `test_verify_done_without_receipt_stays_receipt_pending`를 깨뜨리는 문제라고 판단해 `.pipeline/claude_handoff.md`를 `CONTROL_SEQ: 296`으로 갱신했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py tests/test_turn_arbitration.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_prefers_live_verify_over_stale_real_job tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_prefers_receipt_pending_over_stale_closed tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_skips_autonomy_state_pseudo_job`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration`
  - 결과: `Ran 75 tests`, `FAILED (failures=6, errors=1)`
  - 확인된 실패/에러: `test_verify_done_without_receipt_stays_receipt_pending`, `test_manifest_mismatch_blocks_receipt_and_marks_degraded`, `test_write_status_marks_runtime_degraded_on_active_lane_auth_failure`, `test_auth_failure_breakage_blocks_restart`, `test_claude_post_accept_breakage_blocks_blind_replay`, `test_codex_breakage_stops_after_retry_budget`, `test_codex_pre_completion_breakage_restarts_within_retry_budget`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py tests/test_turn_arbitration.py .pipeline/README.md`
  - 결과: 통과
- 이번 verify에서는 controller/browser smoke, launcher live replay, 그리고 `/work`가 언급한 `git stash` baseline 비교는 다시 실행하지 않았습니다.
  - 이유: 이번 변경 범위는 supervisor active_round selection과 status surface에 한정되며, dirty worktree에서 stash를 건드리는 것은 unrelated 변경을 잠시라도 치우는 작업이라 verify 범위를 넘기기 때문입니다.

## 남은 리스크
- `_build_active_round(...)` ranking drift는 줄었지만, `_write_status()`는 runtime이 `STOPPED`/`BROKEN`일 때 `surfaced_active_round = None`로 일괄 정리하고 있어 receipt-close 대기 중인 `RECEIPT_PENDING` current truth까지 같이 사라집니다. full suite의 `test_verify_done_without_receipt_stays_receipt_pending` error가 바로 이 지점을 계속 가리킵니다.
- degraded/restart family의 기존 6 failure + 1 error는 이번 round에서도 그대로 남아 있습니다. 이들은 lane recovery / runtime_state 분기 family라서, active_round ranking slice와는 분리해 다루는 편이 맞습니다.
- `.pipeline/README.md`는 현재도 `Receipt: pending close` surface를 launcher thin-client truth로 적고 있지만, runtime `STOPPED`일 때 어떤 필드만 유지하고 어떤 필드를 비우는지까지는 완전히 명시하지 않습니다. 다음 receipt-close slice에서 코드와 문구를 더 정확히 맞출 필요가 있습니다.
