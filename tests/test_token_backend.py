from __future__ import annotations

import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_gui import backend


class TokenBackendTest(unittest.TestCase):
    def test_run_token_collector_once_uses_unbuffered_python_and_forwards_progress(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            db_path = project / ".pipeline" / "usage" / "usage.db"

            class _Proc:
                def __init__(self) -> None:
                    self.stdout = iter(
                        [
                            '{"event":"progress","phase":"preparing","progress_percent":0}\n',
                            '{"event":"progress","phase":"scanning","progress_percent":50}\n',
                            '{"usage_inserted":3,"pipeline_inserted":0,"progress_percent":100}\n',
                        ]
                    )

                def wait(self) -> int:
                    return 0

            progress: list[dict[str, object]] = []
            with mock.patch.object(backend, "IS_WINDOWS", False), mock.patch.object(
                backend.subprocess,
                "Popen",
                return_value=_Proc(),
            ) as popen_mock:
                summary = backend.run_token_collector_once(
                    project,
                    db_path,
                    since_days=7,
                    progress_callback=progress.append,
                )

            cmd = popen_mock.call_args.args[0]
            self.assertEqual(cmd[0:2], ["python3", "-u"])
            self.assertIn("--progress", cmd)
            self.assertEqual(summary["usage_inserted"], 3)
            self.assertEqual([item["phase"] for item in progress], ["preparing", "scanning"])

    def test_pipeline_stop_raises_when_script_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            with mock.patch.object(
                backend.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    args=["bash", "stop-pipeline.sh"],
                    returncode=1,
                    stdout=b"",
                    stderr=b"boom\n",
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "stop-pipeline.sh failed: boom"):
                    backend.pipeline_stop(project, "aip-test")

    def test_token_collector_start_prefers_tmux_when_session_alive(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / ".pipeline" / "usage").mkdir(parents=True)
            with (
                mock.patch.object(backend, "tmux_alive", return_value=True),
                mock.patch.object(backend, "token_collector_alive", return_value=(True, 4321)),
                mock.patch.object(
                    backend,
                    "_run",
                    side_effect=[
                        (0, ""),
                        (0, "%77"),
                        (0, "4321"),
                    ],
                ) as run_mock,
            ):
                result = backend.token_collector_start(project)
            self.assertEqual(result, "token collector started")
            self.assertEqual((project / ".pipeline" / "usage" / "collector.launch_mode").read_text(encoding="utf-8"), "tmux")
            self.assertEqual((project / ".pipeline" / "usage" / "collector.window_name").read_text(encoding="utf-8"), "usage-collector")
            self.assertEqual((project / ".pipeline" / "usage" / "collector.pane_id").read_text(encoding="utf-8"), "%77")
            self.assertEqual(run_mock.call_args_list[1].args[0][0:3], ["tmux", "new-window", "-d"])

    def test_windows_background_collector_start_uses_wrapped_bash_command(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / ".pipeline" / "usage").mkdir(parents=True)
            with (
                mock.patch.object(backend, "IS_WINDOWS", True),
                mock.patch.object(backend, "_token_collector_script_path", return_value="/mnt/c/tmp/_data/_data/token_collector.py"),
                mock.patch.object(backend, "_wsl_wrap", side_effect=lambda cmd: ["wrapped", *cmd]) as wrap_mock,
                mock.patch.object(
                    backend.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess(args=["wrapped"], returncode=0, stdout="", stderr=""),
                ) as run_mock,
                mock.patch.object(backend, "_read_sidecar_text", return_value="4321"),
                mock.patch.object(backend, "token_collector_alive", return_value=(True, 4321)),
            ):
                result = backend._spawn_token_collector_background(project, since_days=7)

        self.assertEqual(result, "token collector started")
        wrapped_cmd = wrap_mock.call_args.args[0]
        self.assertEqual(wrapped_cmd[0:2], ["bash", "-lc"])
        self.assertIn(f"cd {shlex.quote(str(project))}", wrapped_cmd[2])
        # Direct script path (no probe variable) + nohup daemon launch
        self.assertIn("token_collector.py", wrapped_cmd[2])
        self.assertIn("nohup python3 -u", wrapped_cmd[2])
        launch_calls = [call.args[0] for call in run_mock.call_args_list if call.args and isinstance(call.args[0], list)]
        self.assertTrue(any(cmd and cmd[0] == "wrapped" for cmd in launch_calls))

    def test_windows_background_collector_start_surfaces_launch_failure_detail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / ".pipeline" / "usage").mkdir(parents=True)
            with (
                mock.patch.object(backend, "IS_WINDOWS", True),
                mock.patch.object(backend, "_token_collector_script_path", return_value="/mnt/c/tmp/_data/token_collector.py"),
                mock.patch.object(backend, "_wsl_wrap", side_effect=lambda cmd: ["wrapped", *cmd]),
                mock.patch.object(
                    backend.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess(args=["wrapped"], returncode=1, stdout="", stderr="wsl launch failed"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "token collector background launch failed: wsl launch failed"):
                    backend._spawn_token_collector_background(project, since_days=7)

    def test_backfill_stops_and_restarts_running_collector(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / ".pipeline" / "usage").mkdir(parents=True)
            progress: list[dict[str, object]] = []
            with (
                mock.patch.object(backend, "token_collector_alive", return_value=(True, 1234)),
                mock.patch.object(backend, "token_collector_stop") as stop_mock,
                mock.patch.object(
                    backend,
                    "run_token_collector_once",
                    return_value={"elapsed_sec": 1.5, "usage_inserted": 42},
                ) as run_mock,
                mock.patch.object(backend, "token_collector_start") as start_mock,
            ):
                result = backend.backfill_token_history(project, progress_callback=progress.append)
            self.assertEqual(result["action"], "backfill")
            self.assertTrue(result["collector_was_running"])
            stop_mock.assert_called_once_with(project)
            run_mock.assert_called_once()
            self.assertTrue(run_mock.call_args.kwargs["force_rescan"])
            start_mock.assert_called_once_with(project, since_days=backend.DEFAULT_TOKEN_SINCE_DAYS)
            self.assertEqual(progress[0]["phase"], "stopping_collector")
            self.assertEqual(progress[-1]["phase"], "starting_collector")

    def test_backfill_starts_collector_even_when_it_was_not_running(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / ".pipeline" / "usage").mkdir(parents=True)
            with (
                mock.patch.object(backend, "token_collector_alive", return_value=(False, None)),
                mock.patch.object(
                    backend,
                    "run_token_collector_once",
                    return_value={"elapsed_sec": 1.5, "usage_inserted": 42},
                ) as run_mock,
                mock.patch.object(backend, "token_collector_start") as start_mock,
            ):
                result = backend.backfill_token_history(project)
            self.assertEqual(result["action"], "backfill")
            self.assertEqual(result["backup_path"], "")
            self.assertFalse(result["collector_was_running"])
            run_mock.assert_called_once()
            start_mock.assert_called_once_with(project, since_days=backend.DEFAULT_TOKEN_SINCE_DAYS)

    def test_rebuild_swaps_temp_db_and_keeps_backup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            usage_dir = project / ".pipeline" / "usage"
            usage_dir.mkdir(parents=True)
            db_path = usage_dir / "usage.db"
            db_path.write_text("old-db", encoding="utf-8")

            def _fake_run(_project: Path, temp_db: Path, **_kwargs: object) -> dict[str, object]:
                temp_db.write_text("new-db", encoding="utf-8")
                return {"elapsed_sec": 2.5, "usage_inserted": 99}

            with (
                mock.patch.object(backend, "token_collector_alive", return_value=(False, None)),
                mock.patch.object(backend, "run_token_collector_once", side_effect=_fake_run),
                mock.patch.object(backend, "token_collector_start") as start_mock,
            ):
                result = backend.rebuild_token_db(project)

            self.assertEqual(result["action"], "rebuild")
            self.assertEqual(db_path.read_text(encoding="utf-8"), "new-db")
            backup_path = Path(result["backup_path"])
            self.assertTrue(backup_path.exists())
            self.assertEqual(backup_path.read_text(encoding="utf-8"), "old-db")
            start_mock.assert_called_once_with(project, since_days=backend.DEFAULT_TOKEN_SINCE_DAYS)

    def test_rebuild_starts_collector_even_when_it_was_not_running(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            usage_dir = project / ".pipeline" / "usage"
            usage_dir.mkdir(parents=True)
            db_path = usage_dir / "usage.db"
            db_path.write_text("old-db", encoding="utf-8")

            def _fake_run(_project: Path, temp_db: Path, **_kwargs: object) -> dict[str, object]:
                temp_db.write_text("new-db", encoding="utf-8")
                return {"elapsed_sec": 2.5, "usage_inserted": 99}

            with (
                mock.patch.object(backend, "token_collector_alive", return_value=(False, None)),
                mock.patch.object(backend, "run_token_collector_once", side_effect=_fake_run),
                mock.patch.object(backend, "token_collector_start") as start_mock,
            ):
                result = backend.rebuild_token_db(project)
            self.assertEqual(result["action"], "rebuild")
            start_mock.assert_called_once_with(project, since_days=backend.DEFAULT_TOKEN_SINCE_DAYS)

    def test_token_collector_script_path_uses_packaged_data_root_on_windows(self) -> None:
        runtime_root = Path("/home/test/project/.pipeline/gui-runtime/_data")
        expected_script = runtime_root / "token_collector.py"
        with (
            mock.patch.object(backend, "IS_WINDOWS", True),
            mock.patch.object(backend, "resolve_project_runtime_file", return_value=expected_script),
            mock.patch.object(
                backend,
                "_windows_to_wsl_mount",
                side_effect=lambda path: f"mounted::{path}",
            ) as mount_mock,
        ):
            result = backend._token_collector_script_path(Path("/home/test/project"))
        self.assertEqual(result, f"mounted::{expected_script}")
        mount_mock.assert_called_once_with(expected_script)

    def test_token_collector_script_path_collapses_duplicate_data_segment_on_windows(self) -> None:
        duplicated_script = Path("/home/test/project/.pipeline/gui-runtime/_data/_data/token_collector.py")
        expected_script = Path("/home/test/project/.pipeline/gui-runtime/_data/token_collector.py")
        with (
            mock.patch.object(backend, "IS_WINDOWS", True),
            mock.patch.object(backend, "resolve_project_runtime_file", return_value=duplicated_script),
            mock.patch.object(
                backend,
                "_windows_to_wsl_mount",
                side_effect=lambda path: f"mounted::{path}",
            ) as mount_mock,
        ):
            result = backend._token_collector_script_path(Path("/home/test/project"))
        self.assertEqual(result, f"mounted::{expected_script}")
        mount_mock.assert_called_once_with(expected_script)

    def test_token_collector_wsl_candidates_include_normalized_packaged_path(self) -> None:
        candidates = backend._token_collector_wsl_candidates(
            "/mnt/c/Users/test/AppData/Local/Temp/_MEI12345/_data/_data/token_collector.py"
        )
        self.assertEqual(
            candidates[0],
            "/mnt/c/Users/test/AppData/Local/Temp/_MEI12345/_data/token_collector.py",
        )
        self.assertIn(
            "/mnt/c/Users/test/AppData/Local/Temp/_MEI12345/token_collector.py",
            candidates,
        )

    def test_token_collector_script_path_falls_back_to_source_tree_data_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            expected_script = repo_root / "_data" / "token_collector.py"
            expected_script.parent.mkdir(parents=True, exist_ok=True)
            expected_script.write_text("# stub\n", encoding="utf-8")
            with (
                mock.patch.object(backend, "IS_WINDOWS", False),
                mock.patch.object(backend, "resolve_project_runtime_file", return_value=expected_script),
            ):
                result = backend._token_collector_script_path(Path(td))
        self.assertEqual(result, str(expected_script))

    def test_token_collector_script_path_falls_back_to_flattened_frozen_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle_root = Path(td)
            app_root = bundle_root / "_data"
            app_root.mkdir(parents=True, exist_ok=True)
            expected_script = bundle_root / "token_collector.py"
            expected_script.write_text("# stub\n", encoding="utf-8")
            with (
                mock.patch.object(backend, "IS_WINDOWS", False),
                mock.patch.object(backend, "resolve_project_runtime_file", return_value=expected_script),
            ):
                result = backend._token_collector_script_path(Path(td))
        self.assertEqual(result, str(expected_script))

    def test_flattened_token_runtime_layout_can_run_token_collector_help(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copy2(Path("_data/token_collector.py"), root / "token_collector.py")
            shutil.copy2(Path("_data/token_store.py"), root / "token_store.py")
            shutil.copy2(Path("_data/job_linker.py"), root / "job_linker.py")
            shutil.copy2(Path("_data/token_schema.sql"), root / "token_schema.sql")
            shutil.copytree(Path("_data/token_parsers"), root / "token_parsers")

            result = subprocess.run(
                ["python3", str(root / "token_collector.py"), "--help"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Collect local CLI token usage into SQLite.", result.stdout)

    def test_raise_token_maintenance_errors_merges_action_and_restart_failures(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "scan failed; collector restart failed: restart failed"):
            backend._raise_token_maintenance_errors(
                RuntimeError("scan failed"),
                RuntimeError("restart failed"),
            )
