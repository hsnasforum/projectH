# 2026-04-28 PR Merge Recovery No Next Control

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/28/2026-04-28-pr-merge-recovery-no-next-control.md`

## 사용 skill
- `onboard-lite`: pipeline runtime의 run/test entrypoint와 operator recovery 소유 경계를 좁게 확인했습니다.
- `security-gate`: runtime control write와 operator boundary가 approval/merge 경계를 우회하지 않는지 확인했습니다.
- `github:github`: PR #53이 실제 merged 상태인지 GitHub connector로 확인해 원인 판단에 사용했습니다.
- `doc-sync`: runtime control-recovery 계약을 기술설계서와 RUNBOOK에 좁게 반영했습니다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 closeout으로 정리했습니다.

## 변경 이유
- PR merge gate가 실제로 완료되어 `pr_merge_completed` recovery로 내려간 뒤, verify/handoff owner가 새 control 없이 idle로 돌아오면 watcher가 다음 control을 만들지 못하고 `next_control_pending`에 머무를 수 있었습니다.
- 기존 `operator_retriage_no_next_control` 승격은 gated operator marker만 보았고, `pr_merge_completed` 같은 control-recovery marker는 보지 못했습니다.

## 핵심 변경
- watcher가 operator control-recovery 시작 시각과 recovery key를 기록합니다.
- `operator_retriage_no_next_control` 감지가 기존 gated operator follow-up뿐 아니라 `pr_merge_completed`, `pr_merge_head_mismatch`, `operator_approval_completed` 같은 recovery follow-up도 포함하도록 확장했습니다.
- no-next-control 승격이 recovery marker의 원 reason을 `source_reason`으로 보존해 advisory request 본문에 `pr_merge_completed` 같은 원인을 남깁니다.
- polling 순서를 조정해 recovery follow-up이 반복 재처리되기 전에 no-next-control 승격 기회를 먼저 갖게 했습니다.
- PR #53 merge 완료 패턴을 재현하는 watcher 테스트를 추가했습니다.
- 기술설계서와 RUNBOOK에 control-recovery follow-up도 새 control 없이 idle이면 advisory로 승격된다는 운영 계약을 추가했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py`
- 통과: `python3 -m unittest -v tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_promotes_to_advisory_request tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_promotes_to_advisory_request`
- 통과: `python3 -m unittest -v tests.test_watcher_core` (207 tests)
- 통과: `git diff --check -- watcher_core.py tests/test_watcher_core.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- 통과: `python3 -m py_compile watcher_core.py`

## 남은 리스크
- 현재 실행 중인 daemon에는 코드 변경이 자동 반영되지 않으므로, 실제 파이프라인 재개에는 watcher/supervisor 재시작 또는 다음 런타임 로드가 필요합니다.
- 이번 변경은 no-silent-stall guard만 보강하며, PR 머지 자체를 자동 실행하거나 operator approval 경계를 우회하지 않습니다.
- 전체 repo unittest, browser/E2E, 장기 soak는 실행하지 않았습니다.
