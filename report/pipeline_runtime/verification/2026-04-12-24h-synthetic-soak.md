# Pipeline Runtime synthetic soak sample

## 요약
- project=/tmp/projecth-pipeline-runtime-synthetic-meoo785o
- session=aip-projecth-pipeline-runtime-synthetic-meoo785o
- mode=experimental
- duration_sec=86400.0
- samples=8674
- state_counts={"RUNNING": 8673, "STARTING": 1}
- degraded_counts={}
- receipt_count=1
- control_change_count=2
- duplicate_dispatch_count=0
- control_mismatch_samples=1
- control_mismatch_max_streak=1
- receipt_pending_samples=0
- orphan_session=False
- broken_seen=False
- workspace_retained=True

## 체크 결과
- `PASS` runtime start
  - started
- `FAIL` synthetic workload produced receipts
  - receipt_count=1
- `PASS` soak completed without BROKEN
  - broken_seen=False
- `PASS` soak completed without DEGRADED
  - degraded_seen=False
- `PASS` duplicate dispatch stayed at zero
  - duplicate_dispatch_count=0
- `PASS` control surface stayed free of persistent mismatch
  - control_mismatch_samples=1, max_streak=1
- `PASS` stop left no orphan session
  - orphan_session=False
