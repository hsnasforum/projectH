# Pipeline Runtime fault check

## 요약
- source_project=/home/xpdlqj/code/projectH
- project=/tmp/projecth-pipeline-runtime-synthetic-zz3ovrbk
- session=aip-projecth-pipeline-runtime-synthetic-zz3ovrbk
- mode=experimental
- workspace_retained=False
- workspace_cleanup=background_delete_requested(pid=277589)

## 체크 결과
- `PASS` receipt manifest mismatch degraded precedence
  - runtime_state=DEGRADED, reasons=["receipt_manifest:job-fault-manifest:artifact_hash_mismatch"]
- `PASS` active lane auth failure degraded precedence
  - runtime_state=DEGRADED, reasons=["claude_auth_login_required"]
- `PASS` runtime start
  - started
- `PASS` status surface ready
  - wait_sec=2.7, {"active_round": {"state": ""}, "automation_health": "ok", "automation_incident_family": "", "automation_next_action": "continue", "automation_reason_code": "", "control": {"active_control_status": "none"}, "lanes": [{"attachable": true, "last_event_at": "2026-04-21T07:56:22.509825Z", "last_heartbeat_at": "2026-04-21T07:56:22.423386Z", "name": "Claude", "note": "prompt_visible", "pid": 275154, "state": "READY"}, {"attachable": true, "last_event_at": "2026-04-21T07:56:22.518754Z", "last_heartbeat_at": "2026-04-21T07:56:22.423945Z", "name": "Codex", "note": "prompt_visible", "pid": 275178, "state": "READY"}, {"attachable": true, "last_event_at": "2026-04-21T07:56:22.624598Z", "last_heartbeat_at": "2026-04-21T07:56:22.542889Z", "name": "Gemini", "note": "prompt_visible", "pid": 275204, "state": "READY"}], "runtime_state": "RUNNING", "watcher": {"alive": true, "pid": 275270}}
- `PASS` session loss degraded
  - runtime_state=DEGRADED, reason=session_missing, reasons=["session_missing"], secondary_recovery_failures=[], session_recovery={"recovery_expected": true, "event_observed": true, "event_type": "session_recovery_completed", "attempt": 1, "result": "recreated", "error": ""}
- `PASS` runtime stop after session loss
  - stopped
- `PASS` runtime restart
  - started
- `PASS` recoverable lane pid observed
  - lane=Claude, pid=277326
- `PASS` lane recovery
  - {"seq": 11, "ts": "2026-04-21T07:56:29.805748Z", "run_id": "20260421T075628Z-p276607", "event_type": "recovery_completed", "source": "supervisor", "payload": {"lane": "Claude", "attempt": 1, "result": "restarted"}}
