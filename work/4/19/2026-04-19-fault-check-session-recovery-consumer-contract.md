# 2026-04-19 fault-check session recovery consumer contract

## 변경 파일
- 이번 라운드 직접 편집:
  - `tests/test_pipeline_runtime_gate.py`
  - `.pipeline/README.md`
  - `work/4/19/2026-04-19-fault-check-session-recovery-consumer-contract.md`
- 이번 라운드 범위 밖의 기존 dirty worktree:
  - `scripts/pipeline_runtime_gate.py`, `pipeline_runtime/tmux_adapter.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py` (직전 same-family 라운드 누적)
  - watcher/manual-cleanup, controller cozy, runtime docs/tests 등 이 슬라이스와 무관한 기존 편집

## 사용 skill
- `superpowers:using-superpowers`: 세션 시작 시 필수 skill 확인 규칙을 따르기 위해 사용.
- `doc-sync`: `.pipeline/README.md`의 `session loss degraded` consumer 계약 문장을 shipped gate 동작에 맞춰 좁게 동기화하기 위해 사용.
- `work-log-closeout`: 이번 consumer-contract 동기화 라운드의 `/work` 기록을 repo 규약 형식으로 남기기 위해 사용.

## 변경 이유
- 직전 라운드가 `scripts/pipeline_runtime_gate.py`의 `session loss degraded` 체크에 bounded session-recovery terminal event evidence(`data.session_recovery`)를 추가하고, recovery-expected 상황에서 terminal event 부재 시 gate가 실패하도록 계약을 좁혔습니다.
- 그러나 consumer 쪽 truth는 아직 그 변경을 따라오지 못했습니다. `.pipeline/README.md`의 `session loss degraded` payload 문단은 여전히 예전 4필드(`runtime_state` / `representative_reason` / `degraded_reasons` / `secondary_recovery_failures`)만 언급했고, `tests/test_pipeline_runtime_gate.py`의 lifecycle green-path와 CLI sidecar 테스트는 새 `session_recovery` 필드를 pin하지 않고 있었습니다.
- 이번 라운드는 그 consumer-contract drift를 좁게 닫아, 후속 자동화/문서 독자가 새 payload 계약을 shipped gate와 동일하게 읽도록 고정합니다.

## 핵심 변경
- `.pipeline/README.md`의 `session loss degraded` payload 문장을 확장해 `data.session_recovery` 존재, stable 서브필드(`recovery_expected`, `broken_lane_names`, `event_observed`, `event_type`, `attempt`, `result`, `error`, `event`)와 “recovery가 기대됐는데 terminal `session_recovery_completed`/`session_recovery_failed` event가 관측되지 않으면 gate 자체가 실패한다”는 규칙을 명시했습니다. recovery가 기대되지 않은 경로에서도 같은 스키마 키가 빈 기본값으로 유지된다는 점을 같이 적어, 자동화가 detail scraping 없이 match 실패까지 읽을 수 있음을 문서화했습니다.
- `tests/test_pipeline_runtime_gate.py::test_lifecycle_checks_expose_structured_data_on_green_path`에 `session loss degraded` 엔트리의 `data.session_recovery` 서브필드 assertion을 추가했습니다. 이 테스트는 degraded 스냅샷에 BROKEN lane이 없는 green path이므로 `recovery_expected=False`, `broken_lane_names=[]`, `event_observed=False`, `event_type=""`, `attempt=0`, `result=""`, `error=""`, `event={}`이 기본값으로 남는 스키마를 고정합니다.
- `tests/test_pipeline_runtime_gate.py::test_fault_check_cli_writes_markdown_and_json_sidecar_with_structured_checks`의 sample_checks에 새 `session loss degraded` 엔트리를 추가했습니다. representative `session_missing`, `recovery_expected=True`, `broken_lane_names=["Claude"]`, terminal `session_recovery_completed` event(attempt=1, result="recreated") payload를 담아 markdown 출력과 JSON sidecar가 같은 구조를 그대로 유지함을 assertion으로 pin합니다. markdown 쪽도 `PASS session loss degraded`와 `session_recovery=` prefix가 실제로 남는지 확인합니다.
- 이번 라운드는 shipped **gate 동작을 바꾸지 않았습니다**. `scripts/pipeline_runtime_gate.py`는 건드리지 않았으며, 오직 문서/테스트가 기존 shipped 계약을 truthfully pin하도록 좁혔습니다. 따라서 round 성격은 docs/consumer-contract drift closure입니다.

## 검증
- `python3 -m py_compile tests/test_pipeline_runtime_gate.py`
  - 결과: 통과(출력 없음)
- `python3 -m unittest -v tests.test_pipeline_runtime_gate.PipelineRuntimeGateSoakTest.test_lifecycle_checks_expose_structured_data_on_green_path tests.test_pipeline_runtime_gate.PipelineRuntimeGateSoakTest.test_fault_check_cli_writes_markdown_and_json_sidecar_with_structured_checks`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_gate`
  - 결과: `Ran 34 tests`, `OK`
- `git diff --check -- tests/test_pipeline_runtime_gate.py .pipeline/README.md scripts/pipeline_runtime_gate.py`
  - 결과: 출력 없음
- live `python3 scripts/pipeline_runtime_gate.py fault-check ...`와 broad browser suite(`make e2e-test`)는 실행하지 않았습니다. 이번 라운드는 docs/test consumer contract만 좁혔고 gate 동작과 browser 경로는 범위 밖이기 때문입니다.

## 남은 리스크
- README 확장은 현재 shipped gate 계약을 문장으로 고정한 것이며, 앞으로 `session_recovery` 서브필드를 더 추가하거나 삭제하면 같은 라운드에서 이 문단과 테스트를 함께 갱신해야 drift가 반복되지 않습니다.
- CLI sidecar 테스트의 새 `session loss degraded` sample은 `run_fault_check`를 mock으로 치환해 markdown/JSON 직렬화 경로만 검증합니다. 실제 live `fault-check` 실행에서 terminal `session_recovery_*` event가 event budget 안에 관측되는지는 별도 live 단계에서 확인해야 합니다.
- lifecycle green-path 테스트는 degraded 스냅샷에 `lanes` 필드가 없는 경우까지 커버하지만, supervisor가 미래에 lane state 이름을 변경하면 `recovery_expected` 판정과 green-path 기본값이 의도치 않게 바뀔 수 있으므로 해당 변경 라운드에서 이 fixture도 함께 갱신할 필요가 있습니다.
