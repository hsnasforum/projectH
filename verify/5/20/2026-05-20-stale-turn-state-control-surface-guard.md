STATUS: verified
WORK: work/5/20/2026-05-20-stale-turn-state-control-surface-guard.md
CONTROL_SEQ: 2032

# 검증 기록

## 요약

`stale turn-state control surface guard` 작업은 검증 기준을 충족했습니다.
실제 `.pipeline` control slot이 없을 때 오래된 `turn_state.json`의
`OPERATOR_WAIT` / `operator_request.md#2031` mirror가 active control과
`operator_boundary` progress로 되살아나지 않도록 한 변경을 확인했습니다.

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-stale-turn-state-control-surface-guard.md`
- `verify/5/20/2026-05-20-stale-turn-state-control-surface-guard.md`

## 확인한 대상

- `pipeline_runtime/supervisor.py`
  - `_write_status()`가 active control slot이 없을 때 `turn_state.json`에서 active control snapshot을 fallback으로 만들지 않는지 확인했습니다.
  - `_surface_turn_state_for_missing_control()`이 control slot 없음 + 사라진 operator control mirror를 `IDLE`과 빈 active control로 정규화하는지 확인했습니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - no-control-slot + stale `OPERATOR_WAIT` mirror 회귀 테스트가 추가된 것을 확인했습니다.
  - 실제 `operator_request.md`가 존재하는 기존 operator-wait 표면 보존 테스트를 함께 재실행했습니다.
- `RUNTIME_STATUS_AT_DISPATCH`
  - dispatcher 기준 runtime은 `RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control은 `.pipeline/implement_handoff.md#2032 implement`, active round는 `VERIFY_PENDING`이었습니다.

## 실행한 검증

- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_ignores_missing_operator_control_from_stale_turn_state tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_codex_task_hint_during_operator_wait`
  - 결과: PASS. 2개 테스트 모두 통과했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py work/5/20/2026-05-20-stale-turn-state-control-surface-guard.md`
  - 결과: PASS.

## 실행하지 않은 검증

- Playwright/e2e, 전체 unittest, long soak, socket-bound smoke
  - 이유: 이번 변경은 browser-visible behavior가 아니라 supervisor status surface의 좁은 회귀 방지입니다.
- lane-local `status --json`, `doctor --json`, tmux 접근
  - 이유: 지시에서 dispatcher의 `RUNTIME_STATUS_AT_DISPATCH`를 runtime liveness 기준으로 삼도록 했고, lane-local tmux/session 접근 충돌은 비권위 신호로 제한했습니다.
- commit, push, PR, merge, release
  - 이유: 현 verify/handoff 범위 밖이며 publication boundary입니다.

## 판정

- `work/5/20/2026-05-20-stale-turn-state-control-surface-guard.md`의 핵심 주장은 현재 코드와 테스트로 뒷받침됩니다.
- active control slot이 없을 때 stale turn-state control leakage를 status surface에서 제거하는 경로는 회귀 테스트로 보호됩니다.
- 실제 operator control file이 존재하는 경우의 `OPERATOR_WAIT` 표면은 인접 테스트로 보존됨을 확인했습니다.

## 남은 리스크

- `pipeline_runtime/supervisor.py`와 `tests/test_pipeline_runtime_supervisor.py`에는 이번 라운드 이전부터 있던 다른 runtime/local-socket/task-hint 관련 dirty 변경이 함께 남아 있습니다. 이번 검증은 stale turn-state control leakage guard 범위만 판정했습니다.
- active `implement_handoff`, `advisory_request`, `advisory_advice` 전반을 한 번에 다시 검증하지는 않았습니다. 이번 변경은 parse된 control slot이 있으면 turn-state 정규화를 건너뛰는 방식이라 핵심 위험은 낮지만, 다음 안전한 local slice에서 active control family 보존 회귀를 더 촘촘히 묶을 수 있습니다.
