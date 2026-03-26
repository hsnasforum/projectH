import unittest
from pathlib import Path

from tools.path_utils import normalize_local_path_input


class PathUtilsTest(unittest.TestCase):
    def test_normalizes_windows_drive_path_with_backslashes(self) -> None:
        normalized = normalize_local_path_input(r"C:\Users\HS\Desktop\demo.txt")

        self.assertEqual(normalized, Path("/mnt/c/Users/HS/Desktop/demo.txt"))

    def test_normalizes_windows_drive_path_with_forward_slashes(self) -> None:
        normalized = normalize_local_path_input("D:/docs/demo.txt")

        self.assertEqual(normalized, Path("/mnt/d/docs/demo.txt"))

    def test_normalizes_windows_unc_wsl_path(self) -> None:
        normalized = normalize_local_path_input(r"\\wsl.localhost\Ubuntu\home\xpdlqj\code\projectH\README.md")

        self.assertEqual(normalized, Path("/home/xpdlqj/code/projectH/README.md"))

    def test_leaves_regular_linux_path_unchanged(self) -> None:
        normalized = normalize_local_path_input("/mnt/c/Users/HS/Desktop/demo.txt")

        self.assertEqual(normalized, Path("/mnt/c/Users/HS/Desktop/demo.txt"))


if __name__ == "__main__":
    unittest.main()
