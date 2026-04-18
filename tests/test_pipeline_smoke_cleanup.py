import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_SOURCE = REPO_ROOT / ".pipeline" / "smoke-cleanup-lib.sh"
MANUAL_SCRIPT_SOURCE = REPO_ROOT / ".pipeline" / "cleanup-old-smoke-dirs.sh"
AUTO_TRIAGE_SCRIPT_SOURCE = (
    REPO_ROOT / ".pipeline" / "smoke-implement-blocked-auto-triage.sh"
)
LIVE_ARB_SCRIPT_SOURCE = (
    REPO_ROOT / ".pipeline" / "smoke-three-agent-arbitration.sh"
)


class SmokeCleanupLibTest(unittest.TestCase):
    def _make_temp_repo(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name).resolve()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.email=t@example.com",
                "-c",
                "user.name=t",
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "init",
            ],
            cwd=root,
            check=True,
        )
        pipeline_dir = root / ".pipeline"
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        (pipeline_dir / "smoke-cleanup-lib.sh").write_text(
            LIB_SOURCE.read_text(encoding="utf-8"), encoding="utf-8"
        )
        return tmp, root

    def _install_manual_cleanup_script(self, root: Path) -> Path:
        target = root / ".pipeline" / "cleanup-old-smoke-dirs.sh"
        target.write_text(
            MANUAL_SCRIPT_SOURCE.read_text(encoding="utf-8"), encoding="utf-8"
        )
        target.chmod(0o755)
        return target

    def _mkdir_with_mtime(self, path: Path, epoch: int) -> None:
        path.mkdir(parents=True, exist_ok=True)
        stub = path / "note.txt"
        stub.write_text(f"smoke fixture stub {path.name}\n", encoding="utf-8")
        os.utime(stub, (epoch, epoch))
        os.utime(path, (epoch, epoch))

    def _commit_tracked(self, root: Path, path: Path) -> None:
        subprocess.run(["git", "add", "-f", "--", str(path)], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.email=t@example.com",
                "-c",
                "user.name=t",
                "commit",
                "-q",
                "-m",
                f"fixture {path.name}",
            ],
            cwd=root,
            check=True,
        )
        # Re-set mtime after commit in case filesystem touched the entries.
        for child in path.rglob("*"):
            if child.is_file():
                os.utime(child, (100, 100))
        os.utime(path, (100, 100))

    def _call_prune(
        self,
        root: Path,
        pattern: str,
        keep_recent: int,
        protect_tracked: int = 0,
        dry_run: int = 0,
    ) -> subprocess.CompletedProcess:
        script = (
            'set -euo pipefail\n'
            f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
            f'prune_smoke_dirs "{root}/.pipeline" "{pattern}" '
            f'{keep_recent} {protect_tracked} {dry_run}\n'
        )
        return subprocess.run(
            ["bash", "-c", script],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        )

    def test_blocked_smoke_protects_tracked_fixture_dir(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED"
            older_untracked = pipeline_dir / "live-blocked-smoke-old1"
            middle_untracked = pipeline_dir / "live-blocked-smoke-old2"
            newest_untracked = pipeline_dir / "live-blocked-smoke-new"
            # mtime order: newest(400) > middle(300) > older(200) > tracked(100)
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._mkdir_with_mtime(middle_untracked, 300)
            self._mkdir_with_mtime(newest_untracked, 400)

            self._commit_tracked(root, tracked)

            result = self._call_prune(
                root,
                "live-blocked-smoke-*",
                keep_recent=1,
                protect_tracked=1,
            )

            self.assertTrue(
                tracked.exists(),
                "tracked `live-blocked-smoke-*` fixture must be protected",
            )
            self.assertTrue(newest_untracked.exists(), "newest dir must be kept")
            self.assertFalse(middle_untracked.exists())
            self.assertFalse(older_untracked.exists())

            stdout = result.stdout
            self.assertIn(f"KEEP {newest_untracked}", stdout)
            self.assertIn(f"PROTECT {tracked}", stdout)
            self.assertIn(f"DELETE {middle_untracked}", stdout)
            self.assertIn(f"DELETE {older_untracked}", stdout)

    def test_blocked_smoke_deletes_untracked_older_dirs(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            new1 = pipeline_dir / "live-blocked-smoke-new"
            old1 = pipeline_dir / "live-blocked-smoke-older"
            old2 = pipeline_dir / "live-blocked-smoke-oldest"
            self._mkdir_with_mtime(new1, 400)
            self._mkdir_with_mtime(old1, 200)
            self._mkdir_with_mtime(old2, 100)

            self._call_prune(
                root,
                "live-blocked-smoke-*",
                keep_recent=1,
                protect_tracked=1,
            )

            self.assertTrue(new1.exists())
            self.assertFalse(old1.exists())
            self.assertFalse(old2.exists())

    def test_live_arb_cleanup_keeps_newest_keep_recent_dirs(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-1"
            d2 = pipeline_dir / "live-arb-smoke-2"
            d3 = pipeline_dir / "live-arb-smoke-3"
            d4 = pipeline_dir / "live-arb-smoke-4"
            d5 = pipeline_dir / "live-arb-smoke-5"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)
            self._mkdir_with_mtime(d3, 300)
            self._mkdir_with_mtime(d4, 400)
            self._mkdir_with_mtime(d5, 500)

            self._call_prune(root, "live-arb-smoke-*", keep_recent=3)

            self.assertTrue(d5.exists())
            self.assertTrue(d4.exists())
            self.assertTrue(d3.exists())
            self.assertFalse(d2.exists())
            self.assertFalse(d1.exists())


    def test_manual_cleanup_script_protects_tracked_under_pattern_override(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED"
            older_untracked = pipeline_dir / "live-blocked-smoke-old1"
            middle_untracked = pipeline_dir / "live-blocked-smoke-old2"
            newest_untracked = pipeline_dir / "live-blocked-smoke-new"
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._mkdir_with_mtime(middle_untracked, 300)
            self._mkdir_with_mtime(newest_untracked, 400)
            self._commit_tracked(root, tracked)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-blocked-smoke-*"
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "1"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "1"
            dry_result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn(f"PROTECT {tracked}", dry_result.stdout)
            self.assertNotIn(f"DELETE {tracked}", dry_result.stdout)
            self.assertIn(f"KEEP {newest_untracked}", dry_result.stdout)
            self.assertTrue(tracked.exists(), "dry-run must not touch tracked dir")
            self.assertTrue(older_untracked.exists(), "dry-run must not delete")

            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            live_result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn(f"PROTECT {tracked}", live_result.stdout)
            self.assertNotIn(f"DELETE {tracked}", live_result.stdout)
            self.assertTrue(
                tracked.exists(),
                "manual override must not delete tracked `live-blocked-smoke-*` fixture",
            )
            self.assertTrue(newest_untracked.exists())
            self.assertFalse(middle_untracked.exists())
            self.assertFalse(older_untracked.exists())


    def test_blocked_auto_triage_caller_protects_tracked_and_prunes_generated(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED"
            older_untracked = pipeline_dir / "live-blocked-smoke-old1"
            middle_untracked = pipeline_dir / "live-blocked-smoke-old2"
            newest_untracked = pipeline_dir / "live-blocked-smoke-new"
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._mkdir_with_mtime(middle_untracked, 300)
            self._mkdir_with_mtime(newest_untracked, 400)
            self._commit_tracked(root, tracked)

            script = (
                "set -euo pipefail\n"
                f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                f'prune_blocked_smoke_dirs "{root}" 1\n'
            )
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertTrue(
                tracked.exists(),
                "blocked auto-prune caller must keep tracked fixture",
            )
            self.assertTrue(
                newest_untracked.exists(),
                "newest generated smoke workspace must be kept by caller",
            )
            self.assertFalse(middle_untracked.exists())
            self.assertFalse(older_untracked.exists())
            # Caller silences prune output with >/dev/null, so the helper
            # itself must still have emitted no stdout beyond what the
            # shared helper prints — assert the helper wrote PROTECT/DELETE
            # lines by running it without the caller redirect.
            _ = result  # keep reference; caller stdout not asserted here

    def test_blocked_auto_triage_caller_noop_when_keep_recent_invalid(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-blocked-smoke-one"
            d2 = pipeline_dir / "live-blocked-smoke-two"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)

            for keep_recent_arg in ('""', "0", '"-1"', '"abc"'):
                script = (
                    "set -euo pipefail\n"
                    f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                    f"prune_blocked_smoke_dirs \"{root}\" {keep_recent_arg}\n"
                )
                subprocess.run(
                    ["bash", "-c", script],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                self.assertTrue(
                    d1.exists() and d2.exists(),
                    f"no-op expected when keep_recent={keep_recent_arg!r}",
                )

    def test_blocked_auto_triage_script_delegates_to_shared_helper(self) -> None:
        # The actual caller in `.pipeline/smoke-implement-blocked-auto-triage.sh`
        # must route its auto-prune through the shared helper so the caller
        # contract stays covered by the helper-level regressions above. A bare
        # textual grep is enough here: the script is a thin tmux harness and
        # re-running it in unit tests would require a live tmux session.
        script_text = AUTO_TRIAGE_SCRIPT_SOURCE.read_text(encoding="utf-8")
        self.assertIn(
            "prune_blocked_smoke_dirs",
            script_text,
            "blocked auto-triage script must delegate auto-prune to the "
            "shared prune_blocked_smoke_dirs helper",
        )

    def test_live_arb_caller_keeps_newest_and_prunes_older(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-1"
            d2 = pipeline_dir / "live-arb-smoke-2"
            d3 = pipeline_dir / "live-arb-smoke-3"
            d4 = pipeline_dir / "live-arb-smoke-4"
            d5 = pipeline_dir / "live-arb-smoke-5"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)
            self._mkdir_with_mtime(d3, 300)
            self._mkdir_with_mtime(d4, 400)
            self._mkdir_with_mtime(d5, 500)

            script = (
                "set -euo pipefail\n"
                f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                f'prune_live_arb_smoke_dirs "{root}" 3\n'
            )
            subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertTrue(d5.exists())
            self.assertTrue(d4.exists())
            self.assertTrue(d3.exists())
            self.assertFalse(d2.exists())
            self.assertFalse(d1.exists())

    def test_live_arb_caller_noop_when_keep_recent_invalid(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-one"
            d2 = pipeline_dir / "live-arb-smoke-two"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)

            for keep_recent_arg in ('""', "0", '"-5"', '"abc"'):
                script = (
                    "set -euo pipefail\n"
                    f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                    f"prune_live_arb_smoke_dirs \"{root}\" {keep_recent_arg}\n"
                )
                subprocess.run(
                    ["bash", "-c", script],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                self.assertTrue(
                    d1.exists() and d2.exists(),
                    f"no-op expected when keep_recent={keep_recent_arg!r}",
                )

    def test_live_arb_caller_does_not_touch_blocked_smoke_dirs(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            arb_old = pipeline_dir / "live-arb-smoke-old"
            arb_new = pipeline_dir / "live-arb-smoke-new"
            blocked_old = pipeline_dir / "live-blocked-smoke-old"
            self._mkdir_with_mtime(arb_old, 100)
            self._mkdir_with_mtime(arb_new, 300)
            self._mkdir_with_mtime(blocked_old, 50)

            script = (
                "set -euo pipefail\n"
                f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                f'prune_live_arb_smoke_dirs "{root}" 1\n'
            )
            subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue(arb_new.exists())
            self.assertFalse(arb_old.exists())
            self.assertTrue(
                blocked_old.exists(),
                "live-arb caller must not touch live-blocked-smoke-* dirs",
            )

    def test_live_arb_script_delegates_to_shared_helper(self) -> None:
        # Mirror of the blocked-smoke delegation regression: the live-arb
        # caller must route its auto-prune through the shared wrapper so
        # the caller contract stays covered by the helper-level tests above.
        script_text = LIVE_ARB_SCRIPT_SOURCE.read_text(encoding="utf-8")
        self.assertIn(
            "prune_live_arb_smoke_dirs",
            script_text,
            "live-arb smoke script must delegate auto-prune to the shared "
            "prune_live_arb_smoke_dirs helper",
        )

    def test_manual_cleanup_caller_default_live_arb_path_prunes_older(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-1"
            d2 = pipeline_dir / "live-arb-smoke-2"
            d3 = pipeline_dir / "live-arb-smoke-3"
            d4 = pipeline_dir / "live-arb-smoke-4"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)
            self._mkdir_with_mtime(d3, 300)
            self._mkdir_with_mtime(d4, 400)

            script = (
                "set -euo pipefail\n"
                f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                f'prune_manual_smoke_dirs "{root}/.pipeline" '
                f'"live-arb-smoke-*" 2 0\n'
            )
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertTrue(d4.exists())
            self.assertTrue(d3.exists())
            self.assertFalse(d2.exists())
            self.assertFalse(d1.exists())
            # Manual cleanup keeps the KEEP/DELETE diagnostic visible
            # (unlike auto-prune callers which silence to /dev/null).
            self.assertIn(f"KEEP {d4}", result.stdout)
            self.assertIn(f"KEEP {d3}", result.stdout)
            self.assertIn(f"DELETE {d2}", result.stdout)
            self.assertIn(f"DELETE {d1}", result.stdout)

    def test_manual_cleanup_caller_pattern_override_protects_tracked(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED"
            older_untracked = pipeline_dir / "live-blocked-smoke-old1"
            newer_untracked = pipeline_dir / "live-blocked-smoke-new"
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._mkdir_with_mtime(newer_untracked, 300)
            self._commit_tracked(root, tracked)

            script = (
                "set -euo pipefail\n"
                f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                f'prune_manual_smoke_dirs "{root}/.pipeline" '
                f'"live-blocked-smoke-*" 1 0\n'
            )
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertTrue(
                tracked.exists(),
                "manual cleaner must protect checked-in fixture under "
                "pattern override",
            )
            self.assertTrue(newer_untracked.exists())
            self.assertFalse(older_untracked.exists())
            self.assertIn(f"PROTECT {tracked}", result.stdout)
            self.assertIn(f"KEEP {newer_untracked}", result.stdout)
            self.assertIn(f"DELETE {older_untracked}", result.stdout)

    def test_manual_cleanup_caller_honors_dry_run(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-1"
            d2 = pipeline_dir / "live-arb-smoke-2"
            d3 = pipeline_dir / "live-arb-smoke-3"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)
            self._mkdir_with_mtime(d3, 300)

            script = (
                "set -euo pipefail\n"
                f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                f'prune_manual_smoke_dirs "{root}/.pipeline" '
                f'"live-arb-smoke-*" 1 1\n'
            )
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertTrue(d1.exists())
            self.assertTrue(d2.exists())
            self.assertTrue(d3.exists())
            self.assertIn(f"KEEP {d3}", result.stdout)
            self.assertIn(f"DELETE {d2}", result.stdout)
            self.assertIn(f"DELETE {d1}", result.stdout)

    def test_manual_cleanup_script_delegates_to_shared_helper(self) -> None:
        script_text = MANUAL_SCRIPT_SOURCE.read_text(encoding="utf-8")
        self.assertIn(
            "prune_manual_smoke_dirs",
            script_text,
            "manual cleanup script must delegate its final prune_smoke_dirs "
            "contract to the shared prune_manual_smoke_dirs helper",
        )

    def test_prune_smoke_dirs_fails_closed_outside_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            pipeline_dir = root / ".pipeline"
            pipeline_dir.mkdir()
            (pipeline_dir / "smoke-cleanup-lib.sh").write_text(
                LIB_SOURCE.read_text(encoding="utf-8"), encoding="utf-8"
            )
            d1 = pipeline_dir / "live-blocked-smoke-one"
            d2 = pipeline_dir / "live-blocked-smoke-two"
            d3 = pipeline_dir / "live-blocked-smoke-three"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)
            self._mkdir_with_mtime(d3, 300)

            script = (
                'set -uo pipefail\n'
                f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                f'prune_smoke_dirs "{root}/.pipeline" "live-blocked-smoke-*" 1 1 0\n'
            )
            env = os.environ.copy()
            env["GIT_CEILING_DIRECTORIES"] = str(root.parent)
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(
                result.returncode,
                0,
                f"expected non-zero exit when protect_tracked=1 and smoke_root has no git repo; "
                f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("protect_tracked=1", result.stderr)
            self.assertIn(str(pipeline_dir), result.stderr)
            # No enumeration or deletion should have happened.
            self.assertEqual(result.stdout, "")
            self.assertTrue(d1.exists())
            self.assertTrue(d2.exists())
            self.assertTrue(d3.exists())


if __name__ == "__main__":
    unittest.main()
