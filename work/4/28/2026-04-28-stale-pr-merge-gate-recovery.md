# 2026-04-28 stale PR merge gate recovery

## 상태

완료.

## 사용 스킬

- `github`: PR #46의 실제 머지 상태 확인
- `security-gate`: operator control / merge gate 대기 상태 변경의 안전 경계 확인
- `work-log-closeout`: 변경 및 검증 기록 작성

## 변경 파일

- `pipeline_runtime/pr_merge_state.py`
- `tests/test_pr_merge_state.py`
- `.pipeline/advisory_request.md` (ignored runtime control slot)
- `work/4/28/2026-04-28-stale-pr-merge-gate-recovery.md`

## 배경

`.pipeline/operator_request.md`의 `CONTROL_SEQ 1149`가 `pr_merge_gate`로 PR #46 머지를 계속
요청하고 있었지만, GitHub truth 기준 PR #46은 이미 `2026-04-27T15:05:51Z`에 merge commit
`89285ca`로 머지된 상태였다. 로컬 `origin/main`도 `89285ca`까지 fetch했다.

## 핵심 변경

- `PrMergeStatusCache`의 PR merge 판별을 GitHub CLI 경로와 로컬 git 증거 경로로 분리했다.
- `gh pr view`가 없거나 pending으로 확인될 때, 로컬 `origin/main`/`main` 계열 ref에서 merge 완료 증거를 확인한다.
- control에 기대 HEAD SHA가 있으면 `git merge-base --is-ancestor <head> <ref>`로 main 포함 여부를 확인한다.
- 기대 HEAD SHA가 없으면 `git log --grep "Merge pull request #<number>"`로 해당 PR merge commit을 확인한다.
- `gh`가 불가능한 환경에서 로컬 merge commit, 로컬 HEAD 포함, 증거 없음 pending을 각각 검증하는 unit test를 추가했다.
- `.pipeline/advisory_request.md`를 `CONTROL_SEQ 1150`으로 갱신해 stale operator merge gate `CONTROL_SEQ 1149`를 supersede했다.

## 검증

- PASS: `python3 -m py_compile pipeline_runtime/pr_merge_state.py tests/test_pr_merge_state.py`
- PASS: `python3 -m unittest -v tests.test_pr_merge_state`
- PASS: `python3 -m unittest -v tests.test_watcher_core.TurnResolutionTest.test_operator_wait_recovers_pr_merge_completion_without_operator_file_change tests.test_watcher_core.TurnResolutionTest.test_pr_merge_gate_recovers_after_referenced_pr_is_merged`
- PASS: `python3 -m unittest -v tests.test_pr_merge_state tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_ignores_pr_merge_gate_after_pr_is_merged tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_internal_pr_merge_gate_to_verify_followup_backlog tests.test_watcher_core.TurnResolutionTest.test_operator_wait_recovers_pr_merge_completion_without_operator_file_change tests.test_watcher_core.TurnResolutionTest.test_pr_merge_gate_recovers_after_referenced_pr_is_merged tests.test_watcher_core.TurnResolutionTest.test_pr_merge_gate_notifies_verify_retriage_without_blocking_operator_wait`
- PASS: `git diff --check -- pipeline_runtime/pr_merge_state.py tests/test_pr_merge_state.py .pipeline/advisory_request.md`
- PASS: `pipeline_runtime.schema.parse_control_slots(Path(".pipeline"))` 기준 active control은 `advisory_request.md` / `request_open` / `CONTROL_SEQ 1150`, stale operator control은 `operator_request.md` / `needs_operator` / `CONTROL_SEQ 1149`.
- 참고: 보조 확인 중 `pipeline_runtime.control_slot` 잘못된 import로 1회 실패했고, 위의 실제 parser 위치로 정정해 확인했다.

## 남은 위험

- 로컬 fallback은 fetch된 로컬 ref 증거에 의존한다. `gh`도 없고 `origin/main`도 최신이 아니면 pending으로 남는 것이 안전한 기본값이다.
- 이번 라운드에서 commit, push, PR 생성, merge 실행은 하지 않았다.
- 브라우저/E2E는 변경 범위가 runtime merge gate helper와 unit contract에 한정되어 실행하지 않았다.
