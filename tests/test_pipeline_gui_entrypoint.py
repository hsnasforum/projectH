from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ENTRYPOINT_PATH = Path(__file__).resolve().parent.parent / "pipeline-gui.py"


class PipelineGuiEntrypointTest(unittest.TestCase):
    def _load_entrypoint(
        self,
        *,
        sys_path: list[str],
        cwd: Path,
        meipass: Path,
        exe_path: Path,
    ) -> tuple[list[str], mock.Mock]:
        spec = importlib.util.spec_from_file_location("_pipeline_gui_entrypoint_test", ENTRYPOINT_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)

        fake_pkg = types.ModuleType("pipeline_gui")
        fake_pkg.__path__ = []
        fake_project = types.ModuleType("pipeline_gui.project")
        fake_project.resolve_project_root = lambda: Path("/tmp/project")
        fake_app = types.ModuleType("pipeline_gui.app")

        class _DummyApp:
            def __init__(self, project: Path) -> None:
                self.project = project

            def run(self) -> None:
                return None

        fake_app.PipelineGUI = _DummyApp

        injected = {
            "pipeline_gui": fake_pkg,
            "pipeline_gui.project": fake_project,
            "pipeline_gui.app": fake_app,
        }
        saved_modules = {name: sys.modules.get(name) for name in injected}
        saved_path = list(sys.path)
        saved_executable = sys.executable
        had_frozen = hasattr(sys, "frozen")
        saved_frozen = getattr(sys, "frozen", None)
        had_meipass = hasattr(sys, "_MEIPASS")
        saved_meipass = getattr(sys, "_MEIPASS", None)

        try:
            sys.modules.update(injected)
            sys.path[:] = list(sys_path)
            sys.executable = str(exe_path)
            setattr(sys, "frozen", True)
            setattr(sys, "_MEIPASS", str(meipass))
            with mock.patch("pathlib.Path.cwd", return_value=cwd), mock.patch("os.chdir") as chdir:
                spec.loader.exec_module(module)
                return list(sys.path), chdir
        finally:
            sys.path[:] = saved_path
            sys.executable = saved_executable
            if had_frozen:
                setattr(sys, "frozen", saved_frozen)
            elif hasattr(sys, "frozen"):
                delattr(sys, "frozen")
            if had_meipass:
                setattr(sys, "_MEIPASS", saved_meipass)
            elif hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")
            for name, old in saved_modules.items():
                if old is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = old

    def test_frozen_entrypoint_strips_shadow_source_roots_and_chdirs_to_exe_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_root = root / "projectH"
            repo_root.mkdir()
            (repo_root / "pipeline_gui").mkdir()
            (repo_root / "storage").mkdir()
            other_root = root / "other"
            other_root.mkdir()
            meipass = root / "_MEI12345"
            (meipass / "_data").mkdir(parents=True)
            exe_dir = root / "Desktop"
            exe_dir.mkdir()
            exe_path = exe_dir / "pipeline-gui.exe"

            new_path, chdir = self._load_entrypoint(
                sys_path=["", str(repo_root), str(other_root)],
                cwd=repo_root,
                meipass=meipass,
                exe_path=exe_path,
            )

        self.assertEqual(new_path[0], str((meipass / "_data").resolve()))
        self.assertEqual(new_path[1], str(meipass.resolve()))
        self.assertNotIn(str(repo_root), new_path)
        self.assertIn(str(other_root), new_path)
        chdir.assert_called_once_with(exe_dir.resolve())

    def test_frozen_entrypoint_strips_powershell_provider_prefixed_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_root = root / "projectH"
            repo_root.mkdir()
            (repo_root / "pipeline_gui").mkdir()
            meipass = root / "_MEI12345"
            (meipass / "_data").mkdir(parents=True)
            exe_dir = root / "Desktop"
            exe_dir.mkdir()
            exe_path = exe_dir / "pipeline-gui.exe"
            provider_prefixed = f"Microsoft.PowerShell.Core\\FileSystem::{repo_root}"

            new_path, _chdir = self._load_entrypoint(
                sys_path=[provider_prefixed],
                cwd=repo_root,
                meipass=meipass,
                exe_path=exe_path,
            )

        self.assertEqual(new_path[:2], [str((meipass / "_data").resolve()), str(meipass.resolve())])
        self.assertNotIn(provider_prefixed, new_path)


if __name__ == "__main__":
    unittest.main()
