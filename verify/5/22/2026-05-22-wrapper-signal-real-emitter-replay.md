# verify: 2026-05-22 wrapper signal real emitter replay (2133)

## 대상 work
`work/5/22/2026-05-22-wrapper-signal-real-emitter-replay.md`

## 검증 결과: READY

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `_WrapperEmitter.finish_stream()`이 `stream_eof` completion helper 호출 | `pipeline_runtime/cli.py:988-989` | ✓ |
| `_lane_wrapper()`가 `stop_requested`에서 `_finish_stream_once()` 호출 | `pipeline_runtime/cli.py:1544-1606` | ✓ |
| fake selector + real `_WrapperEmitter` + active task hint replay 추가 | `tests/test_pipeline_runtime_cli.py:1235-1332` | ✓ |
| replay가 `TASK_DONE(reason=stream_eof)` 1회와 직후 `READY`를 검증 | `tests/test_pipeline_runtime_cli.py:1320-1328` | ✓ |

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py` | PASS |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_text_stream_finish_emits_task_done_once_after_acceptance -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_finishes_stream_once_when_signal_requests_stop -v` | PASS (`Ran 1 test`, `OK`) |
| `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/22/2026-05-22-wrapper-signal-real-emitter-replay.md` | PASS |

## 범위 준수 확인

- scope-in: real `_WrapperEmitter`를 쓰는 local replay test, active task hint, wrapper event log assertion, 새 `/work` closeout ✓
- scope-out: production runtime 추가 수정, watcher deadline policy, runtime profile/owner binding, dispatch selection, live trigger notes, commit/push/PR/merge/publication ✓
- 제품/UI/승인 정책/운영자 규칙 변경이 아니라 local runtime wrapper test 보강이므로 별도 제품 문서 동기화는 필요하지 않은 범위로 확인했습니다.

## 런타임 상태 참고

- dispatcher 제공 상태: `.pipeline/runs/20260522T074442Z-p9631/status.json`
- run_id: `20260522T074442Z-p9631`
- runtime_state: `RUNNING`
- automation_health: `recovering`
- automation_next_action: `retrying`
- active_control: `.pipeline/implement_handoff.md#2133 implement`
- turn_state: `IDLE`
- active_round: `VERIFY_PENDING`
- 이 verify round에서는 lane-local `status --json`, `doctor --json`, `tmux` 결과를 런타임 liveness 권위로 사용하지 않았습니다.

## 현재 의미

- signal stop path의 `finish_stream()` 호출 보장, text-mode `finish_stream()` completion semantics, real emitter/task-hint/event-log 결합 replay가 모두 focused unit 수준에서 통과했습니다.
- 이번 검증은 local unit replay truth이며, live Claude lane dispatch 성공까지 확인한 것은 아닙니다.

## 남은 리스크

- Claude lane이 실제 enabled/active 상태에서 trigger work를 수신하는지는 이번 verify에서 live로 재관찰하지 않았습니다.
- 이전 `verify/5/22/2026-05-22-live-claude-trigger-4-restart-observation.md`는 active profile이 Codex-only라 trigger-4가 Claude lane에 전달되지 않은 `BLOCKED_BY_PRECONDITION`을 기록했습니다. 이 선행조건은 이번 local replay test로 직접 해결되지 않습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일이나 broad runtime smoke는 실행하지 않았습니다. 변경 범위가 focused replay와 focused completion tests에 한정되어 좁은 검증만 수행했습니다.
- 기존 working tree에는 CONTROL_SEQ 2129/2131/2132 관련 미커밋 변경과 여러 untracked `work/`, `verify/` 기록이 남아 있으며, 이번 verify에서 되돌리지 않았습니다.

## 다음 판단 필요

- 같은 incident family에서 다음 후보는 최소 세 가지입니다.
- 후보 A: Claude lane이 실제 enabled/active인 상태로 live trigger 재관찰 조건을 정리합니다.
- 후보 B: active profile/role routing이 Codex-only인 현재 운영 상태를 전제로 Claude-specific live 관찰 목표를 보류하고 Codex-owned wrapper completion 쪽으로 검증 축을 전환합니다.
- 후보 C: 더 넓은 runtime CLI focused suite 실행 또는 추가 replay를 통해 local confidence를 먼저 높입니다.
- 이 선택은 next-slice 우선순위와 live 관찰 전제 판단이 겹치므로 advisory에 요청합니다.
