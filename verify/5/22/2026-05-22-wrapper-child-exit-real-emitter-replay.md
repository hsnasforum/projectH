# verify: 2026-05-22 wrapper child-exit real emitter replay (2142)

## 대상 work
`work/5/22/2026-05-22-wrapper-child-exit-real-emitter-replay.md`

## 검증 결과: READY

## 변경 파일
- 없음

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| real `_WrapperEmitter` child-exit replay 추가 | `tests/test_pipeline_runtime_cli.py:1342-1439` | ✓ |
| replay가 fake selector, fake child, local pipe, fake stdout, active task hint를 사용함 | `tests/test_pipeline_runtime_cli.py:1354-1424` | ✓ |
| `child.poll() == 0` 경로로 `_lane_wrapper()` child-exit branch를 타게 함 | `tests/test_pipeline_runtime_cli.py:1346-1348` | ✓ |
| `TASK_DONE(reason=stream_eof)` 1회와 직후 `READY`를 검증함 | `tests/test_pipeline_runtime_cli.py:1426-1434` | ✓ |
| selector close와 child `wait()` 호출을 확인함 | `tests/test_pipeline_runtime_cli.py:1435-1439` | ✓ |
| 이번 slice에서 production code 추가 수정은 없음 | `pipeline_runtime/cli.py` | ✓ |

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py` | PASS |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_child_exit_with_real_emitter_emits_task_done -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_text_stream_finish_emits_task_done_once_after_acceptance -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done -v` | PASS (`Ran 1 test`, `OK`) |
| `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/22/2026-05-22-wrapper-child-exit-real-emitter-replay.md` | PASS |

## 범위 준수 확인

- scope-in: `tests/test_pipeline_runtime_cli.py`의 focused local child-exit/PTY EOF replay, active task hint, wrapper event log assertion, `/work` closeout ✓
- scope-out: live Claude dispatch, tmux, supervisor, browser, web server, networked command, runtime profile/role binding 변경, watcher deadline policy 변경, commit/push/PR/merge/publication ✓
- 제품/UI/승인 정책 변경이 아니라 local runtime wrapper test 보강이므로 별도 제품 문서 동기화는 필요하지 않은 범위로 확인했습니다.

## 런타임 상태 참고

- dispatcher 제공 상태: `.pipeline/runs/20260522T074442Z-p9631/status.json`
- run_id: `20260522T074442Z-p9631`
- runtime_state: `RUNNING`
- automation_health: `recovering`
- automation_next_action: `retrying`
- active_control: `.pipeline/implement_handoff.md#2141 implement`
- turn_state: `IDLE`
- active_round: `VERIFY_PENDING`
- 이 verify round에서는 lane-local `status --json`, `doctor --json`, `tmux` 결과를 런타임 liveness 권위로 사용하지 않았습니다.

## 현재 의미

- text-mode `finish_stream()`, SIGTERM/SIGINT stop path, real-emitter signal replay, real-emitter child-exit/PTY EOF replay가 모두 focused unit 수준에서 통과했습니다.
- `verify/5/22/2026-05-22-live-claude-verify-trigger-5.md`는 Claude verify lane 활성화와 trigger-5 fresh verify 대상 전제를 READY로 기록했지만, 그 뒤 최신 `/work`가 child-exit replay로 바뀌었습니다.
- 따라서 live Claude 관찰을 다시 시도하려면 현재 profile 전제를 유지한 상태에서 최신 `/work`를 fresh trigger로 갱신하는 것이 가장 좁은 다음 slice입니다.

## 남은 리스크

- Claude lane이 실제 enabled/active 상태에서 latest work를 수신하고 `TASK_DONE source=wrapper lane=Claude`를 내는지는 이번 verify에서 live로 관찰하지 않았습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일, broad runtime smoke, controller/browser smoke, full smoke는 실행하지 않았습니다.
- 기존 working tree에는 이전 CONTROL_SEQ 2131/2132/2133/2136/2137 관련 미커밋 변경과 여러 untracked `work/`, `verify/`, `report/` 기록이 남아 있으며, 이번 verify에서 되돌리지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.

## 다음 control 판단

COUNCIL_DECISION: implement
REASON_CODE: live_claude_verify_trigger_6
OWNER_ROLE: implement
NEXT_CONTROL_FILE: `.pipeline/implement_handoff.md`
NEXT_CONTROL_SEQ: 2142

EVIDENCE:
- `work/5/22/2026-05-22-wrapper-child-exit-real-emitter-replay.md`
- `verify/5/22/2026-05-22-wrapper-child-exit-real-emitter-replay.md`
- `verify/5/22/2026-05-22-live-claude-verify-trigger-5.md`
- `.pipeline/config/agent_profile.json`
- dispatcher-provided `RUNTIME_STATUS_AT_DISPATCH`

REJECTED:
- `.pipeline/advisory_request.md`: child-exit replay is READY and trigger-5 verify already states the next observation criterion, so no low-confidence tie remains for advisory.
- `.pipeline/operator_request.md`: no destructive write, credential/auth, approval-record repair, truth-sync blocker, merge/release/publication, or immediate safety boundary blocks local work now.
