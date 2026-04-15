# 2026-04-11 Pipeline Runtime live gate sample 결과

## 실행 명령
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental soak --duration-sec 20 --sample-interval-sec 2 --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-11-live-soak-sample.md`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental fault-check --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-11-live-fault-check.md`

## 결과
- short soak sample: 완료
  - 최신 샘플에서는 `BROKEN` 전이가 없었고 `STARTING` / `RUNNING` 범위에서 유지됐습니다.
  - stale historical `VERIFY_DONE`를 current receipt 대상으로 다시 평가하던 경로를 줄인 뒤 `degraded_counts`가 비어 있는 것을 확인했습니다.
- live fault check: 완료
  - session loss 후 runtime status의 `degraded_reasons`에 `session_missing`가 포함되는 것을 확인했습니다.
  - recoverable lane 강제 종료 후 `recovery_completed` 이벤트가 기록되는 것을 확인했습니다.

## 해석
- harness 자체는 동작합니다.
- 현재 adoption gate를 막는 것은 live fault 재현 불가가 아니라, 아직 실행하지 않은 6h/24h soak입니다.
