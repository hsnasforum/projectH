# Pipeline Runtime fault check

## 요약
- source_project=/home/xpdlqj/code/projectH
- project=/tmp/projecth-pipeline-runtime-synthetic-c4obkxvt
- session=aip-projecth-pipeline-runtime-synthetic-c4obkxvt
- mode=experimental
- workspace_retained=False
- workspace_cleanup=background_delete_requested(pid=3128134)

## 체크 결과
- `PASS` runtime start
  - started
- `PASS` status surface ready
  - runtime_state=RUNNING
- `PASS` session loss degraded
  - runtime_state=DEGRADED, reason=claude_recovery_failed, reasons=["claude_recovery_failed", "codex_recovery_failed", "gemini_recovery_failed", "session_missing"]
- `PASS` runtime stop after session loss
  - stopped
- `PASS` runtime restart
  - started
- `PASS` recoverable lane pid observed
  - lane=Claude, pid=3127856
- `PASS` lane recovery
  - {"seq": 7, "ts": "2026-04-15T13:40:57.548875Z", "run_id": "20260415T134056Z-p3127147", "event_type": "recovery_completed", "source": "supervisor", "payload": {"lane": "Claude", "attempt": 1, "result": "restarted"}}
