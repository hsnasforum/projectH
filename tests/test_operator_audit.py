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
            with NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
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


if __name__ == "__main__":
    unittest.main()
