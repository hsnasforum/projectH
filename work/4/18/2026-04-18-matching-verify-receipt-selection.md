# 2026-04-18 matching verify receipt selection

## 변경 파일
- `pipeline_runtime/schema.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`

## 사용 skill
- `work-log-closeout`: `/work` closeout 형식과 필수 사실 항목을 repo 규칙에 맞춰 정리하기 위해 사용했습니다.
- `release-check`: 마무리 단계에서 실제 실행한 검증, 문서 동기화 범위, 남은 리스크를 과장 없이 점검하기 위해 사용했습니다.

## 변경 이유
- current runtime receipt를 확인해 보니 `2026-04-18-active-round-live-verify-preference` job의 receipt가 실제 same-day `/verify`가 아니라 `verify/4/9/...` note를 가리키고 있었습니다.
- 원인은 watcher와 supervisor가 verify note를 고르는 규칙을 다르게 들고 있었기 때문입니다. watcher 쪽은 latest work 기준 same-day verify를 어느 정도 좁혀 봤지만, supervisor receipt write와 `artifacts.latest_verify`는 여전히 global latest `/verify`를 집어 현재 round truth를 drift시킬 수 있었습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`에 `latest_verify_note_for_work(...)`, `same_day_verify_dir_for_work(...)`, `normalize_repo_artifact_path(...)`를 추가해 "work에 매칭되는 canonical verify note" 해석을 shared helper로 올렸습니다.
- shared helper는 우선 `work/...md` 참조가 명시된 verify note를 고르고, 참조가 전혀 없는 same-day verify note가 하나만 있을 때만 backward-compat fallback을 허용하며, 다른 work를 가리키는 note나 여러 unrelated verify note 사이에서는 fail-safe로 `None`을 돌리도록 좁혔습니다.
- `watcher_core.py`의 `_get_latest_same_day_verify_path_for_work()`와 same-day verify dir 계산이 이 shared helper를 쓰도록 맞췄습니다.
- `pipeline_runtime/supervisor.py`의 receipt reconcile과 `artifacts.latest_verify`가 더 이상 global latest `/verify`를 쓰지 않고 current work/job과 매칭되는 verify note만 쓰도록 바꿨습니다. 매칭 verify가 없으면 unrelated note로 receipt를 쓰지 않고 `receipt_verify_missing:<job_id>`로 fail-safe 경로를 탑니다.
- `tests/test_pipeline_runtime_schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `tests/test_watcher_core.py`에 explicit reference 우선, single-note fallback, unrelated verify fail-safe, receipt artifact selection 회귀를 추가했습니다.
- `.pipeline/README.md`에 watcher뿐 아니라 supervisor receipt close와 `artifacts.latest_verify`도 matching `/verify` 기준으로만 current truth를 읽어야 한다는 계약을 명시했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema`
  - 결과: `Ran 17 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.LatestVerifyNoteForWorkTest tests.test_watcher_core.WorkNoteFilteringTest.test_latest_unverified_broad_work_ignores_newer_unrelated_verify tests.test_watcher_core.WorkNoteFilteringTest.test_same_day_verify_lookup_accepts_direct_day_dir_note tests.test_watcher_core.WorkNoteFilteringTest.test_same_day_verify_lookup_rejects_multiple_unrelated_verifies tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 10 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 112 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 71 tests`, `FAILED (failures=6)`
  - 남은 failure 이름: `test_auth_failure_breakage_blocks_restart`, `test_claude_post_accept_breakage_blocks_blind_replay`, `test_codex_breakage_stops_after_retry_budget`, `test_codex_pre_completion_breakage_restarts_within_retry_budget`, `test_manifest_mismatch_blocks_receipt_and_marks_degraded`, `test_write_status_marks_runtime_degraded_on_active_lane_auth_failure`
  - 이번 변경으로 새로 생긴 failure는 확인되지 않았고, 이전 same-family supervisor baseline failure 집합이 그대로 남아 있습니다.
- `git diff --check -- pipeline_runtime/schema.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과

## 남은 리스크
- 현재 이미 써져 있는 historical receipt/status generated artifact 자체를 이번 라운드에서 backfill하지는 않았습니다. 다음 supervisor status/receipt write부터는 corrected matching rule을 따르지만, 과거 잘못 써진 `.pipeline/runs/.../receipts/*.json`는 자동 교정하지 않습니다.
- backward-compat를 위해 "same-day verify note가 정확히 1개이고 work 참조가 비어 있을 때"는 아직 fallback을 허용합니다. verify note가 항상 `work/...md` 참조를 적도록 repo 습관이 완전히 굳으면 이 fallback도 제거하는 편이 더 안전합니다.
- supervisor 전체 스위트의 기존 6 failure family는 이번 라운드 범위 밖이라 그대로 남아 있습니다. auth/breakage/degraded restart 쪽과 receipt manifest mismatch family는 별도 current-risk slice로 닫아야 합니다.
