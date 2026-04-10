from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_gui import platform as platform_module


class PipelineGuiPlatformTest(unittest.TestCase):
    def test_resolve_packaged_file_prefers_meipass_data_then_flattened(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            meipass = root / "_MEI12345"
            (meipass / "_data").mkdir(parents=True, exist_ok=True)
            preferred = meipass / "_data" / "token_collector.py"
            fallback = meipass / "token_collector.py"
            preferred.write_text("# packaged\n", encoding="utf-8")
            fallback.write_text("# flattened\n", encoding="utf-8")
            with mock.patch.object(platform_module.sys, "_MEIPASS", str(meipass), create=True):
                resolved = platform_module.resolve_packaged_file("token_collector.py")
        self.assertEqual(resolved, preferred)

    def test_normalize_token_runtime_asset_path_collapses_duplicate_data_segments(self) -> None:
        path = Path("C:/Users/test/AppData/Local/Temp/_MEI12345/_data/_data/token_collector.py")
        normalized = platform_module._normalize_token_runtime_asset_path(path)
        self.assertEqual(
            str(normalized).replace("\\", "/"),
            "C:/Users/test/AppData/Local/Temp/_MEI12345/_data/token_collector.py",
        )

    def test_token_runtime_candidates_do_not_duplicate_data_segment_for_frozen_root(self) -> None:
        frozen_root = Path("C:/Users/test/AppData/Local/Temp/_MEI12345/_data")
        candidates = platform_module._token_runtime_asset_candidates("token_collector.py", frozen_root)
        rendered = [str(path).replace("\\", "/") for path in candidates]
        self.assertIn("C:/Users/test/AppData/Local/Temp/_MEI12345/_data/token_collector.py", rendered)
        self.assertNotIn("C:/Users/test/AppData/Local/Temp/_MEI12345/_data/_data/token_collector.py", rendered)

    def test_ensure_staged_runtime_root_copies_runtime_assets_into_project_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source_root = Path(td) / "bundle" / "_data"
            source_root.mkdir(parents=True, exist_ok=True)
            for rel in platform_module._RUNTIME_STAGE_REQUIRED:
                target = source_root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(rel, encoding="utf-8")
            dest_root = Path(td) / "wsl-share" / "gui-runtime" / "_data"

            def _fake_resolve(name: str) -> Path:
                return source_root / name

            with (
                mock.patch.object(platform_module, "resolve_packaged_file", side_effect=_fake_resolve),
                mock.patch.object(platform_module, "_wsl_to_windows_unc", return_value=dest_root),
            ):
                platform_module._STAGED_RUNTIME_KEYS.clear()
                staged = platform_module.ensure_staged_runtime_root(Path("/home/test/project"))
                self.assertEqual(str(staged).replace("\\", "/"), "/home/test/project/.pipeline/gui-runtime/_data")
                self.assertTrue((dest_root / "start-pipeline.sh").exists())
                self.assertTrue((dest_root / "token_collector.py").exists())
                self.assertTrue((dest_root / "token_usage_shared.py").exists())
                self.assertTrue((dest_root / "token_dashboard_shared.py").exists())

    def test_resolve_project_runtime_file_uses_staged_runtime_root_for_windows_frozen(self) -> None:
        with (
            mock.patch.object(platform_module, "IS_WINDOWS", True),
            mock.patch.object(platform_module.sys, "frozen", True, create=True),
            mock.patch.object(
                platform_module,
                "ensure_staged_runtime_root",
                return_value=Path("/home/test/project/.pipeline/gui-runtime/_data"),
            ) as stage_mock,
        ):
            resolved = platform_module.resolve_project_runtime_file(Path("/home/test/project"), "token_collector.py")

        stage_mock.assert_called_once_with(Path("/home/test/project"))
        self.assertEqual(
            str(resolved).replace("\\", "/"),
            "/home/test/project/.pipeline/gui-runtime/_data/token_collector.py",
        )

    def test_ensure_staged_runtime_root_refreshes_when_source_asset_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source_root = Path(td) / "bundle" / "_data"
            source_root.mkdir(parents=True, exist_ok=True)
            for rel in platform_module._RUNTIME_STAGE_REQUIRED:
                target = source_root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"v1:{rel}", encoding="utf-8")
            dest_root = Path(td) / "wsl-share" / "gui-runtime" / "_data"

            def _fake_resolve(name: str) -> Path:
                return source_root / name

            with (
                mock.patch.object(platform_module, "resolve_packaged_file", side_effect=_fake_resolve),
                mock.patch.object(platform_module, "_wsl_to_windows_unc", return_value=dest_root),
            ):
                platform_module._STAGED_RUNTIME_KEYS.clear()
                platform_module.ensure_staged_runtime_root(Path("/home/test/project"))
                self.assertEqual(
                    (dest_root / "watcher_core.py").read_text(encoding="utf-8"),
                    "v1:watcher_core.py",
                )

                (source_root / "watcher_core.py").write_text("v2:watcher_core.py", encoding="utf-8")
                platform_module.ensure_staged_runtime_root(Path("/home/test/project"))

                self.assertEqual(
                    (dest_root / "watcher_core.py").read_text(encoding="utf-8"),
                    "v2:watcher_core.py",
                )

    def test_wsl_wrap_passes_args_directly_without_nested_bash_quoting(self) -> None:
        with mock.patch.object(platform_module, "IS_WINDOWS", True):
            wrapped = platform_module._wsl_wrap(["bash", "-lc", "echo 'hello' && true"])
        self.assertEqual(
            wrapped,
            ["wsl.exe", "-d", platform_module.WSL_DISTRO, "--", "bash", "-lc", "echo 'hello' && true"],
        )

    def test_path_exists_uses_wsl_test_for_posix_project_paths_on_windows(self) -> None:
        target = Path("/home/test/project/.pipeline/config/agent_profile.json")
        with (
            mock.patch.object(platform_module, "IS_WINDOWS", True),
            mock.patch.object(platform_module, "_run", return_value=(0, "")) as run_mock,
        ):
            self.assertTrue(platform_module.path_exists(target))
        run_mock.assert_called_once_with(["test", "-e", "/home/test/project/.pipeline/config/agent_profile.json"], timeout=platform_module.FILE_QUERY_TIMEOUT)

    def test_read_json_path_reads_wsl_json_via_run_on_windows(self) -> None:
        target = Path("/home/test/project/.pipeline/config/agent_profile.json")
        payload = {"schema_version": 1, "selected_agents": ["Claude"]}
        with (
            mock.patch.object(platform_module, "IS_WINDOWS", True),
            mock.patch.object(platform_module, "_run", side_effect=[(0, ""), (0, json.dumps(payload, ensure_ascii=False))]),
        ):
            data = platform_module.read_json_path(target)
        self.assertEqual(data, payload)

    def test_atomic_write_json_path_writes_to_wsl_path_via_stdin(self) -> None:
        target = Path("/home/test/project/.pipeline/config/agent_profile.json")
        payload = {"schema_version": 1, "selected_agents": ["Claude"]}
        completed = mock.Mock()
        completed.returncode = 0
        with (
            mock.patch.object(platform_module, "IS_WINDOWS", True),
            mock.patch.object(platform_module, "_hidden_subprocess_kwargs", return_value={}),
            mock.patch("pipeline_gui.platform.subprocess.run", return_value=completed) as run_mock,
        ):
            platform_module.atomic_write_json_path(target, payload)
        args, kwargs = run_mock.call_args
        command = args[0]
        self.assertEqual(command[:5], ["wsl.exe", "-d", platform_module.WSL_DISTRO, "--", "bash"])
        self.assertEqual(kwargs["input"], json.dumps(payload, ensure_ascii=False, indent=2))
        self.assertTrue(kwargs["check"])


if __name__ == "__main__":
    unittest.main()
