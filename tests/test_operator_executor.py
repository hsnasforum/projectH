import os
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

from core.operator_executor import execute_operator_action


class TestExecuteOperatorAction(unittest.TestCase):
    def test_local_file_edit_returns_preview(self) -> None:
        content = "\n".join(f"line {i}" for i in range(1, 16))
        with NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = execute_operator_action(
                {"action_kind": "local_file_edit", "target_id": tmp_path}
            )
            self.assertEqual(result["action_kind"], "local_file_edit")
            self.assertEqual(result["target_id"], tmp_path)
            preview_lines = result["preview"].splitlines()
            self.assertEqual(len(preview_lines), 10)
            self.assertEqual(preview_lines[0], "line 1")
        finally:
            os.unlink(tmp_path)

    def test_local_file_edit_writes_to_disk(self) -> None:
        with NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False) as f:
            f.write("original")
            tmp_path = f.name
        try:
            record = {
                "action_kind": "local_file_edit",
                "target_id": tmp_path,
                "content": "updated content",
            }
            result = execute_operator_action(record)
            self.assertTrue(result.get("written"))
            self.assertIn("파일 쓰기 완료", result.get("preview", ""))
            with open(tmp_path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "updated content")
        finally:
            os.unlink(tmp_path)

    def test_local_file_edit_backup_on_reversible_write(self) -> None:
        with NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False) as f:
            f.write("original backup test")
            tmp_path = f.name
        backup_path = None
        try:
            record = {
                "action_kind": "local_file_edit",
                "target_id": tmp_path,
                "content": "new content",
                "is_reversible": True,
            }
            result = execute_operator_action(record)
            self.assertTrue(result.get("written"))
            backup_path = result.get("backup_path")
            self.assertIsNotNone(backup_path, "backup_path should be set when is_reversible=True")
            with open(backup_path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "original backup test")
            with open(tmp_path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "new content")
        finally:
            os.unlink(tmp_path)
            if backup_path and os.path.exists(backup_path):
                os.unlink(backup_path)

    def test_local_file_edit_no_backup_when_not_reversible(self) -> None:
        with NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False) as f:
            f.write("original")
            tmp_path = f.name
        try:
            record = {
                "action_kind": "local_file_edit",
                "target_id": tmp_path,
                "content": "overwritten",
                "is_reversible": False,
            }
            result = execute_operator_action(record)
            self.assertTrue(result.get("written"))
            self.assertNotIn("backup_path", result)
        finally:
            os.unlink(tmp_path)

    def test_local_file_edit_rollback_restores_content(self) -> None:
        from core.operator_executor import rollback_operator_action
        with NamedTemporaryFile(mode="w", suffix=".txt", dir=".", delete=False) as f:
            f.write("original for rollback test")
            tmp_path = f.name
        backup_path = None
        try:
            write_record = {
                "action_kind": "local_file_edit",
                "target_id": tmp_path,
                "content": "updated content",
                "is_reversible": True,
            }
            write_result = execute_operator_action(write_record)
            self.assertTrue(write_result.get("written"))
            backup_path = write_result.get("backup_path")
            self.assertIsNotNone(backup_path)
            rollback_record = {
                "action_kind": "local_file_edit",
                "target_id": tmp_path,
                "backup_path": backup_path,
            }
            rollback_result = rollback_operator_action(rollback_record)
            self.assertTrue(rollback_result.get("restored"))
            with open(tmp_path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "original for rollback test")
        finally:
            os.unlink(tmp_path)
            if backup_path and os.path.exists(backup_path):
                os.unlink(backup_path)

    def test_rollback_missing_backup_returns_error(self) -> None:
        from core.operator_executor import rollback_operator_action
        result = rollback_operator_action({
            "action_kind": "local_file_edit",
            "target_id": str(Path.cwd() / "nonexistent_target_for_test.txt"),
            "backup_path": str(Path.cwd() / "nonexistent_backup_for_test.txt"),
        })
        self.assertFalse(result.get("restored"))
        self.assertIn("백업 파일 없음", result.get("error", ""))

    def test_unsupported_kind_raises(self) -> None:
        with self.assertRaises(ValueError):
            execute_operator_action({"action_kind": "shell_execute", "target_id": "/tmp/x"})

    def test_missing_target_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            execute_operator_action({"action_kind": "local_file_edit", "target_id": ""})

    def test_missing_file_returns_not_found(self) -> None:
        target = str(Path.cwd() / "nonexistent_test_file_verify_xyz.txt")
        result = execute_operator_action(
            {"action_kind": "local_file_edit", "target_id": target}
        )
        self.assertIn("파일 없음", result["preview"])

    def test_local_file_edit_path_restriction(self) -> None:
        with self.assertRaises(ValueError):
            execute_operator_action({
                "action_kind": "local_file_edit",
                "target_id": "/etc/passwd",
            })

    def test_rollback_path_restriction(self) -> None:
        from core.operator_executor import rollback_operator_action
        with self.assertRaises(ValueError):
            rollback_operator_action({
                "action_kind": "local_file_edit",
                "target_id": "/etc/passwd",
                "backup_path": str(Path.cwd() / "backup" / "operator" / "some.txt"),
            })


if __name__ == "__main__":
    unittest.main()
