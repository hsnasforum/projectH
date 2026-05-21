STATUS: verified
WORK: work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-reviewed-memory-mutation-identity-no-socket-truth-bundle.md
NEXT_CONTROL_SEQ: 2024
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`의
주장은 현재 코드와 일치합니다. `WatcherDispatchQueue.dispatch()`는
`require_active_control` 즉시 전송 전에 active control mismatch를 구조화된
`lane_input_deferred_dropped`로 drop하고, `watcher_core._check_pipeline_signal_updates()`는
active control이 다른 slot일 때 낮은 seq implement handoff 파일 sig를 fallback으로
소비하지 않습니다.

추가 회귀 테스트와 기존 dispatch mismatch/defer 테스트를 재실행했고 모두 통과했습니다.
이번 검증은 runtime/live socket이나 Playwright release readiness를 주장하지 않습니다.

## 변경 파일

- `verify/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`

## 확인한 대상

- `work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`
- `verify/5/20/2026-05-20-reviewed-memory-mutation-identity-no-socket-truth-bundle.md`
- `watcher_dispatch.py`
- `watcher_core.py`
- `tests/test_watcher_core.py`
- dispatcher-provided runtime status: `.pipeline/implement_handoff.md#2023`, `runtime_state=STARTING`, `automation_health=recovering`

## 실행한 검증

- `python3 -m py_compile watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py pipeline_runtime/turn_arbitration.py pipeline_runtime/control_writers.py tests/test_watcher_core.py`
  - 결과: PASS
- `python3 -m unittest -v tests.test_watcher_core.RollingSignalTransitionTest.test_higher_seq_advisory_keeps_stale_handoff_signal_unconsumed tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_implement_dispatch_drops_when_higher_seq_advisory_is_active tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_new_control_dispatch_replaces_stale_codex_pasted_content tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_flush_pending_logs_structured_control_seq_drift tests.test_watcher_core.BusyLaneNotificationDeferTest.test_implement_handoff_notify_defers_until_prompt_is_ready`
  - 결과: PASS, 5개 테스트 통과
- `git diff --check -- watcher_core.py watcher_dispatch.py tests/test_watcher_core.py work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`
  - 결과: PASS, 출력 없음
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`
  - 결과: PASS. 새 파일 비교라 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 실행하지 않은 검증

- `tmux`, lane-local `status --json`, `doctor --json`는 실행하지 않았습니다.
  - 이유: 이번 verify 지시는 dispatcher status를 runtime liveness authority로 사용하라고 했고, lane-local tmux/session 접근 충돌은 비권위 증거입니다.
- Playwright, controller smoke, full `make e2e-test`, socket-bound HTTP, long soak는 실행하지 않았습니다.
  - 이유: 변경 범위가 watcher/dispatch control arbitration과 단위 회귀 테스트에 한정되며 browser-visible contract나 release readiness를 넓히지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 실행하지 않았습니다.

## 판정

- 최신 `/work`의 구현 주장은 검증되었습니다.
- operator-only decision, approval/truth-sync blocker, immediate safety stop, external publication boundary는 없습니다.
- advisory는 disabled이므로 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- 같은 incident family의 남은 위험은 즉시 dispatch가 아니라 이미 큐에 들어간 stale implement notification이 더 높은 seq advisory control 아래에서 재전송되지 않는지 명시적으로 고정하는 것입니다.

## Council 결정

COUNCIL_DECISION: implement
REASON_CODE: stale_implement_pending_dispatch_after_advisory_control_guard
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2024

EVIDENCE:
- `work/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`
- `verify/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`
- `watcher_dispatch.py`
- `watcher_core.py`
- `tests/test_watcher_core.py`

REJECTED:
- operator_request: 현재 남은 사항은 operator-only boundary가 아니라 local regression guard입니다.
- advisory_request: `ADVISORY_ENABLED=false`이며 다음 조치가 명확합니다.
- publish work: implement lane에 넘길 수 없고 이번 검증은 publication approval이 아닙니다.
- full smoke/release readiness: socket-bound 환경 보류가 남아 있고 이번 변경 범위를 넘어섭니다.

## 남은 리스크

- 전체 dirty tree에는 이전 runtime/reviewed-memory/docs 변경이 많이 섞여 있으며, 이번 검증은 stale implement dispatch guard 경로만 좁게 확인했습니다.
- 다음 implement slice는 stale implement notification의 queued/pending variant를 회귀 테스트로 고정하고, 기존 helper가 이미 처리한다면 코드 변경 없이 테스트 및 `/work` closeout으로 끝내야 합니다.
