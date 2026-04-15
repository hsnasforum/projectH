# 2026-04-15 stale operator stop codex followup recovery verification

## 검증 범위
- `watcher_core.py`
- `pipeline_runtime/supervisor.py`
- stale operator stop startup/rolling recovery
- Codex follow-up lane surface

## 실행한 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_watcher_core tests.test_pipeline_runtime_supervisor`
- live runtime restart + status/tail inspection

## 결과
- unit/regression:
  - `tests.test_watcher_core` 62개 통과
  - `tests.test_pipeline_runtime_supervisor` 29개 통과
  - 총 91개 통과
- startup stale-stop recovery:
  - watcher raw event에 `initial_turn=codex_followup`
  - `operator_request_stale_ignored`
  - `codex_control_recovery_notify`
  가 기록됐습니다.
- live status:
  - `runtime_state = RUNNING`
  - `control.active_control_status = none`
  - `compat.turn_state.state = CODEX_FOLLOWUP`
  - lane surface는 `Codex = WORKING`, `note = followup`
- live tail:
  - Codex pane이 stale operator stop control-recovery prompt를 읽고 실제 `Working` 상태로 들어간 것을 확인했습니다.

## 해석
- stale operator stop suppression만 있을 때의 문제는 “truth는 none인데 다음 actor가 없는 공백”이었습니다.
- 이번 수정으로 runtime은 stale stop을 operator wait로 붙잡지 않고, Codex가 다음 control을 다시 고르는 bounded recovery 단계로 자동 이어집니다.
- 따라서 사용자 표면에서도 `READY인데 사실 멈춘 것처럼 보이는` 상태가 아니라, `Codex follow-up working`으로 truthfully 보이게 됐습니다.

## 메모
- 이번 검증은 long soak 채택 근거가 아니라 runtime behavior correction 확인입니다.
- stale stop 이후 Codex가 실제 어떤 control file을 최종 선택하는지는 별도 lane execution 결과로 판단해야 합니다.
