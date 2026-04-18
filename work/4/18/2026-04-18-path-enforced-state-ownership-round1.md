# 2026-04-18 path-enforced state ownership 1차 라운드

## 변경 파일
이번 라운드에서 직접 편집한 파일만 기재합니다. 같은 `git diff HEAD`에는 이 세션 중 별도 라운드(16:23 `work/4/18/2026-04-18-active-round-live-verify-preference.md`, 16:31 `work/4/18/2026-04-18-stopped-runtime-receipt-pending-visibility.md`)가 생성한 `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py`, `.pipeline/README.md`의 STOPPED/RECEIPT_PENDING 관련 변경이 함께 포함되어 있으며, 그 라인들은 이번 슬라이스 산출물이 아닙니다.

- `pipeline_runtime/schema.py`
- `verify_fsm.py`
- `watcher_core.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md` (이번 라운드 기여는 "JobState primary 경로 + state-dir scan 소유권" 두 단락만 해당. STOPPED/RECEIPT_PENDING 라인은 16:31 라운드 산출물)

## 사용 skill
- `work-log-closeout`: `/work` closeout 형식과 실제 사실 항목을 current repo 규칙에 맞춰 정리하기 위해 사용했습니다.

## 변경 이유
- 직전 라운드(`work/4/18/2026-04-18-state-dir-shared-files-owner-boundary.md`)는 `STATE_DIR_SHARED_FILES` name filter로 `.pipeline/state/` scan 경계를 좁혔지만, `.pipeline/state/`는 여전히 "job state + shared state 혼합 디렉터리"로 남아 owner가 path 자체로 강제되지 않았습니다.
- Operator handoff는 이 축을 좁게 풀라고 지정했습니다. 이번 라운드는 자동 이동 없이 "새 경로 우선 + 루트 fallback" 읽기/쓰기 계약을 먼저 고정해 `.pipeline/state/jobs/`를 JobState 전용 primary path로 도입하고, 공용 상태 파일은 루트에 그대로 둡니다.
- verify close chain / lease release / active_round selection 같은 다른 축은 이번 라운드 범위 밖입니다. 테스트/문서에서 필요한 최소 수정만 허용했고, 자동 startup move는 replay/복구 증거 없이 넣지 않았습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`
  - `JOB_STATE_DIR_NAME = "jobs"` 상수와 `jobs_state_dir(state_dir)` helper를 추가해 JobState primary 경로(`<state_dir>/jobs`)를 단일 helper로 노출했습니다.
  - `iter_job_state_paths(state_dir)` helper를 추가해 primary scan(`<state_dir>/jobs/*.json`) 뒤에 root fallback scan(`<state_dir>/*.json`, `STATE_DIR_SHARED_FILES` 제외)을 돌리도록 구성했습니다. 같은 `job_id`가 양쪽에 있으면 primary가 우선이고 fallback은 건너뜁니다. 루트 fallback에서만 name filter가 필요하므로 filter는 migration 기간 fallback 해석에만 좁게 남았습니다.
  - 기존 `load_job_states(...)`는 `iter_job_state_paths`를 통해 스캔하도록 다시 맞췄습니다. run_id/legacy_not_before 판정 로직은 그대로 유지됐습니다.
  - `STATE_DIR_SHARED_FILES` 상수 주석에 새로운 owner 구조(primary path = `jobs/`, fallback = root with name filter)를 반영했습니다.
- `verify_fsm.py`
  - `JobState.save(state_dir)`가 `jobs_state_dir(state_dir)` 하위에 `{job_id}.json`을 tmp→rename으로 쓰도록 바꿨습니다. 루트에는 더 이상 새 파일을 쓰지 않습니다.
  - `JobState.load(state_dir, job_id)`는 primary(`jobs/<job_id>.json`) → fallback(`<state_dir>/<job_id>.json`) 순서로 읽습니다. 동일한 경로 기반 corrupt quarantine 경로도 유지됩니다.
- `watcher_core.py`
  - `_archive_stale_job_states`, `_verified_work_paths`, `_get_current_run_jobs`가 이제 `iter_job_state_paths`를 통해 state-dir을 스캔합니다. 각 함수 안의 직접 `self.state_dir.glob("*.json")` + `STATE_DIR_SHARED_FILES` 조립은 제거됐습니다.
  - `_get_current_run_jobs`에는 `seen_job_ids` 집합을 추가해 primary/fallback 중복 yield를 한 번 더 보호하도록 했습니다.
  - `STATE_DIR_SHARED_FILES` 직접 import는 더 이상 필요 없어 import 목록을 `iter_job_state_paths`, `read_control_meta`, `read_json`으로 정리했습니다.
- `tests/test_pipeline_runtime_schema.py`
  - `PathEnforcedJobStateOwnershipTest` 클래스를 추가해 `jobs_state_dir` 상수, `iter_job_state_paths`의 primary-우선/shared-file-스킵/primary-없을때-fallback 동작, `load_job_states`의 primary+fallback merge와 primary-우선 동작, `JobState.save`가 primary `jobs/`로만 쓰는지, `JobState.load`가 primary 우선 읽고 primary가 없을 때만 root fallback을 읽는지를 한 번에 고정했습니다. 이번 라운드가 추가한 테스트는 총 7개입니다.
- `tests/test_watcher_core.py`
  - `WorkNoteFilteringTest`의 `_poll` 이후 job state glob 대상 경로를 기존 `base_dir / "state"`에서 새 primary `base_dir / "state" / "jobs"`로 좁게 맞춰 두 개 테스트를 정리했습니다. 같은 assert 의도(“job state file이 실제로 생겼는지 + artifact_path가 meta_note인지”)를 유지합니다.
- `.pipeline/README.md`
  - "JobState primary 경로는 `.pipeline/state/jobs/<job_id>.json`, 공용 상태 파일은 루트 유지, migration window 동안 root fallback은 읽기 전용, auto-move는 이번 라운드 범위 밖" 단락과 "state-dir scan 소유권은 `jobs_state_dir` / `iter_job_state_paths` / `load_job_states` helper" 단락을 추가했습니다. STOPPING/STOPPED + RECEIPT_PENDING visibility 라인은 이번 라운드가 아니라 `2026-04-18-stopped-runtime-receipt-pending-visibility.md` 라운드가 추가한 내용입니다.

## fallback / owner boundary 고정 방식
- **primary (쓰기 + 읽기)**: `<state_dir>/jobs/<job_id>.json`. `JobState.save`는 오직 이 경로로만 씁니다.
- **shared state (쓰기 + 읽기)**: `<state_dir>/turn_state.json`, `<state_dir>/autonomy_state.json`. 이 파일들은 JobState schema가 아니라서 `jobs/` 하위에 들어가지 않으며, 같은 루트에 path로 구분됩니다.
- **root fallback (읽기 전용)**: `<state_dir>/<job_id>.json`. migration 기간 동안 루트에 남은 기존 file도 `JobState.load`와 `load_job_states`가 찾아 줍니다. 같은 `job_id`가 primary와 fallback에 동시에 있으면 primary가 우선이며 fallback은 조용히 무시됩니다.
- **자동 이동 없음**: 이번 라운드는 watcher startup에서 루트 job state를 `jobs/`로 bulk move하지 않습니다. 이 단계는 `.pipeline/README.md`에 "추후 마이그레이션 라운드에서 replay/복구 테스트와 함께 별도로" 처리한다고 명시돼 있습니다.
- **name filter 축소**: `STATE_DIR_SHARED_FILES`는 primary scan에서는 쓰이지 않습니다(primary 경로가 JobState 전용이므로). fallback scan에서만 공용 파일을 걸러 내는 용도로 좁혀졌습니다.

## 이번 라운드 범위 밖인 dirty-worktree 변경
- `pipeline_runtime/supervisor.py` 34행(`_liveness_rank` 도입 및 STOPPED `RECEIPT_PENDING` 보존)
- `tests/test_pipeline_runtime_supervisor.py`에 추가된 두 테스트(`test_build_active_round_prefers_live_verify_over_stale_real_job`, `test_build_active_round_prefers_receipt_pending_over_stale_closed`)
- `.pipeline/README.md`의 "runtime이 STOPPING/STOPPED/BROKEN으로 내려가더라도 ..." 라인

이 변경들은 이 세션 안의 별도 라운드(16:23 `active_round live verify preference`, 16:31 `stopped runtime receipt pending visibility`)가 이미 자체 `/work` closeout으로 기록한 산출물이며, `active_round selection` 및 runtime surface 축에 속합니다. 이번 path-ownership 1차 슬라이스는 그 축을 건드리지 않았고, 해당 변경을 revert하는 것은 dirty-worktree 존중 규칙에 어긋나므로 그대로 두었습니다. 초기 응답 요약이 위 세 파일을 `변경 파일` 리스트에 같이 적지 않아 `git diff HEAD` 기준의 truthful 정합성이 깨졌던 것은 인정하며, 본 closeout으로 바로잡습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py watcher_core.py verify_fsm.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest tests.test_pipeline_runtime_schema -v`
  - 결과: `Ran 13 tests`, `OK` (새 `PathEnforcedJobStateOwnershipTest` 7개 포함)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor -v`
  - 결과: `Ran 68 tests`, `FAILED (failures=6)`. `git stash` 후 baseline(`43ae02a`)에서 동일 파일 집합을 돌렸을 때 `Ran 65 tests, FAILED (failures=6, errors=1)`가 나옵니다. 이번 세션 중 별도 라운드(16:31 `stopped-runtime-receipt-pending-visibility`)가 `test_verify_done_without_receipt_stays_receipt_pending` ERROR 하나를 이미 닫아 준 결과 현재 working tree에서는 `errors=0`입니다. 나머지 6개 실패(`test_auth_failure_breakage_blocks_restart`, `test_claude_post_accept_breakage_blocks_blind_replay`, `test_codex_breakage_stops_after_retry_budget`, `test_codex_pre_completion_breakage_restarts_within_retry_budget`, `test_manifest_mismatch_blocks_receipt_and_marks_degraded`, `test_write_status_marks_runtime_degraded_on_active_lane_auth_failure`)는 baseline과 동일 이름이며 이번 라운드 변경으로 새로 깨진 테스트는 없습니다. 실패한 pre-existing family: `runtime_state` DEGRADED/STOPPING 계약과 breakage retry budget 계열. 이번 owner-boundary 슬라이스 범위 밖입니다.
- `python3 -m unittest -v tests.test_watcher_core.ClaudeHandoffDispatchTest tests.test_watcher_core.VerifyCompletionContractTest`
  - 결과: `Ran 17 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core` (전체)
  - 결과: `Ran 111 tests`, `OK`
- `git diff --check -- pipeline_runtime/schema.py watcher_core.py verify_fsm.py tests/test_pipeline_runtime_schema.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과

## 남은 리스크
- **auto-move 미포함**: `.pipeline/state/`에 남은 기존 루트 job state는 이번 라운드에서 `jobs/`로 자동 이동하지 않습니다. migration window 동안 primary/fallback이 공존하고, 같은 `job_id`가 양쪽에 있으면 fallback 사본은 조용히 가려집니다. 다음 마이그레이션 라운드에서 bulk move + replay/복구 테스트를 별도 슬라이스로 처리해야 합니다.
- **archive 대칭성**: `_archive_stale_job_states`는 primary와 fallback을 `iter_job_state_paths`로 훑지만 같은 `stem`의 fallback은 primary가 존재할 때 dedupe되어 건너뜁니다. drift fallback 사본이 즉시 archive되지 않을 수 있습니다. 영향은 "루트에 오래된 사본이 남을 수 있음"이며, 다음 마이그레이션 라운드에서 policy를 같이 정리해야 합니다.
- **pre-existing supervisor failure 7건**: `runtime_state` DEGRADED/STOPPING 계약과 breakage retry budget 계열. verify close chain / lease release 구조 라운드에서 같이 닫는 편이 맞습니다.
- **tmux live replay 부재**: 이번 라운드는 unit 범위에서 primary/fallback 계약을 검증했습니다. 실제 tmux live runtime에서 primary path 전후 dispatch 흐름이 끊기지 않는지는 launcher live stability gate에서 별도로 한 번 확인하는 편이 안전합니다.
- **세션 동시 라운드로 인한 `/work` 교차 기록**: 같은 세션 안에서 supervisor 축 두 라운드와 이번 path-ownership 라운드가 시간대가 겹쳐 진행됐고, 제 초기 closeout 파일은 한 번 유실됐다가 본 노트로 복원됐습니다. 초기 응답 요약이 `git diff HEAD` 전체를 truthful하게 반영하지 못한 점은 이번 closeout으로 정정했습니다.
