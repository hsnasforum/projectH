from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WindowsLaunchersContractTest(unittest.TestCase):
    def test_cmd_launchers_separate_launcher_source_from_target_project(self) -> None:
        for name, script_name in (
            ("pipeline-gui.cmd", "pipeline-gui.py"),
            ("pipeline-tui.cmd", "pipeline-launcher.py"),
        ):
            text = (ROOT / "windows-launchers" / name).read_text(encoding="utf-8")
            self.assertIn("WSL_LAUNCHER_ROOT", text, name)
            self.assertIn('--cd "%WSL_LAUNCHER_ROOT%"', text, name)
            self.assertIn(f"--exec python3 {script_name}", text, name)
            self.assertIn('"%WSL_PROJECT%"', text, name)

    def test_pipeline_gui_spec_matches_staged_runtime_asset_contract(self) -> None:
        text = (ROOT / "windows-launchers" / "pipeline-gui.spec").read_text(encoding="utf-8")
        self.assertIn("('..\\\\_data', '_data')", text)
        self.assertIn("pipeline_gui\\\\token_usage_shared.py", text)
        self.assertIn("pipeline_gui\\\\token_dashboard_shared.py", text)
        self.assertNotIn("('..\\\\_data', '.')", text)


if __name__ == "__main__":
    unittest.main()
