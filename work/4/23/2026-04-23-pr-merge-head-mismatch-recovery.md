# 2026-04-23 PR merge HEAD mismatch recovery

## 변경 파일
- `pipeline_runtime/pr_merge_state.py`
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `pipeline_gui/home_presenter.py`
- `pipeline_gui/app.py`
- `tests/test_pr_merge_state.py`
- `tests/test_operator_request_schema.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `.pipeline/README.md`
- `README.md`
- `docs/MILESTONES.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/23/2026-04-23-pr-merge-head-mismatch-recovery.md`

## 사용 skill
- `github`: PR #27 merge 상태와 현재 branch/PR 관계 확인에 사용.
- `security-gate`: `needs_operator`, PR merge gate, runtime control surface 변경이 operator boundary를 숨기지 않는지 점검.
- `doc-sync`: runtime 계약 변경을 README, `.pipeline/README.md`, milestone/runtime docs에 동기화.
- `finalize-lite`: 구현 라운드 종료 전에 focused verification, doc-sync, closeout 범위를 정리.
- `release-check`: 변경 범위에 맞는 좁은 검증과 남은 리스크 확인.
- `work-log-closeout`: 최신 `/work` 노트를 읽고 이번 라운드의 실행 사실을 한국어 closeout으로 기록.

## 변경 이유
- operator가 PR #27을 merge했지만 `.pipeline/operator_request.md`가 계속 `STATUS: needs_operator`, `REASON_CODE: pr_merge_gate`로 남아 런타임/컨트롤러가 사람 대기처럼 보이는 문제가 있었다.
- PR #27은 merge 당시 head `1b23edf...`를 기준으로 닫혔고, 이후 `feat/watcher-turn-state`에는 `0b5c420`, `77d1827`, `ba93943`, `5cc7a1d` 같은 추가 commit이 생겼다.
- 따라서 같은 PR #27 번호로 현재 branch HEAD merge 승인을 계속 요구하는 것은 완료된 merge gate가 아니라 닫힌 PR 번호 재사용/HEAD mismatch 상황이다.
- 이 경우 자동화는 operator에게 같은 승인을 다시 요구하지 말고, stale operator wait를 내린 뒤 verify/handoff가 새 PR 또는 control 정정을 맡아야 한다.

## 핵심 변경
- `PrMergeStatusCache`가 `gh pr view <PR> --json state,mergedAt,headRefOid`로 참조 PR의 merge 상태를 확인하고, control 본문/meta의 `HEAD`와 GitHub `headRefOid`를 prefix match로 비교한다.
- `pr_merge_gate`가 참조한 PR이 이미 merged이고 HEAD가 맞으면 `pr_merge_completed` recovery로 stale operator wait를 내린다.
- 참조 PR은 merged이지만 control `HEAD`가 merged PR head와 다르면 `pr_merge_head_mismatch` recovery로 내려 `active_control_status=none`을 유지하고 verify/handoff follow-up으로 회수한다.
- `supervisor.py`와 `watcher_core.py`가 동일한 `PrMergeStatusCache.control_resolution()` 결과를 사용하도록 통합해 런타임과 watcher 판정이 갈라지지 않게 했다.
- Tk GUI presenter는 canonical `automation_health != needs_operator`인 verify/recovery 상태에서 debug용 `compat.control_slots.active`의 `operator_request.md`를 active operator wait 색상으로 승격하지 않게 했다.
- `README.md`, `.pipeline/README.md`, `docs/MILESTONES.md`, runtime 기술설계/운영 RUNBOOK에 `pr_merge_completed`와 `pr_merge_head_mismatch` 계약을 반영했다.
- 새/기존 단위 테스트가 schema evaluator, watcher turn recovery, supervisor status surface에서 `pr_merge_head_mismatch`가 `needs_operator`로 남지 않는지 확인한다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/pr_merge_state.py pipeline_runtime/supervisor.py watcher_core.py` → 통과.
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/pr_merge_state.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pr_merge_state.py` → 통과.
- `python3 -m unittest tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_pr_merge_gate_stays_operator_visible_without_gate_marker tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_pr_merge_gate_is_recoverable_after_referenced_pr_is_completed -v` → 통과.
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest.test_pr_merge_gate_stays_operator_wait_without_verify_retriage tests.test_watcher_core.TurnResolutionTest.test_pr_merge_gate_recovers_after_referenced_pr_is_merged -v` → 통과.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_pr_merge_gate_operator_visible_without_gated_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_ignores_pr_merge_gate_after_pr_is_merged -v` → 통과.
- `python3 -m unittest tests.test_pr_merge_state tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_pr_merge_gate_head_mismatch_routes_to_recovery tests.test_watcher_core.TurnResolutionTest.test_pr_merge_gate_head_mismatch_routes_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_recovers_pr_merge_gate_when_pr_head_mismatches_control_head -v` → 5개 통과.
- `python3 -m unittest tests.test_pr_merge_state tests.test_operator_request_schema tests.test_watcher_core.TurnResolutionTest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_pr_merge_gate_operator_visible_without_gated_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_ignores_pr_merge_gate_after_pr_is_merged tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_recovers_pr_merge_gate_when_pr_head_mismatches_control_head tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_external_publication_boundary_operator_visible -v` → 58개 통과.
- `python3 -m py_compile pipeline_gui/home_presenter.py pipeline_gui/app.py` → 통과.
- `python3 -m unittest tests.test_pipeline_gui_home_presenter -v` → 20개 통과.
- `git diff --check -- .pipeline/README.md README.md docs/MILESTONES.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md tests/test_pipeline_runtime_supervisor.py` → 통과.
- `python3 -m unittest tests.test_pipeline_gui_home_presenter tests.test_pr_merge_state tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_pr_merge_gate_head_mismatch_routes_to_recovery tests.test_watcher_core.TurnResolutionTest.test_pr_merge_gate_head_mismatch_routes_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_recovers_pr_merge_gate_when_pr_head_mismatches_control_head -v` → 25개 통과.
- `git diff --check` → 통과.
- `python3 -m pipeline_runtime.cli restart . --mode experimental --no-attach` → 통과.
- `python3 -m pipeline_runtime.cli status . --json` → run `20260423T042237Z-p41181`, `control.active_control_status=none`, `automation_health=recovering`, `automation_next_action=retrying`, `autonomy.block_reason=pr_merge_head_mismatch`.
- `rg -n "control_operator_stale_ignored|pr_merge_head_mismatch" .pipeline/runs/20260423T042237Z-p41181/events.jsonl` → `control_operator_stale_ignored` event가 `reason=pr_merge_head_mismatch`로 기록됨.

## 남은 리스크
- 현재 branch `feat/watcher-turn-state`는 `origin/main`의 PR #27 merge commit 이후 추가 commit을 포함한다. PR #27 자체는 이미 닫혔으므로 verify/handoff가 새 PR을 만들거나 control을 현재 HEAD 기준으로 바로잡아야 한다.
- `.pipeline/operator_request.md` 파일은 compatibility/debug surface에 남아 있을 수 있지만 canonical `control`은 `none`으로 내려간다. 컨트롤러/런타임 판단은 canonical `status.json`와 `events.jsonl`을 기준으로 봐야 하며, Tk GUI도 canonical `automation_health`를 기준으로 operator wait 색상을 결정한다.
- 현재 live runtime은 `VERIFY_ACTIVE` / `verify_dispatch_pending` 상태로 Claude verify lane이 follow-up을 잡는 중이다. 이 상태는 operator 승인 대기가 아니라 recovery 후속 처리다.
- 이번 closeout 시점의 문서/test/work-note 변경은 아직 별도 commit/push되지 않았다.
