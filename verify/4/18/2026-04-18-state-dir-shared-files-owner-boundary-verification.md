# 2026-04-18 state-dir 공용 파일 owner boundary 검증

## 변경 파일
- `verify/4/18/2026-04-18-state-dir-shared-files-owner-boundary-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-state-dir-shared-files-owner-boundary.md`가 `STATE_DIR_SHARED_FILES` owner boundary와 watcher/supervisor state-dir scan 정합성을 고쳤다고 주장하므로, 현재 작업 트리와 focused regression에서 그 주장이 실제로 맞는지 다시 확인해야 했습니다.
- same-day 최신 `/verify`인 `verify/4/18/2026-04-18-watcher-verify-running-handoff-dispatch-guard-verification.md`는 이전 watcher round를 닫은 문서라서, 이 최신 `/work`를 참조하는 canonical verify truth를 별도로 남긴 뒤에만 다음 control slot을 열 수 있습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`에는 `STATE_DIR_SHARED_FILES`가 정의되어 있고, `load_job_states(...)`가 `turn_state.json`과 `autonomy_state.json`을 모두 건너뛰도록 바뀌어 있어 latest `/work`의 shared-file owner boundary 주장이 현재 트리와 일치함을 확인했습니다.
- `watcher_core.py`도 `_archive_stale_job_states`, `_verified_work_paths`, `_get_current_run_jobs`에서 같은 `STATE_DIR_SHARED_FILES`를 재사용하고 있어, watcher/supervisor가 `.pipeline/state/`를 서로 다른 local 규칙으로 해석하던 drift는 이번 범위에서 정리된 상태입니다.
- `tests/test_pipeline_runtime_schema.py`의 shared-file 회귀 3개와 `tests/test_pipeline_runtime_supervisor.py`의 `test_build_active_round_skips_autonomy_state_pseudo_job`는 재실행 시 모두 통과했습니다.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` 전체를 다시 돌린 결과는 `Ran 66 tests`, `FAILED (failures=6, errors=1)`로 나왔고, 이는 latest `/work`가 적어 둔 "unrelated supervisor baseline failure 6개 + error 1개가 여전히 남아 있다"는 단서와 일치했습니다.
- 따라서 이번 `/work`는 truthfully 닫혔고, 다음 same-family current-risk reduction은 shared-file pseudo-job 제거 이후에도 남아 있는 `pipeline_runtime/supervisor.py::_build_active_round()`의 real-job active_round selection 보정이라고 판단해 `.pipeline/claude_handoff.md`를 `CONTROL_SEQ: 295`로 갱신했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py watcher_core.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema`
  - 결과: `Ran 6 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_active_round_skips_autonomy_state_pseudo_job -v`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.ClaudeHandoffDispatchTest tests.test_watcher_core.VerifyCompletionContractTest`
  - 결과: `Ran 17 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 66 tests`, `FAILED (failures=6, errors=1)`
  - 확인된 예시: `test_verify_done_without_receipt_stays_receipt_pending`, `test_manifest_mismatch_blocks_receipt_and_marks_degraded`, `test_write_status_marks_runtime_degraded_on_active_lane_auth_failure` 등 기존 supervisor failure family가 그대로 남아 있습니다.
- `git diff --check -- pipeline_runtime/schema.py watcher_core.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- 이번 verify에서는 controller/browser smoke와 launcher live replay는 다시 실행하지 않았습니다.
  - 이유: latest `/work` 범위가 state-dir shared-file ownership과 watcher/supervisor regression에 한정되어 있었고, browser-visible 계약 변경은 없었기 때문입니다.

## 남은 리스크
- `pipeline_runtime/supervisor.py::_build_active_round()`는 여전히 real job 사이에서는 `updated_at`/`last_activity_at` 중심으로 current round를 고르기 때문에, shared-file pseudo-job이 사라진 뒤에도 stale `VERIFY_PENDING` 또는 older `VERIFY_DONE`가 thin-client `active_round` surface를 왜곡할 가능성이 남아 있습니다.
- supervisor 전체 스위트에는 `RECEIPT_PENDING` surface와 degraded/broken-lane recovery family의 기존 6 failure + 1 error가 남아 있습니다. 이번 라운드는 shared-file owner boundary만 닫았고 그 family까지는 넓히지 않았습니다.
- live tmux runtime replay나 launcher live stability gate는 이번 verify에 포함하지 않았으므로, 실제 세션에서 stale real-job selection이 얼마나 자주 surface되는지는 다음 supervisor slice에서 다시 확인해야 합니다.
