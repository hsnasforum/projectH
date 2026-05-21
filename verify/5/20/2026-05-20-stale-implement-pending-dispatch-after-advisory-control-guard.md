STATUS: verified
WORK: work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md
NEXT_CONTROL_SEQ: 2025
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`의
주장은 현재 코드와 일치합니다. 최신 `/work`는 runtime source 변경 없이
`WatcherDispatchQueue.flush_pending()`의 기존 active-control mismatch drop 동작을
회귀 테스트로 고정했다고 기록했고, 실제로 pending `implement_handoff.md#2019`
notification이 active `advisory_request.md#2022` 아래에서 전송되지 않고
`lane_input_deferred_dropped`로 제거되는 테스트가 추가되어 있습니다.

이번 검증은 dispatcher-provided runtime status를 권위 surface로 사용했습니다.
file-backed runtime은 `STARTING/recovering/retrying` 상태이므로 live runtime 회복,
socket-bound smoke, release readiness는 주장하지 않습니다.

## 변경 파일

- `verify/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`

## 확인한 대상

- `work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`
- `verify/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`
- `tests/test_watcher_core.py`
- `watcher_dispatch.py`
- dispatcher-provided runtime status: `.pipeline/implement_handoff.md#2024`, `runtime_state=STARTING`, `automation_health=recovering`, `automation_next_action=retrying`

## 실행한 검증

- `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS
- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_flush_pending_drops_stale_implement_when_higher_seq_advisory_is_active tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_flush_pending_logs_structured_control_seq_drift tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_pending_control_path_accepts_legacy_alias_for_same_slot tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_implement_dispatch_drops_when_higher_seq_advisory_is_active`
  - 결과: PASS, 4개 테스트 통과
- `git diff --check -- tests/test_watcher_core.py work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`
  - 결과: PASS, 출력 없음
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`
  - 결과: PASS. 새 파일 비교라 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 실행하지 않은 검증

- `tmux`, lane-local `status --json`, `doctor --json`는 실행하지 않았습니다.
  - 이유: verify 지시는 dispatcher status를 runtime liveness authority로 사용하라고 했고, lane-local tmux/session 접근 충돌은 비권위 증거입니다.
- Playwright, controller smoke, full `make e2e-test`, socket-bound HTTP, long soak는 실행하지 않았습니다.
  - 이유: 변경 범위가 watcher dispatch queue regression test에 한정되고 browser-visible contract나 release readiness를 넓히지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 실행하지 않았습니다.

## 판정

- 최신 `/work`의 구현 주장은 검증되었습니다.
- operator-only decision, approval/truth-sync blocker, immediate safety stop, external publication boundary는 없습니다.
- advisory는 disabled이므로 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- stale implement dispatch incident family는 immediate path와 pending path 회귀가 각각 추가되었습니다. 다음 local slice는 새 미세 예외 추가가 아니라 같은 family의 aggregate guard로 관련 테스트 묶음을 한 번에 확인하고, 빠진 직접 assertion이 있을 때만 보강하는 것이 가장 좁은 current-risk reduction입니다.

## Council 결정

COUNCIL_DECISION: implement
REASON_CODE: stale_implement_dispatch_family_aggregate_guard
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2025

EVIDENCE:
- `work/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`
- `verify/5/20/2026-05-20-stale-implement-pending-dispatch-after-advisory-control-guard.md`
- `verify/5/20/2026-05-20-stale-implement-dispatch-after-advisory-control-guard.md`
- `tests/test_watcher_core.py`
- `watcher_dispatch.py`

REJECTED:
- operator_request: 현재 남은 사항은 operator-only boundary가 아니라 local regression aggregate guard입니다.
- advisory_request: `ADVISORY_ENABLED=false`이며 다음 조치가 명확합니다.
- publish work: implement lane에 넘길 수 없고 이번 검증은 publication approval이 아닙니다.
- another file-local exception branch: 현재 직접 증거는 테스트 aggregate로 닫는 것이 맞으며 새 runtime branch가 필요하다는 실패 증거는 없습니다.

## 남은 리스크

- 전체 dirty tree에는 이전 runtime/reviewed-memory/docs 변경이 많이 섞여 있으며, 이번 검증은 stale implement dispatch pending guard 경로만 좁게 확인했습니다.
- live runtime reload, socket-bound runtime surface, browser-visible behavior는 이번 검증 범위 밖입니다.
- 다음 implement slice는 stale implement dispatch family의 immediate/pending/core mismatch tests를 묶어 aggregate guard로 확인하고, 기존 테스트가 충분하면 code change 없이 `/work` closeout만 남기면 됩니다.
