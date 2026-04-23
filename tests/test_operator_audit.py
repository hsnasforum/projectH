import os
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from core.operator_executor import execute_operator_action
from storage.session_store import SessionStore


class TestOperatorAuditTrail(unittest.TestCase):
    def test_end_to_end_audit_trail_with_backup(self) -> None:
        with TemporaryDirectory() as store_dir:
            with NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False) as f:
                f.write("original content for audit test")
                target_path = f.name
            backup_path = None
            try:
                store = SessionStore(base_dir=store_dir)
                session_id = "audit_test_session"

                # 1. Record an operator action request
                action_contract = {
                    "action_kind": "local_file_edit",
                    "target_id": target_path,
                    "content": "updated content",
                    "is_reversible": True,
                    "audit_trace_required": True,
                }
                approval_id = store.record_operator_action_request(session_id, action_contract)

                # 2. Retrieve the pending approval (as agent_loop does after gate passes)
                session = store.get_session(session_id)
                pending = session["pending_approvals"]
                self.assertEqual(len(pending), 1)
                approval_record = pending[0]
                self.assertEqual(approval_record["approval_id"], approval_id)

                # 3. Execute the action (replicates agent_loop post-approval call)
                result = execute_operator_action(approval_record)
                self.assertTrue(result.get("written"))
                backup_path = result.get("backup_path")
                self.assertIsNotNone(backup_path, "backup_path must be set for is_reversible=True")

                # 4. Build and persist the outcome record (mirrors agent_loop logic)
                outcome_record = dict(approval_record)
                outcome_record["status"] = "executed"
                outcome_record["preview"] = result.get("preview", "")
                if "backup_path" in result:
                    outcome_record["backup_path"] = result["backup_path"]
                store.record_operator_action_outcome(session_id, outcome_record)

                # 5. Assert audit trail integrity
                session = store.get_session(session_id)
                history = session["operator_action_history"]
                self.assertEqual(len(history), 1)
                entry = history[0]

                # approval_id matches the original request
                self.assertEqual(entry["approval_id"], approval_id)

                # status is "executed"
                self.assertEqual(entry["status"], "executed")

                # completed_at is a valid ISO timestamp
                completed_at = entry.get("completed_at", "")
                self.assertTrue(completed_at, "completed_at must be present")
                datetime.fromisoformat(completed_at)

                # backup_path points to an existing file with the original content
                self.assertIn("backup_path", entry)
                self.assertTrue(Path(entry["backup_path"]).exists())
                with open(entry["backup_path"], encoding="utf-8") as fh:
                    self.assertEqual(fh.read(), "original content for audit test")

                # content matches the applied update
                self.assertEqual(entry["content"], "updated content")
            finally:
                os.unlink(target_path)
                if backup_path and os.path.exists(backup_path):
                    os.unlink(backup_path)

    def test_rollback_trace_in_history(self) -> None:
        import os
        from core.operator_executor import execute_operator_action, rollback_operator_action

        with TemporaryDirectory() as store_dir:
            store = SessionStore(base_dir=store_dir)
            session_id = "test-rollback-trace-sess"
            target_path = None
            backup_path = None

            with NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False) as f:
                f.write("original content")
                target_path = f.name

            try:
                # Execute: write + backup
                exec_record = {
                    "action_kind": "local_file_edit",
                    "target_id": target_path,
                    "content": "updated content",
                    "is_reversible": True,
                    "approval_id": "test-approval-rollback-trace",
                }
                exec_result = execute_operator_action(exec_record)
                backup_path = exec_result.get("backup_path")
                self.assertIsNotNone(backup_path)

                # Record executed outcome
                executed_outcome = dict(exec_record)
                executed_outcome["status"] = "executed"
                executed_outcome["backup_path"] = backup_path
                store.record_operator_action_outcome(session_id, executed_outcome)

                # Look up from history + rollback
                history_entry = store.get_operator_action_from_history(
                    session_id, "test-approval-rollback-trace"
                )
                self.assertIsNotNone(history_entry)
                self.assertEqual(history_entry["status"], "executed")

                rollback_result = rollback_operator_action(history_entry)
                self.assertTrue(rollback_result.get("restored"))

                # Record rolled_back outcome
                rollback_outcome = dict(history_entry)
                rollback_outcome["status"] = "rolled_back"
                rollback_outcome["restored"] = True
                store.record_operator_action_outcome(session_id, rollback_outcome)

                # Verify history has 2 entries with correct statuses
                data = store.get_session(session_id)
                history = data.get("operator_action_history", [])
                self.assertEqual(len(history), 2)
                self.assertEqual(history[0]["status"], "executed")
                self.assertEqual(history[1]["status"], "rolled_back")
                self.assertTrue(history[1].get("restored"))
            finally:
                if target_path and os.path.exists(target_path):
                    os.unlink(target_path)
                if backup_path and os.path.exists(backup_path):
                    os.unlink(backup_path)


if __name__ == "__main__":
    unittest.main()
