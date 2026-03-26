import unittest

from core.approval import ApprovalRequest


class ApprovalRequestTest(unittest.TestCase):
    def test_create_save_note_contains_public_and_private_fields(self) -> None:
        approval = ApprovalRequest.create_save_note(
            requested_path="data/notes/demo.md",
            overwrite=False,
            preview_markdown="# Demo",
            source_paths=["/tmp/source.md"],
            note_text="# Demo\n\ncontent",
        )

        self.assertEqual(approval.kind, "save_note")
        self.assertTrue(approval.approval_id.startswith("approval-"))
        self.assertEqual(approval.to_public_dict()["requested_path"], "data/notes/demo.md")
        self.assertNotIn("note_text", approval.to_public_dict())

    def test_from_record_restores_full_request(self) -> None:
        original = ApprovalRequest.create_save_note(
            requested_path="data/notes/demo.md",
            overwrite=True,
            preview_markdown="# Demo",
            source_paths=["/tmp/source.md"],
            note_text="# Demo\n\ncontent",
        )

        restored = ApprovalRequest.from_record(original.to_record())

        self.assertEqual(restored.approval_id, original.approval_id)
        self.assertEqual(restored.note_text, "# Demo\n\ncontent")
        self.assertTrue(restored.overwrite)


if __name__ == "__main__":
    unittest.main()
