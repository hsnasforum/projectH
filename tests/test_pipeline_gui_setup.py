from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_gui import setup as setup_module


class PipelineGuiSetupTest(unittest.TestCase):
    def test_soft_warnings_include_token_runtime_assets(self) -> None:
        labels = [label for label, _check_type, _target in setup_module._SOFT_WARNINGS]
        self.assertIn("token_collector.py", labels)
        self.assertIn("token_schema.sql", labels)

    def test_check_soft_warnings_reports_missing_token_runtime_assets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            missing_targets = {"token_collector.py", "token_schema.sql"}

            def _fake_exists(_base: Path, rel: str) -> bool:
                return rel not in missing_targets

            with mock.patch.object(setup_module, "_file_exists", side_effect=_fake_exists):
                warnings = setup_module._check_soft_warnings(project)

        self.assertIn("token_collector.py", warnings)
        self.assertIn("token_schema.sql", warnings)

    def test_file_exists_accepts_flattened_frozen_token_runtime_assets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle_root = Path(td)
            app_root = bundle_root / "_data"
            app_root.mkdir(parents=True, exist_ok=True)
            script = bundle_root / "token_collector.py"
            script.write_text("# stub\n", encoding="utf-8")
            with (
                mock.patch.object(setup_module, "APP_ROOT", app_root),
                mock.patch.object(setup_module, "resolve_packaged_file", return_value=script),
            ):
                self.assertTrue(setup_module._file_exists(app_root, "token_collector.py"))


if __name__ == "__main__":
    unittest.main()
