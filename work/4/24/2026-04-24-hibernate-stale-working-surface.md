# 2026-04-24 hibernate stale working surface 수정

## 변경 파일
- `pipeline_runtime/turn_arbitration.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_turn_arbitration.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/24/2026-04-24-hibernate-stale-working-surface.md`
- `verify/4/24/2026-04-24-hibernate-stale-working-surface.md`

## 사용 skill
- `security-gate`: runtime control/status 표면 변경이 로컬 tmux 런처 상태 표시만 바꾸며 승인/쓰기 경계를 넓히지 않는지 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 재현 원인, 검증 결과를 한국어 `/work` closeout으로 기록했습니다.

## 변경 이유
- 실제 Claude pane은 idle prompt(`❯`)이고 task hint도 `active:false`였지만, status JSON에는 이전 `turn_state=VERIFY_ACTIVE`와 `progress_phase=running_verification`이 남아 controller가 Claude를 working처럼 표시했습니다.
- 원인은 `.pipeline/operator_request.md`가 hibernate gate로 분류된 뒤에도 watcher startup arbitration과 supervisor status surface가 stale verify turn을 충분히 지우지 못한 것이었습니다.

## 핵심 변경
- `resolve_watcher_turn()`이 hibernate operator gate를 만나면 최신 work verify 필요 표시가 남아 있어도 `TURN_IDLE`을 반환하도록 했습니다.
- `RuntimeSupervisor` status surface가 hibernate operator gate를 만나면 stale `VERIFY_ACTIVE` 대신 `IDLE / operator_request_gated_hibernate`를 노출하도록 했습니다.
- 이때 `progress`는 빈 객체로 유지되고 lane에는 `progress_phase`가 붙지 않으며, Claude task hint도 `active:false`로 유지됩니다.
- 변경은 status/arbitration 표면에 한정되며 control slot, 승인 흐름, 파일 쓰기 권한, PR merge 경계를 자동으로 넘지 않습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/turn_arbitration.py pipeline_runtime/supervisor.py tests/test_turn_arbitration.py tests/test_pipeline_runtime_supervisor.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_turn_arbitration.WatcherTurnArbitrationTest.test_operator_gate_hibernate_suppresses_stale_verify_need tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_stale_verify_progress_during_operator_hibernate`
  - 통과: `Ran 2 tests`, `OK`
- `python3 -m unittest tests.test_turn_arbitration tests.test_pipeline_runtime_supervisor`
  - 통과: `Ran 156 tests in 1.187s`, `OK`
- `bash stop-pipeline.sh`
  - 통과: exit code 0
- `bash start-pipeline.sh`
  - 통과: exit code 0
- `python3 -m pipeline_runtime.cli status . --json`
  - 재시작 후 최종 확인: `runtime_state=RUNNING`, `turn_state.state=IDLE`, `turn_state.reason=operator_request_gated_hibernate`, `progress={}`, Claude/Codex/Gemini 모두 `READY`
- `cat .pipeline/runs/20260424T052542Z-p434030/task-hints/claude.json`
  - 확인: `active=false`, `job_id=""`, `dispatch_id=""`, `control_seq=-1`, `inactive_reason=task_hint_cleared`
- `tmux capture-pane -t aip-projectH:0.0 -p -S -40`
  - 확인: Claude pane은 idle prompt(`❯`) 상태
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- `.pipeline/operator_request.md`의 `m28_direction + pr_merge_gate` hibernate 경계는 여전히 남아 있어, 런처가 새 구현 작업을 dispatch하지 않는 것은 현재 정책상 정상입니다.
- 이번 수정은 "idle인데 working처럼 보이는 거짓 표면"을 제거한 것이며, PR merge 또는 M28 방향 선택 문제를 자동으로 해결하지는 않습니다.
- 다음 자동화 개선은 operator gate가 PR merge 대기와 safe local next-slice를 분리해, merge 승인을 기다리면서도 안전한 로컬 구현을 계속 시작하도록 control writer 쪽을 고치는 것입니다.
