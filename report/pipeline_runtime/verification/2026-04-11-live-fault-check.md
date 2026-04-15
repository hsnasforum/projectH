# Pipeline Runtime live fault check

## 요약
- project=/home/xpdlqj/code/projectH
- session=aip-projectH
- mode=experimental

## 체크 결과
- `PASS` runtime start
  - started
- `PASS` status surface ready
  - runtime_state=STARTING
- `PASS` session loss degraded
  - runtime_state=DEGRADED, reason=claude_recovery_failed, reasons=["claude_recovery_failed", "session_missing"]
- `PASS` runtime stop after session loss
  - stopped
- `PASS` runtime restart
  - started
- `PASS` recoverable lane pid observed
  - lane=Claude, pid=465016
- `PASS` lane recovery
  - {"seq": 7, "ts": "2026-04-10T19:41:24.413472Z", "run_id": "20260410T194123Z-p464894", "event_type": "recovery_completed", "source": "supervisor", "payload": {"lane": "Claude", "attempt": 1, "result": "restarted"}}
