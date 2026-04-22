from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_gui import setup as setup_module


def _write_codex_only_profile(project: Path) -> None:
    profile_path = project / ".pipeline" / "config" / "agent_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "selected_agents": ["Codex"],
                "role_bindings": {"implement": "Codex", "verify": "Codex", "advisory": ""},
                "role_options": {
                    "advisory_enabled": False,
                    "operator_stop_enabled": True,
                    "session_arbitration_enabled": False,
                },
                "mode_flags": {
                    "single_agent_mode": True,
                    "self_verify_allowed": True,
                    "self_advisory_allowed": False,
                },
            }
        ),
        encoding="utf-8",
    )


class PipelineGuiSetupHardBlockerTest(unittest.TestCase):
    def test_hard_blockers_without_active_profile_do_not_require_all_agent_clis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            labels = [item[0] for item in setup_module.hard_blockers_for_project(project)]

        self.assertIn("tmux", labels)
        self.assertIn("python3", labels)
        self.assertNotIn("claude", labels)
        self.assertNotIn("codex", labels)
        self.assertNotIn("gemini", labels)

    def test_hard_blockers_require_only_active_profile_enabled_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            _write_codex_only_profile(project)

            labels = [item[0] for item in setup_module.hard_blockers_for_project(project)]

        self.assertIn("codex", labels)
        self.assertNotIn("claude", labels)
        self.assertNotIn("gemini", labels)

    def test_check_hard_blockers_reports_missing_enabled_agent_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
            _write_codex_only_profile(project)

            def _fake_find(name: str) -> bool:
                return name != "codex"

            with mock.patch.object(setup_module, "_find_cli_bin", side_effect=_fake_find):
                missing = setup_module._check_hard_blockers(project)

        self.assertEqual([item[0] for item in missing], ["codex"])


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

    def test_agents_template_mentions_turbo_lite_wrapper_order(self) -> None:
        template = setup_module._TMPL_AGENTS
        self.assertIn("Turbo-lite Wrappers", template)
        self.assertIn("`onboard-lite`", template)
        self.assertIn("`finalize-lite`", template)
        self.assertIn("`round-handoff`", template)
        self.assertIn("`next-slice-triage`", template)


if __name__ == "__main__":
    unittest.main()
