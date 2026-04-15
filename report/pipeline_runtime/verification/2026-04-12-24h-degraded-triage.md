# 2026-04-12 24h soak degraded triage

## 요약
- 24시간 soak 보고서에서 `broken_seen=False`였지만 `DEGRADED 54회`가 함께 관측됐습니다.
- degraded reason은 모두 `receipt_manifest:<job_id>:missing_manifest_path` 패턴이었습니다.
- 원인은 `watcher_core`의 feedback-complete 경로가 `VERIFY_DONE(passed_by_feedback)`로 닫히면서도 `verify_manifest_path`를 남기지 않던 contract 누락이었습니다.
- 추가로 `pipeline_runtime.receipts`는 manifest `role=="verify"`만 허용하고 있었는데, watcher 쪽 manifest contract는 `slot_verify`를 사용하고 있어 role contract도 어긋나 있었습니다.

## 확인한 사실
- 24시간 보고서 [2026-04-11-24h-soak.md](/home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-11-24h-soak.md) 에 `state_counts={"DEGRADED": 54, "RUNNING": 2979, "STARTING": 1}` 이 기록돼 있었습니다.
- 루트 [.pipeline/state](/home/xpdlqj/code/projectH/.pipeline/state) 의 `VERIFY_DONE` job state들은 `verify_manifest_path=""` 인 채 저장돼 있었습니다.
- 현재 soak run의 [events.jsonl](/home/xpdlqj/code/projectH/.pipeline/runs/20260411T051546Z-p737404/events.jsonl) 에서 degraded enter/clear가 각 control 전이 직후 반복됐고, 모두 같은 `missing_manifest_path` 계열이었습니다.

## 적용한 수정
- [watcher_core.py](/home/xpdlqj/code/projectH/watcher_core.py) 의 feedback-complete 경로에서 synthetic verify manifest를 `.pipeline/manifests/<job_id>/round-<n>.verify.json` 으로 기록하고 `job.verify_manifest_path` 를 채우도록 수정했습니다.
- [pipeline_runtime/receipts.py](/home/xpdlqj/code/projectH/pipeline_runtime/receipts.py) 는 manifest role로 `verify` 와 `slot_verify` 를 모두 허용하도록 맞췄습니다.
- [scripts/pipeline_runtime_gate.py](/home/xpdlqj/code/projectH/scripts/pipeline_runtime_gate.py) 는 `BROKEN` 뿐 아니라 `DEGRADED` 샘플도 soak 실패로 판정하도록 바꿨습니다.
- [tests/test_watcher_core.py](/home/xpdlqj/code/projectH/tests/test_watcher_core.py), [tests/test_pipeline_runtime_supervisor.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_supervisor.py), [tests/test_pipeline_runtime_gate.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_gate.py) 에 회귀 테스트를 추가/보강했습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/receipts.py scripts/pipeline_runtime_gate.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_gate.py`
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_gate`
- `python3 -m unittest -v tests.test_watcher_core.LiveSessionEscalationTest`

## 남은 사항
- 이번 수정은 24시간 soak의 degraded 원인을 코드상으로 막는 조치입니다.
- 이미 끝난 기존 24시간 보고서는 historical fact로 유지해야 하므로, 채택 판단용 24시간 soak는 수정본으로 다시 실행해야 합니다.
- 넓은 런타임 묶음 전체 재실행에서는 `tests.test_pipeline_gui_app.PipelineGuiAppTest.test_setup_refresh_downgrades_cached_applied_state_when_active_profile_is_missing` 1건이 순서 의존적으로 한 번 실패했고, 단독 재실행은 통과했습니다. 현재 triage 범위와는 분리된 flaky setup-mode 테스트로 보입니다.
