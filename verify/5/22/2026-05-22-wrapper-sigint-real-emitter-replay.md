# verify: 2026-05-22 wrapper SIGINT real emitter replay (2138)

## 대상 work
`work/5/22/2026-05-22-wrapper-sigint-real-emitter-replay.md`

## 검증 결과: READY

## 변경 파일
- 없음

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| real `_WrapperEmitter` signal stop replay가 helper + `subTest` 구조로 정리됨 | `tests/test_pipeline_runtime_cli.py:1235-1340` | ✓ |
| SIGTERM replay가 기존 `TASK_DONE(reason=stream_eof)` 1회와 직후 `READY` 검증을 유지함 | `tests/test_pipeline_runtime_cli.py:1321-1333` | ✓ |
| SIGINT replay가 같은 event 계약과 `os.killpg(child.pid, signal.SIGINT)` 호출을 검증함 | `tests/test_pipeline_runtime_cli.py:1335-1340` | ✓ |
| 이번 slice에서 production code 추가 수정은 없음 | `pipeline_runtime/cli.py` | ✓ |

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py` | PASS |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_text_stream_finish_emits_task_done_once_after_acceptance -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done -v` | PASS (`Ran 1 test`, `OK`) |
| `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/22/2026-05-22-wrapper-sigint-real-emitter-replay.md` | PASS |

## 범위 준수 확인

- scope-in: `tests/test_pipeline_runtime_cli.py`의 real `_WrapperEmitter` lane-wrapper signal stop replay 확장, active task hint, wrapper event log assertion, SIGINT forwarding assertion ✓
- scope-out: live Claude dispatch, tmux, supervisor, browser, web server, networked command, runtime profile/owner binding 변경, watcher deadline policy 변경, commit/push/PR/merge/publication ✓
- 이번 slice는 local unit replay coverage 보강이므로 제품/UI/승인 정책 문서 동기화는 필요하지 않은 범위로 확인했습니다.

## 런타임 상태 참고

- dispatcher 제공 상태: `.pipeline/runs/20260522T074442Z-p9631/status.json`
- run_id: `20260522T074442Z-p9631`
- runtime_state: `RUNNING`
- automation_health: `recovering`
- automation_next_action: `retrying`
- active_control: `.pipeline/implement_handoff.md#2137 implement`
- turn_state: `IDLE`
- active_round: `VERIFY_PENDING`
- 이 verify round에서는 lane-local `status --json`, `doctor --json`, `tmux` 결과를 런타임 liveness 권위로 사용하지 않았습니다.

## 현재 의미

- `finish_stream()` signal stop 호출, text-mode `TASK_DONE(reason=stream_eof)` completion semantics, real emitter/task-hint/event-log 결합 replay, SIGTERM/SIGINT forwarding replay가 모두 focused unit 수준에서 통과했습니다.
- 이번 검증은 local unit replay truth이며, live Claude lane dispatch 성공까지 확인한 것은 아닙니다.
- 이전 live Claude trigger-4 observation의 `BLOCKED_BY_PRECONDITION` 상태는 이번 SIGINT local replay로 직접 해결되지 않았습니다.

## 남은 리스크

- Claude lane이 실제 enabled/active 상태에서 trigger work를 수신하는지는 이번 verify에서 live로 재관찰하지 않았습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일, broad runtime smoke, controller/browser smoke는 실행하지 않았습니다.
- 기존 working tree에는 CONTROL_SEQ 2131/2132/2133 관련 미커밋 변경과 여러 untracked `work/`, `verify/` 기록이 남아 있으며, 이번 verify에서 되돌리지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.

## 다음 control 판단

COUNCIL_DECISION: advisory_followup
REASON_CODE: next_slice_ambiguity_after_sigint_wrapper_replay
OWNER_ROLE: advisory
NEXT_CONTROL_FILE: `.pipeline/advisory_request.md`
NEXT_CONTROL_SEQ: 2138

EVIDENCE:
- `work/5/22/2026-05-22-wrapper-sigint-real-emitter-replay.md`
- `verify/5/22/2026-05-22-wrapper-sigint-real-emitter-replay.md`
- `verify/5/22/2026-05-22-live-claude-trigger-4-restart-observation.md`
- `.pipeline/advisory_advice.md`

REJECTED:
- `.pipeline/implement_handoff.md`: SIGINT replay는 완료되어 READY지만, 그 다음 동일 family 후보가 live precondition cleanup, child-exit real-emitter replay, bounded wrapper confidence check로 다시 갈라져 exact implement slice 확신이 낮습니다.
- `.pipeline/operator_request.md`: destructive write, credential/auth, approval-record repair, truth-sync blocker, merge/release/publication, immediate safety boundary가 현재 증거에 없습니다.
