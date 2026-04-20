# 2026-04-19 watcher operator alias gate recovery

## 변경 파일
- pipeline_runtime/operator_autonomy.py
- tests/test_watcher_core.py
- tests/test_pipeline_runtime_supervisor.py
- .pipeline/README.md
- .pipeline/operator_request.md

## 사용 skill
- doc-sync: operator stop gate 계약과 compatibility alias 정규화를 `.pipeline/README.md`에 현재 구현 truth로 맞췄습니다.
- work-log-closeout: 이번 라운드 직접 수정 파일, live unstick 조치, 실제 실행한 검증만 기준으로 closeout 형식을 맞췄습니다.

## 변경 이유
- 현재 watcher가 작업을 시작하지 않은 직접 원인은 최신 `.pipeline/operator_request.md`가 `REASON_CODE: gemini_axis_switch_without_exact_slice`, `OPERATOR_POLICY: stop_until_exact_slice_selected`를 사용하고 있었는데, runtime 분류기가 이를 canonical gated next-slice stop으로 해석하지 못하고 `metadata_fallback -> immediate_publish`로 승격한 데 있었습니다.
- 그 결과 current truth가 `OPERATOR_WAIT`로 굳어져 watcher가 implement/follow-up을 시작하지 못했습니다. 이건 실제 operator-only blocker가 아니라 next-slice ambiguity family의 alias 해석 누락이었습니다.

## 핵심 변경
- `pipeline_runtime/operator_autonomy.py`에서 `gemini_axis_switch_without_exact_slice -> slice_ambiguity`, `stop_until_exact_slice_selected -> gate_24h` alias를 정규화하도록 추가했습니다.
- `tests/test_watcher_core.py`에 alias metadata를 가진 `needs_operator` control이 즉시 publish로 떨어지지 않고 `codex_followup` gated path로 남는 회귀 테스트를 추가했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 같은 alias control이 supervisor status에서도 `control.active_control_status=none`, `autonomy.mode=triage`, `operator_policy=gate_24h`로 기록되는 focused regression을 추가했습니다.
- `.pipeline/README.md`에 오래 남은 control slot compatibility alias를 runtime이 canonical gated 값으로 정규화한다는 계약을 짧게 명시했습니다.
- live runtime unstick을 위해 현재 `.pipeline/operator_request.md`도 canonical metadata(`REASON_CODE: slice_ambiguity`, `OPERATOR_POLICY: gate_24h`)로 정규화했습니다.
- 정규화 직후 current run `status.json`은 `autonomy.mode=triage`, `control.active_control_status=none`, `compat.turn_state=CODEX_FOLLOWUP`, verify owner lane `Claude`의 `state=WORKING(note=followup)`로 바뀌어 hard operator stop이 풀린 것을 확인했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py` → 통과
- `python3 -m unittest -v tests.test_watcher_core.TurnResolutionTest.test_fresh_slice_ambiguity_operator_request_routes_to_codex_followup tests.test_watcher_core.TurnResolutionTest.test_next_slice_alias_operator_request_stays_gated tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_slice_ambiguity_operator_stop_for_24h tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_normalizes_next_slice_aliases_to_gated_operator_stop` → Ran 4 tests, OK
- `python3 -m unittest -v tests.test_watcher_core tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_normalizes_next_slice_aliases_to_gated_operator_stop tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_slice_ambiguity_operator_stop_for_24h` → Ran 135 tests, OK
- `cat .pipeline/runs/20260419T113448Z-p40650/status.json` → `autonomy.mode=triage`, `reason_code=slice_ambiguity`, `operator_policy=gate_24h`, `control.active_control_status=none`, `compat.turn_state.state=CODEX_FOLLOWUP`, `active_lane=Claude`, `Claude state=WORKING(note=followup)` 확인
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md .pipeline/operator_request.md` → 통과

## 남은 리스크
- 이번 수정은 false hard stop을 gated triage로 되돌린 것입니다. next-slice ambiguity 자체가 해결된 것은 아니므로, 새 exact handoff를 정하지 않으면 follow-up lane이 다시 같은 family 판단을 할 수 있습니다.
- alias 정규화는 이번에 실제로 관찰된 `gemini_axis_switch_without_exact_slice` / `stop_until_exact_slice_selected`에 한정했습니다. 다른 비정형 wording이 또 생기면 같은 fallback family가 다시 날 수 있습니다.
- current run은 다시 움직이기 시작했지만, 이는 `needs_operator`를 current truth hard stop으로 잘못 publish하던 문제를 바로잡은 결과입니다. 이후 어떤 exact slice로 이어질지는 별도 control selection truth가 필요합니다.
