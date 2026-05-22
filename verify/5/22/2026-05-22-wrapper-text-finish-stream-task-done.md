# verify: 2026-05-22 wrapper text finish stream TASK_DONE (2132)

## 대상 work
`work/5/22/2026-05-22-wrapper-text-finish-stream-task-done.md`

## 검증 결과: READY

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `_WrapperEmitter.finish_stream()`이 JSONL 여부와 무관하게 `_on_claude_completion("stream_eof")` 호출 | `pipeline_runtime/cli.py:988-989` | ✓ |
| `_lane_wrapper()` 신호/EOF/child-exit 경로가 `_finish_stream_once()`로 중복 방지 유지 | `pipeline_runtime/cli.py:1544-1606` | ✓ |
| text-mode accepted task의 stream finish completion 테스트 추가 | `tests/test_pipeline_runtime_cli.py:590-622` | ✓ |
| 직전 signal stop path 테스트 유지 | `tests/test_pipeline_runtime_cli.py:1155-1233` | ✓ |

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py` | PASS |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_text_stream_finish_emits_task_done_once_after_acceptance -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_finishes_stream_once_when_signal_requests_stop -v` | PASS (`Ran 1 test`, `OK`) |
| `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/22/2026-05-22-wrapper-text-finish-stream-task-done.md` | PASS |

## 범위 준수 확인

- scope-in: `_WrapperEmitter.finish_stream()` behavior, focused wrapper completion tests, 새 `/work` closeout ✓
- scope-out: watcher deadline policy, runtime profile/owner binding, dispatch selection, live trigger notes, commit/push/PR/merge/publication ✓
- 제품/UI/승인 정책/운영자 규칙 변경이 아니라 runtime wrapper completion 내부 보정이므로 별도 제품 문서 동기화는 필요하지 않은 범위로 확인했습니다.

## 런타임 상태 참고

- dispatcher 제공 상태: `.pipeline/runs/20260522T074442Z-p9631/status.json`
- run_id: `20260522T074442Z-p9631`
- runtime_state: `RUNNING`
- automation_health: `recovering`
- automation_next_action: `retrying`
- active_control: `.pipeline/implement_handoff.md#2132 implement`
- turn_state: `IDLE`
- active_round: `VERIFY_PENDING`
- 이 verify round에서는 lane-local `status --json`, `doctor --json`, `tmux` 결과를 런타임 liveness 권위로 사용하지 않았습니다.

## 현재 의미

- 직전 slice는 `_lane_wrapper()`가 SIGTERM/SIGINT에서 `finish_stream()`을 호출하도록 했습니다.
- 이번 slice는 text-mode `_WrapperEmitter.finish_stream()` 호출이 accepted task를 `TASK_DONE(reason=stream_eof)`/`READY`로 닫도록 만들었습니다.
- 따라서 두 변경을 합치면 signal stop path의 stream finish 호출이 wrapper completion 의미를 갖습니다.

## 남은 리스크

- signal stop path와 실제 `_WrapperEmitter`/task hint/event log를 결합한 end-to-end unit replay는 아직 없습니다. 현재 검증은 signal path 호출 보장 테스트와 text-mode completion semantics 테스트가 분리되어 있습니다.
- Claude lane이 실제 enabled/active 상태에서 trigger work를 수신하는지는 이번 verify에서 live로 재관찰하지 않았습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일이나 broad runtime smoke는 실행하지 않았습니다. 변경 범위가 wrapper completion semantics와 focused tests에 한정되어 좁은 검증만 수행했습니다.
- 기존 working tree에는 CONTROL_SEQ 2129/2131 관련 미커밋 변경과 여러 untracked `work/`, `verify/` 기록이 남아 있으며, 이번 verify에서 되돌리지 않았습니다.
