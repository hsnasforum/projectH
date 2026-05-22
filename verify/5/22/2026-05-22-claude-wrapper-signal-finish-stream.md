# verify: 2026-05-22 Claude wrapper signal finish stream (2131)

## 대상 work
`work/5/22/2026-05-22-claude-wrapper-signal-finish-stream.md`

## 검증 결과: READY

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `_lane_wrapper()` 내부 `_finish_stream_once()` helper 추가 | `pipeline_runtime/cli.py:1546-1553` | ✓ |
| PTY EOF 경로가 helper를 통해 `finish_stream()` 호출 | `pipeline_runtime/cli.py:1584-1585` | ✓ |
| child exit / `OSError` 경로가 helper를 통해 중복 없이 `finish_stream()` 호출 | `pipeline_runtime/cli.py:1591-1603` | ✓ |
| SIGTERM/SIGINT forwarding 후 `stop_requested` 경로가 helper 호출 뒤 종료 | `pipeline_runtime/cli.py:1605-1607` | ✓ |
| 신호 요청 경로 focused unit test 추가 | `tests/test_pipeline_runtime_cli.py:1121-1199` | ✓ |

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py` | PASS |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode -v` | PASS (`Ran 1 test`, `OK`) |
| `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_finishes_stream_once_when_signal_requests_stop -v` | PASS (`Ran 1 test`, `OK`) |
| `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/22/2026-05-22-claude-wrapper-signal-finish-stream.md` | PASS |

## 범위 준수 확인

- scope-in: `pipeline_runtime/cli.py`, `tests/test_pipeline_runtime_cli.py`, 새 `/work` closeout ✓
- scope-out: watcher deadline policy, runtime profile/owner binding, dispatch selection, `verify/` 구현 lane 작성, commit/push/PR/merge/publication ✓
- 제품/UI/승인 정책/운영자 규칙 변경이 아니므로 제품 문서 동기화는 필요하지 않은 범위로 확인했습니다.

## 런타임 상태 참고

- dispatcher 제공 상태: `.pipeline/runs/20260522T074442Z-p9631/status.json`
- run_id: `20260522T074442Z-p9631`
- runtime_state: `RUNNING`
- automation_health: `recovering`
- automation_next_action: `retrying`
- active_control: `.pipeline/implement_handoff.md#2131 implement`
- turn_state: `IDLE`
- active_round: `VERIFY_PENDING`
- 이 verify round에서는 lane-local `status --json`, `doctor --json`, `tmux` 결과를 런타임 liveness 권위로 사용하지 않았습니다.

## 이전 관찰과의 관계

- `verify/5/22/2026-05-22-live-claude-trigger-4-restart-observation.md`는 trigger-4 재시작 관찰이 `BLOCKED_BY_PRECONDITION`임을 기록했습니다.
- 이번 code fix는 그 선행조건 문제를 직접 해결하지 않고, wrapper가 신호로 종료될 때 stream finish 호출을 빠뜨리는 경로를 줄인 것입니다.

## 남은 리스크

- `_WrapperEmitter.finish_stream()`의 텍스트 모드 완료 이벤트 의미는 이번 slice에서 바뀌지 않았습니다. 따라서 `finish_stream()` 호출 보장과 `TASK_DONE` 이벤트 보장은 아직 같은 것이 아닙니다.
- Claude lane이 실제 enabled/active 상태에서 trigger work를 수신하는지는 이번 verify에서 live로 재관찰하지 않았습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일이나 broad runtime smoke는 실행하지 않았습니다. 변경 범위가 `_lane_wrapper()` 신호 종료 경로와 focused unit test에 한정되어 좁은 검증만 수행했습니다.
- 기존 working tree에는 CONTROL_SEQ 2129 관련 미커밋 변경과 여러 untracked `work/`, `verify/` 기록이 남아 있으며, 이번 verify에서 되돌리지 않았습니다.
