# 2026-04-24 PR merge gate follow-up backlog 처리

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/4/24/2026-04-24-pr-merge-gate-followup-backlog.md`
- `verify/4/24/2026-04-24-pr-merge-gate-followup-backlog.md`

## 사용 skill
- `security-gate`: merge/PR publication boundary를 넘지 않고 local runtime routing만 바꾸는지 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 한국어 `/work` 기록으로 분리했습니다.

## 변경 이유
- `.pipeline/operator_request.md`의 `REASON_CODE: m28_direction + pr_merge_gate`처럼 compound reason이 들어오면 기존 분류가 operator stop/hibernate 쪽으로 기울어, PR merge 대기 때문에 안전한 로컬 구현까지 멈출 수 있었습니다.
- 사용자 의도는 merge 승인은 명시적으로 남기되, 그 대기 때문에 pipeline launcher 생산성이 떨어지면 안 된다는 것입니다.

## 핵심 변경
- `normalize_reason_code()`가 compound reason 안의 `pr_merge_gate`, `pr_creation_gate`, `commit_push_bundle_authorization`을 우선 인식하도록 했습니다.
- `normalize_decision_class()`가 `next_milestone_selection + branch_strategy` 같은 compound 선택을 `next_slice_selection`으로 정규화하도록 했습니다.
- watcher/operator schema 테스트에서 `m28_direction + pr_merge_gate`가 `triage / verify_followup` backlog로 라우팅되는 것을 고정했습니다.
- supervisor status surface는 idle 상태에 남은 verify-followup operator gate만 `VERIFY_FOLLOWUP`으로 합성하고, 이미 의미 있는 `VERIFY_ACTIVE`나 `OPERATOR_WAIT` 상태는 덮지 않도록 좁혔습니다.
- 실제 재시작 후 `.pipeline/operator_request.md` seq114는 stale backlog로 밀려났고, `.pipeline/implement_handoff.md` seq117이 active implement control로 진행 중입니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py pipeline_runtime/turn_arbitration.py tests/test_operator_request_schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest.test_compound_milestone_pr_merge_gate_routes_to_verify_followup_backlog tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_compound_milestone_pr_merge_gate_routes_to_verify_followup_backlog tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_compound_milestone_pr_merge_gate_to_followup_without_claude_working tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_stale_autonomy_when_active_round_targets_newer_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_codex_task_hint_during_operator_wait`
  - 통과: `Ran 5 tests`, `OK`
- `python3 -m unittest tests.test_operator_request_schema tests.test_turn_arbitration tests.test_pipeline_runtime_supervisor tests.test_watcher_core`
  - 통과: `Ran 382 tests in 11.223s`, `OK (skipped=1)`
- `git diff --check`
  - 통과: 출력 없음
- `python3 -m unittest discover -s tests -p 'test_*.py'`
  - 통과: `Ran 1783 tests in 350.739s`, `OK (skipped=1)`
- `bash stop-pipeline.sh`
  - 통과: exit code 0
- `bash start-pipeline.sh`
  - 통과: exit code 0
- `python3 -m pipeline_runtime.cli status . --json`
  - 재시작 후 최종 확인: `runtime_state=RUNNING`, `automation_health=ok`, `automation_next_action=continue`, active control `.pipeline/implement_handoff.md` seq117, stale backlog에 `.pipeline/operator_request.md` seq114 유지

## 남은 리스크
- PR merge 자체는 여전히 operator-approved publication boundary입니다. 이번 변경은 merge를 자동 수행하지 않고, merge 대기와 safe local implementation을 분리합니다.
- 현재 별도 tmux Codex implement lane이 seq117 작업을 진행 중입니다. 그 lane의 `verify_fsm.py`, `watcher_core.py`, `tests/test_verify_fsm.py` 변경은 이 closeout의 소유 범위가 아닙니다.
- browser/e2e는 이 runtime-only routing slice 이후 재실행하지 않았습니다. 브라우저 계약 변경은 없고, 같은 날 앞선 large verification에서 full browser/e2e는 통과한 상태였습니다.
