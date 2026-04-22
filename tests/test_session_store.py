import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from core.approval import ApprovalRequest
from storage.session_store import MAX_MESSAGES_PER_SESSION, SessionStore


class SessionStoreTest(unittest.TestCase):
    def test_new_session_uses_expected_schema(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)

            session = store.get_session("demo")

            self.assertEqual(session["schema_version"], "1.0")
            self.assertEqual(session["session_id"], "demo")
            self.assertEqual(session["messages"], [])
            self.assertEqual(session["pending_approvals"], [])
            self.assertEqual(session["permissions"]["web_search"], "disabled")
            self.assertIsNone(session["active_context"])
            self.assertIn("created_at", session)
            self.assertIn("updated_at", session)

    def test_permissions_round_trip(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)

            store.set_permissions("demo", {"web_search": "approval"})
            permissions = store.get_permissions("demo")
            session = store.get_session("demo")

            self.assertEqual(permissions["web_search"], "approval")
            self.assertEqual(session["permissions"]["web_search"], "approval")

    def test_append_message_assigns_id_and_updates_title(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)

            store.append_message("demo", {"role": "user", "text": "문서 요약을 부탁드립니다."})
            session = store.get_session("demo")

            self.assertEqual(len(session["messages"]), 1)
            self.assertIn("message_id", session["messages"][0])
            self.assertEqual(session["title"], "문서 요약을 부탁드립니다.")

    def test_pending_approval_round_trip_and_pop(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)
            approval = ApprovalRequest.create_save_note(
                requested_path="data/notes/demo.md",
                overwrite=False,
                preview_markdown="# Demo",
                source_paths=["/tmp/source.md"],
                note_text="# Demo",
            )

            store.add_pending_approval("demo", approval.to_record())
            fetched = store.get_pending_approval("demo", approval.approval_id)
            popped = store.pop_pending_approval("demo", approval.approval_id)
            session = store.get_session("demo")

            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["approval_id"], approval.approval_id)
            self.assertIsNotNone(popped)
            self.assertEqual(session["pending_approvals"], [])

    def test_operator_action_request_round_trip(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)

            approval_id = store.record_operator_action_request(
                "demo",
                {
                    "action_kind": "local_file_edit",
                    "target_id": "/tmp/x.txt",
                    "audit_trace_required": True,
                    "is_reversible": True,
                },
            )
            fetched = store.get_pending_approval("demo", approval_id)

            self.assertIsInstance(approval_id, str)
            self.assertTrue(approval_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["kind"], "operator_action")
            self.assertEqual(fetched["status"], "pending")
            self.assertEqual(fetched["action_kind"], "local_file_edit")

    def test_active_context_round_trip(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)
            context = {
                "kind": "document",
                "label": "demo.md",
                "source_paths": ["/tmp/demo.md"],
                "summary_hint": "요약",
                "suggested_prompts": ["핵심만 다시 정리해 주세요."],
            }

            store.set_active_context("demo", context)
            fetched = store.get_active_context("demo")

            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["label"], "demo.md")

    def test_list_sessions_returns_latest_first(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)
            store.append_message("older", {"role": "user", "text": "첫 번째"})
            store.append_message("newer", {"role": "user", "text": "두 번째"})

            summaries = store.list_sessions()

            self.assertEqual(summaries[0]["session_id"], "newer")
            self.assertEqual(summaries[1]["session_id"], "older")

    def test_get_session_recovers_from_corrupt_json_file(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)
            session_path = Path(tmp_dir) / "demo.json"
            session_path.write_text("", encoding="utf-8")

            session = store.get_session("demo")

            self.assertEqual(session["session_id"], "demo")
            self.assertEqual(session["messages"], [])
            self.assertTrue(session_path.exists())
            saved = session_path.read_text(encoding="utf-8")
            self.assertIn('"session_id": "demo"', saved)
            quarantine_dir = Path(tmp_dir) / ".quarantine"
            self.assertTrue(quarantine_dir.is_dir())
            backups = list(quarantine_dir.glob("demo.corrupt-*.json"))
            self.assertEqual(len(backups), 1)

    def test_corrupt_json_goes_to_quarantine_directory(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)
            session_path = Path(tmp_dir) / "broken.json"
            session_path.write_text("{invalid json", encoding="utf-8")

            session = store.get_session("broken")

            self.assertEqual(session["session_id"], "broken")
            quarantine_dir = Path(tmp_dir) / ".quarantine"
            self.assertTrue(quarantine_dir.is_dir())
            quarantined = list(quarantine_dir.glob("broken.corrupt-*.json"))
            self.assertEqual(len(quarantined), 1)
            content = quarantined[0].read_text(encoding="utf-8")
            self.assertEqual(content, "{invalid json")

    def test_save_cleans_up_temp_file_on_write_failure(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)
            session = store._default_session("cleanup")

            with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    store._save("cleanup", session)

            tmp_files = list(Path(tmp_dir).glob("*.tmp"))
            self.assertEqual(len(tmp_files), 0, "Temp file should be cleaned up after write failure")

    def test_version_increments_on_each_save(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)

            session = store.get_session("versioned")
            self.assertEqual(session.get("_version", 0), 0)

            store.append_message("versioned", {"role": "user", "text": "first"})
            session = store.get_session("versioned")
            version_after_first = session["_version"]
            self.assertGreaterEqual(version_after_first, 1)

            store.append_message("versioned", {"role": "user", "text": "second"})
            session = store.get_session("versioned")
            version_after_second = session["_version"]
            self.assertGreater(version_after_second, version_after_first)

    def test_messages_trimmed_to_max_limit(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            store = SessionStore(base_dir=tmp_dir)
            over_limit = MAX_MESSAGES_PER_SESSION + 50
            messages = [
                {"role": "user", "text": f"msg-{i}", "message_id": f"id-{i}"}
                for i in range(over_limit)
            ]
            raw_session = store._default_session("big")
            raw_session["messages"] = messages

            session_path = Path(tmp_dir) / "big.json"
            session_path.write_text(
                json.dumps(raw_session, ensure_ascii=False), encoding="utf-8"
            )

            session = store.get_session("big")

            self.assertEqual(len(session["messages"]), MAX_MESSAGES_PER_SESSION)
            self.assertEqual(session["messages"][0]["text"], f"msg-{over_limit - MAX_MESSAGES_PER_SESSION}")
            self.assertEqual(session["messages"][-1]["text"], f"msg-{over_limit - 1}")


if __name__ == "__main__":
    unittest.main()
