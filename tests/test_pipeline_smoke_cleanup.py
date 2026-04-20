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

    def test_prune_smoke_dirs_preserves_paths_with_spaces(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            older = pipeline_dir / "live-arb-smoke older"
            newest = pipeline_dir / "live-arb-smoke newest"
            self._mkdir_with_mtime(older, 100)
            self._mkdir_with_mtime(newest, 300)

            # dry_run first so we can assert preservation before the
            # live run actually removes the older workspace.
            dry = self._call_prune(
                root,
                "live-arb-smoke*",
                keep_recent=1,
                protect_tracked=0,
                dry_run=1,
            )
            self.assertIn(f"KEEP {newest}", dry.stdout)
            self.assertIn(f"DELETE {older}", dry.stdout)
            self.assertTrue(newest.exists())
            self.assertTrue(older.exists())

            live = self._call_prune(
                root,
                "live-arb-smoke*",
                keep_recent=1,
                protect_tracked=0,
                dry_run=0,
            )
            self.assertIn(f"KEEP {newest}", live.stdout)
            self.assertIn(f"DELETE {older}", live.stdout)
            self.assertTrue(
                newest.exists(),
                "newest space-containing directory must survive a live prune",
            )
            self.assertFalse(
                older.exists(),
                "older space-containing directory must actually be deleted "
                "by the live prune; truncation at space would hide it",
            )

    def test_prune_smoke_dirs_protect_tracked_dry_run_emits_all_three_verbs(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED"
            older_untracked = pipeline_dir / "live-blocked-smoke-older"
            newest_untracked = pipeline_dir / "live-blocked-smoke-newest"
            # mtime order: newest(300) > older(200) > tracked(100)
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._mkdir_with_mtime(newest_untracked, 300)

            self._commit_tracked(root, tracked)

            result = self._call_prune(
                root,
                "live-blocked-smoke-*",
                keep_recent=1,
                protect_tracked=1,
                dry_run=1,
            )

            # Protected dry-run must still surface all three verbs so
            # operators can inspect the plan before a live run:
            #   KEEP    -> newest kept by the window
            #   PROTECT -> tracked fixture skipped even though it would
            #              otherwise be deleted
            #   DELETE  -> older untracked workspace planned for removal
            self.assertIn(f"KEEP {newest_untracked}", result.stdout)
            self.assertIn(f"PROTECT {tracked}", result.stdout)
            self.assertIn(f"DELETE {older_untracked}", result.stdout)
            # dry_run=1 must not touch any directory on disk, even the
            # one that appears as DELETE in the diagnostic.
            self.assertTrue(newest_untracked.exists())
            self.assertTrue(older_untracked.exists())
            self.assertTrue(tracked.exists())

    def test_live_arb_prune_smoke_dirs_live_run_emits_keep_delete_stdout(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            older = pipeline_dir / "live-arb-smoke-older"
            middle = pipeline_dir / "live-arb-smoke-middle"
            newest = pipeline_dir / "live-arb-smoke-newest"
            self._mkdir_with_mtime(older, 100)
            self._mkdir_with_mtime(middle, 200)
            self._mkdir_with_mtime(newest, 300)

            result = self._call_prune(
                root,
                "live-arb-smoke-*",
                keep_recent=1,
                protect_tracked=0,
                dry_run=0,
            )

            self.assertTrue(newest.exists())
            self.assertFalse(middle.exists())
            self.assertFalse(older.exists())
            # Live run emits KEEP for the newest directory and DELETE for
            # the older ones, and must not emit any PROTECT line because
            # protect_tracked=0 skips the tracked-content check entirely.
            self.assertIn(f"KEEP {newest}", result.stdout)
            self.assertIn(f"DELETE {middle}", result.stdout)
            self.assertIn(f"DELETE {older}", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)

    def test_live_arb_prune_smoke_dirs_dry_run_preserves_and_reports(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            older = pipeline_dir / "live-arb-smoke-older"
            middle = pipeline_dir / "live-arb-smoke-middle"
            newest = pipeline_dir / "live-arb-smoke-newest"
            self._mkdir_with_mtime(older, 100)
            self._mkdir_with_mtime(middle, 200)
            self._mkdir_with_mtime(newest, 300)

            result = self._call_prune(
                root,
                "live-arb-smoke-*",
                keep_recent=1,
                protect_tracked=0,
                dry_run=1,
            )

            # dry_run=1 must still report the same KEEP/DELETE diagnostics
            # so operators can inspect the plan, but every matching
            # directory has to stay on disk.
            self.assertIn(f"KEEP {newest}", result.stdout)
            self.assertIn(f"DELETE {middle}", result.stdout)
            self.assertIn(f"DELETE {older}", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertTrue(newest.exists())
            self.assertTrue(middle.exists())
            self.assertTrue(older.exists())

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

    def test_blocked_auto_triage_caller_preserves_paths_with_spaces(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED one"
            older_untracked = pipeline_dir / "live-blocked-smoke-old two"
            newest_untracked = pipeline_dir / "live-blocked-smoke-new three"
            # mtime order: newest(300) > older(200) > tracked(100)
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._mkdir_with_mtime(newest_untracked, 300)
            self._commit_tracked(root, tracked)

            # Wrapper silences the underlying helper stdout with
            # `>/dev/null`, so the protected caller boundary can only be
            # asserted via disk state: the tracked fixture and the
            # newest untracked workspace must survive, and the older
            # untracked workspace must actually be removed. Before the
            # `_smoke_enumerate_dirs` fix, the space-containing paths
            # were truncated and no matching `rm -rf` took effect.
            script = (
                "set -euo pipefail\n"
                f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                f'prune_blocked_smoke_dirs "{root}" 1\n'
            )
            subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertTrue(
                tracked.exists(),
                "tracked space-containing fixture must be protected by the "
                "blocked auto-prune caller",
            )
            self.assertTrue(
                newest_untracked.exists(),
                "newest space-containing workspace must survive the "
                "blocked auto-prune caller",
            )
            self.assertFalse(
                older_untracked.exists(),
                "older space-containing workspace must actually be removed "
                "by the blocked auto-prune caller",
            )

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

    def test_live_arb_caller_preserves_paths_with_spaces(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            older = pipeline_dir / "live-arb-smoke-old one"
            newer = pipeline_dir / "live-arb-smoke-new two"
            self._mkdir_with_mtime(older, 100)
            self._mkdir_with_mtime(newer, 300)

            # Wrapper silences the underlying helper stdout with
            # `>/dev/null`, so the caller boundary can only be asserted
            # via disk state: the newest space-containing workspace must
            # survive and the older one must actually be removed. Before
            # the `_smoke_enumerate_dirs` fix, both paths were truncated
            # at the first space and no actual `rm -rf` took effect.
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

            self.assertTrue(
                newer.exists(),
                "newest space-containing workspace must survive the "
                "live-arb caller",
            )
            self.assertFalse(
                older.exists(),
                "older space-containing workspace must actually be removed "
                "by the live-arb caller",
            )

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

    def test_manual_cleanup_caller_noop_on_early_return_guards(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-one"
            d2 = pipeline_dir / "live-arb-smoke-two"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)

            # Each case targets one of the three remaining early-return
            # guards in prune_manual_smoke_dirs:
            #   - empty keep_recent
            #   - missing smoke_root
            #   - missing pattern
            # All three must return success, emit no helper-level
            # diagnostics, and never touch a real smoke workspace.
            cases = [
                (
                    "empty_keep_recent",
                    f'"{root}/.pipeline"',
                    '"live-arb-smoke-*"',
                    '""',
                ),
                (
                    "missing_smoke_root",
                    '""',
                    '"live-arb-smoke-*"',
                    '"3"',
                ),
                (
                    "missing_pattern",
                    f'"{root}/.pipeline"',
                    '""',
                    '"3"',
                ),
            ]
            for label, smoke_root_arg, pattern_arg, keep_recent_arg in cases:
                with self.subTest(guard=label):
                    script = (
                        "set -euo pipefail\n"
                        f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                        f"prune_manual_smoke_dirs {smoke_root_arg} "
                        f"{pattern_arg} {keep_recent_arg} 0\n"
                    )
                    result = subprocess.run(
                        ["bash", "-c", script],
                        cwd=root,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertEqual(
                        result.returncode,
                        0,
                        f"{label} guard must return 0 from "
                        f"prune_manual_smoke_dirs; stdout={result.stdout!r} "
                        f"stderr={result.stderr!r}",
                    )
                    self.assertNotIn("KEEP ", result.stdout)
                    self.assertNotIn("PROTECT ", result.stdout)
                    self.assertNotIn("DELETE ", result.stdout)
                    # Whenever a real smoke_root is still passed, matching
                    # directories must stay intact even though the helper
                    # returned without iterating.
                    self.assertTrue(
                        d1.exists() and d2.exists(),
                        f"{label} guard must not touch existing smoke dirs",
                    )

    def test_manual_cleanup_caller_noop_when_keep_recent_invalid(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-one"
            d2 = pipeline_dir / "live-arb-smoke-two"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)

            # Non-empty but not a non-negative integer. Mirrors the
            # blocked/live-arb wrapper invalid-input regressions, but
            # locks the manual wrapper boundary so a helper refactor
            # cannot silently turn invalid input into a destructive
            # delete for direct callers.
            for keep_recent_arg in ('"abc"', '"-1"', '"1.5"'):
                with self.subTest(keep_recent=keep_recent_arg):
                    script = (
                        "set -euo pipefail\n"
                        f'. "{root}/.pipeline/smoke-cleanup-lib.sh"\n'
                        f"prune_manual_smoke_dirs "
                        f'"{root}/.pipeline" "live-arb-smoke-*" '
                        f"{keep_recent_arg} 0\n"
                    )
                    result = subprocess.run(
                        ["bash", "-c", script],
                        cwd=root,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertEqual(
                        result.returncode,
                        0,
                        f"invalid keep_recent={keep_recent_arg!r} must "
                        f"return 0 from prune_manual_smoke_dirs; "
                        f"stdout={result.stdout!r} stderr={result.stderr!r}",
                    )
                    # Helper silently returns on invalid input: no
                    # KEEP/PROTECT/DELETE diagnostics should surface.
                    self.assertNotIn("KEEP ", result.stdout)
                    self.assertNotIn("PROTECT ", result.stdout)
                    self.assertNotIn("DELETE ", result.stdout)
                    self.assertTrue(
                        d1.exists() and d2.exists(),
                        f"no-op expected when keep_recent={keep_recent_arg!r}",
                    )

    def test_manual_cleanup_caller_noop_when_keep_recent_is_zero(self) -> None:
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
                f'"live-arb-smoke-*" 0 0\n'
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
            self.assertEqual(
                result.stdout,
                "",
                "keep_recent=0 must disable the manual cleaner with no "
                "KEEP/PROTECT/DELETE output, matching README contract",
            )

    def test_manual_cleanup_script_keep_recent_zero_preserves_dirs(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-1"
            d2 = pipeline_dir / "live-arb-smoke-2"
            d3 = pipeline_dir / "live-arb-smoke-3"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)
            self._mkdir_with_mtime(d3, 300)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-arb-smoke-*"
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "0"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertTrue(d1.exists())
            self.assertTrue(d2.exists())
            self.assertTrue(d3.exists())
            # The script must surface the disabled-cleanup receipt explicitly
            # so operators can distinguish it from a silent helper return.
            self.assertIn(
                "Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0",
                result.stdout,
            )
            self.assertIn("live-arb-smoke-*", result.stdout)
            # No destructive KEEP/PROTECT/DELETE lines should be emitted
            # when cleanup is disabled.
            self.assertNotIn("DELETE ", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertNotIn("KEEP ", result.stdout)

    def test_manual_cleanup_script_no_matching_dirs_receipt(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            # Seed an unrelated directory so the script's find() does not
            # accidentally match and the empty-match receipt is the only
            # branch exercised.
            other = pipeline_dir / "unrelated-workspace"
            self._mkdir_with_mtime(other, 100)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-arb-smoke-*"
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "3"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            expected = (
                f"No live-arb-smoke-* directories found under {pipeline_dir}"
            )
            self.assertIn(expected, result.stdout)
            # No destructive or helper-level lines should be emitted when
            # there is nothing to enumerate.
            self.assertNotIn("DELETE ", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertNotIn("KEEP ", result.stdout)
            self.assertNotIn("Nothing to clean.", result.stdout)
            self.assertNotIn("Cleanup disabled", result.stdout)
            # The unrelated directory must not be touched.
            self.assertTrue(other.exists())

    def test_manual_cleanup_script_nothing_to_clean_receipt(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-1"
            d2 = pipeline_dir / "live-arb-smoke-2"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-arb-smoke-*"
            # keep window is larger than the number of matching directories,
            # so the script hits the "Nothing to clean." branch before
            # delegating to the helper.
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "3"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Nothing to clean.", result.stdout)
            # Header block stays visible so the operator can read context.
            self.assertIn(f"Smoke root: {pipeline_dir}", result.stdout)
            self.assertIn("Pattern: live-arb-smoke-*", result.stdout)
            self.assertIn("Found: 2", result.stdout)
            self.assertIn("Keep recent: 3", result.stdout)
            # No destructive helper-level diagnostics when nothing is pruned.
            self.assertNotIn("DELETE ", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertNotIn("KEEP ", result.stdout)
            self.assertNotIn("Cleanup disabled", result.stdout)
            # Both matching directories must survive.
            self.assertTrue(d1.exists())
            self.assertTrue(d2.exists())

    def test_manual_cleanup_script_rejects_invalid_keep_recent(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            d1 = pipeline_dir / "live-arb-smoke-1"
            d2 = pipeline_dir / "live-arb-smoke-2"
            self._mkdir_with_mtime(d1, 100)
            self._mkdir_with_mtime(d2, 200)

            script_path = self._install_manual_cleanup_script(root)

            # Non-empty but not a non-negative integer. Empty string is
            # unreachable here because the script defaults KEEP_RECENT to
            # `3` when PIPELINE_SMOKE_KEEP_RECENT is unset or empty.
            for bad_value in ("abc", "-1", "1.5"):
                with self.subTest(keep_recent=bad_value):
                    env = os.environ.copy()
                    env["PIPELINE_SMOKE_PATTERN"] = "live-arb-smoke-*"
                    env["PIPELINE_SMOKE_KEEP_RECENT"] = bad_value
                    env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
                    result = subprocess.run(
                        ["bash", str(script_path), str(root)],
                        cwd=root,
                        env=env,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertEqual(
                        result.returncode,
                        1,
                        f"invalid PIPELINE_SMOKE_KEEP_RECENT={bad_value!r} "
                        f"must exit 1; stdout={result.stdout!r} "
                        f"stderr={result.stderr!r}",
                    )
                    self.assertEqual(
                        result.stdout,
                        "",
                        "invalid PIPELINE_SMOKE_KEEP_RECENT must not emit "
                        "any stdout receipt",
                    )
                    self.assertIn(
                        "PIPELINE_SMOKE_KEEP_RECENT must be a non-negative "
                        "integer",
                        result.stderr,
                    )
                    # Matching smoke directories must survive the rejected
                    # invocation.
                    self.assertTrue(d1.exists())
                    self.assertTrue(d2.exists())

    def test_manual_cleanup_script_blocked_pattern_preserves_paths_with_spaces(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED one"
            older_untracked = pipeline_dir / "live-blocked-smoke-old two"
            newest_untracked = pipeline_dir / "live-blocked-smoke-new three"
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._mkdir_with_mtime(newest_untracked, 300)
            self._commit_tracked(root, tracked)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-blocked-smoke*"
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
            # Dry-run must surface full-path KEEP/DELETE/PROTECT lines
            # and leave every space-containing directory on disk.
            self.assertIn(f"KEEP {newest_untracked}", dry_result.stdout)
            self.assertIn(f"DELETE {older_untracked}", dry_result.stdout)
            self.assertIn(f"PROTECT {tracked}", dry_result.stdout)
            self.assertTrue(tracked.exists())
            self.assertTrue(newest_untracked.exists())
            self.assertTrue(older_untracked.exists())

            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            live_result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn(f"KEEP {newest_untracked}", live_result.stdout)
            self.assertIn(f"DELETE {older_untracked}", live_result.stdout)
            self.assertIn(f"PROTECT {tracked}", live_result.stdout)
            self.assertTrue(
                tracked.exists(),
                "tracked space-containing fixture must be protected by the "
                "manual cleanup script live run",
            )
            self.assertTrue(
                newest_untracked.exists(),
                "newest space-containing workspace must survive the manual "
                "cleanup script live run",
            )
            self.assertFalse(
                older_untracked.exists(),
                "older space-containing workspace must actually be removed "
                "by the manual cleanup script live run",
            )

    def test_manual_cleanup_script_preserves_paths_with_spaces(self) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            older = pipeline_dir / "live-arb-smoke-old one"
            newer = pipeline_dir / "live-arb-smoke-new two"
            self._mkdir_with_mtime(older, 100)
            self._mkdir_with_mtime(newer, 300)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-arb-smoke*"
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
            # Dry-run must surface the same full-path diagnostics and
            # leave both space-containing directories on disk.
            self.assertIn(f"KEEP {newer}", dry_result.stdout)
            self.assertIn(f"DELETE {older}", dry_result.stdout)
            self.assertTrue(newer.exists())
            self.assertTrue(older.exists())

            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            live_result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn(f"KEEP {newer}", live_result.stdout)
            self.assertIn(f"DELETE {older}", live_result.stdout)
            self.assertTrue(
                newer.exists(),
                "newest space-containing workspace must survive the "
                "manual cleanup script live run",
            )
            self.assertFalse(
                older.exists(),
                "older space-containing workspace must actually be removed "
                "by the manual cleanup script live run",
            )

    def test_manual_cleanup_script_blocked_pattern_disabled_cleanup_receipt(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED one"
            older_untracked = pipeline_dir / "live-blocked-smoke-old two"
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._commit_tracked(root, tracked)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-blocked-smoke*"
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "0"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            # Header block must stay visible so the operator can read
            # context before the disabled-cleanup receipt.
            self.assertIn(f"Smoke root: {pipeline_dir}", result.stdout)
            self.assertIn("Pattern: live-blocked-smoke*", result.stdout)
            self.assertIn("Found: 2", result.stdout)
            self.assertIn("Keep recent: 0", result.stdout)
            # Explicit disabled-cleanup receipt for the blocked pattern.
            self.assertIn(
                "Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, "
                "preserving all matching live-blocked-smoke* directories.",
                result.stdout,
            )
            # No destructive helper-level diagnostics when cleanup is
            # disabled.
            self.assertNotIn("DELETE ", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertNotIn("KEEP ", result.stdout)
            # Both space-containing directories survive.
            self.assertTrue(tracked.exists())
            self.assertTrue(older_untracked.exists())

    def test_manual_cleanup_script_blocked_pattern_nothing_to_clean_receipt(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED one"
            older_untracked = pipeline_dir / "live-blocked-smoke-old two"
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(older_untracked, 200)
            self._commit_tracked(root, tracked)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-blocked-smoke*"
            # keep window larger than match count hits the nothing-to-clean
            # branch before the helper is ever invoked.
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "3"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn(f"Smoke root: {pipeline_dir}", result.stdout)
            self.assertIn("Pattern: live-blocked-smoke*", result.stdout)
            self.assertIn("Found: 2", result.stdout)
            self.assertIn("Keep recent: 3", result.stdout)
            self.assertIn("Nothing to clean.", result.stdout)
            # No destructive or disabled-cleanup diagnostics when the
            # nothing-to-clean branch wins.
            self.assertNotIn("DELETE ", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertNotIn("KEEP ", result.stdout)
            self.assertNotIn("Cleanup disabled", result.stdout)
            # Both space-containing directories survive.
            self.assertTrue(tracked.exists())
            self.assertTrue(older_untracked.exists())

    def test_manual_cleanup_script_blocked_pattern_no_matching_dirs_receipt(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            # Seed an unrelated workspace so the no-match branch is the
            # only one exercised while still proving the script does not
            # touch sibling directories.
            other = pipeline_dir / "unrelated-workspace"
            self._mkdir_with_mtime(other, 100)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            env["PIPELINE_SMOKE_PATTERN"] = "live-blocked-smoke*"
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "3"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            expected = (
                f"No live-blocked-smoke* directories found under "
                f"{pipeline_dir}"
            )
            self.assertIn(expected, result.stdout)
            # The no-match branch exits before printing the header block.
            self.assertNotIn("Smoke root:", result.stdout)
            self.assertNotIn("Pattern: live-blocked-smoke*", result.stdout)
            self.assertNotIn("Found:", result.stdout)
            self.assertNotIn("Keep recent:", result.stdout)
            self.assertNotIn("Dry run:", result.stdout)
            self.assertNotIn("Nothing to clean.", result.stdout)
            self.assertNotIn("Cleanup disabled", result.stdout)
            self.assertNotIn("DELETE ", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertNotIn("KEEP ", result.stdout)
            # The unrelated workspace must not be touched.
            self.assertTrue(other.exists())

    def test_manual_cleanup_script_empty_pattern_falls_back_to_live_arb(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            arb_older = pipeline_dir / "live-arb-smoke-old one"
            arb_newer = pipeline_dir / "live-arb-smoke-new two"
            blocked_other = pipeline_dir / "live-blocked-smoke-TRACKED one"
            self._mkdir_with_mtime(arb_older, 100)
            self._mkdir_with_mtime(arb_newer, 300)
            self._mkdir_with_mtime(blocked_other, 200)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            # Empty override must fall through the `${PIPELINE_SMOKE_PATTERN:-live-arb-smoke-*}`
            # default, not be treated as a blank pattern. Dry-run keeps
            # the assertion focused on stdout + preservation.
            env["PIPELINE_SMOKE_PATTERN"] = ""
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "1"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "1"
            result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Pattern: live-arb-smoke-*", result.stdout)
            self.assertIn("Found: 2", result.stdout)
            self.assertIn(f"KEEP {arb_newer}", result.stdout)
            self.assertIn(f"DELETE {arb_older}", result.stdout)
            # The blocked sibling must never appear in KEEP/DELETE/PROTECT
            # output — the live-arb fallback pattern does not match it.
            self.assertNotIn(f"{blocked_other}", result.stdout)
            self.assertNotIn("live-blocked-smoke", result.stdout)
            # Dry-run keeps every directory on disk, including the
            # untouched blocked fixture.
            self.assertTrue(arb_newer.exists())
            self.assertTrue(arb_older.exists())
            self.assertTrue(
                blocked_other.exists(),
                "blocked sibling must stay untouched when the empty "
                "override falls back to the live-arb pattern",
            )

    def test_manual_cleanup_script_malformed_pattern_no_match_receipt(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            tracked = pipeline_dir / "live-blocked-smoke-TRACKED one"
            arb = pipeline_dir / "live-arb-smoke-new two"
            self._mkdir_with_mtime(tracked, 100)
            self._mkdir_with_mtime(arb, 200)
            self._commit_tracked(root, tracked)

            script_path = self._install_manual_cleanup_script(root)

            env = os.environ.copy()
            # Malformed-but-shell-safe pattern: an unbalanced `[` never
            # matches any real smoke directory name, so the script must
            # hit the no-match branch with the exact literal pattern
            # echoed back in the receipt.
            env["PIPELINE_SMOKE_PATTERN"] = "live-blocked-smoke["
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "1"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            result = subprocess.run(
                ["bash", str(script_path), str(root)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            expected = (
                f"No live-blocked-smoke[ directories found under "
                f"{pipeline_dir}"
            )
            self.assertIn(expected, result.stdout)
            # No header block: the no-match branch exits before those
            # lines are printed.
            self.assertNotIn("Smoke root:", result.stdout)
            self.assertNotIn("Pattern:", result.stdout)
            self.assertNotIn("Found:", result.stdout)
            self.assertNotIn("Keep recent:", result.stdout)
            self.assertNotIn("Dry run:", result.stdout)
            self.assertNotIn("Nothing to clean.", result.stdout)
            self.assertNotIn("Cleanup disabled", result.stdout)
            self.assertNotIn("DELETE ", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertNotIn("KEEP ", result.stdout)
            # Both pre-existing directories must stay intact.
            self.assertTrue(tracked.exists())
            self.assertTrue(arb.exists())

    def test_manual_cleanup_script_omitted_project_root_uses_cwd(
        self,
    ) -> None:
        # Build the temp repo under a parent path that itself contains
        # a space so `$(pwd)` fallback is exercised with a space-containing
        # project root.
        with tempfile.TemporaryDirectory() as parent:
            root = (Path(parent) / "repo with spaces").resolve()
            root.mkdir()
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
            pipeline_dir.mkdir()
            (pipeline_dir / "smoke-cleanup-lib.sh").write_text(
                LIB_SOURCE.read_text(encoding="utf-8"), encoding="utf-8"
            )
            script_path = pipeline_dir / "cleanup-old-smoke-dirs.sh"
            script_path.write_text(
                MANUAL_SCRIPT_SOURCE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            script_path.chmod(0o755)

            older = pipeline_dir / "live-arb-smoke-old one"
            newer = pipeline_dir / "live-arb-smoke-new two"
            self._mkdir_with_mtime(older, 100)
            self._mkdir_with_mtime(newer, 300)

            env = os.environ.copy()
            # Do not set PIPELINE_SMOKE_PATTERN so the default
            # `live-arb-smoke-*` fallback is exercised alongside the
            # omitted PROJECT_ROOT argument.
            env.pop("PIPELINE_SMOKE_PATTERN", None)
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "1"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "1"
            result = subprocess.run(
                ["bash", str(script_path)],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn(f"Smoke root: {pipeline_dir}", result.stdout)
            self.assertIn("Pattern: live-arb-smoke-*", result.stdout)
            self.assertIn("Found: 2", result.stdout)
            self.assertIn(f"KEEP {newer}", result.stdout)
            self.assertIn(f"DELETE {older}", result.stdout)
            # Dry-run leaves every matching directory in place even though
            # DELETE was planned.
            self.assertTrue(newer.exists())
            self.assertTrue(older.exists())

    def test_manual_cleanup_script_invalid_project_root_fails_cd(
        self,
    ) -> None:
        tmp, root = self._make_temp_repo()
        with tmp:
            pipeline_dir = root / ".pipeline"
            older = pipeline_dir / "live-arb-smoke-1"
            newer = pipeline_dir / "live-arb-smoke-2"
            self._mkdir_with_mtime(older, 100)
            self._mkdir_with_mtime(newer, 200)

            script_path = self._install_manual_cleanup_script(root)

            missing = "/nonexistent path with spaces/missing"
            env = os.environ.copy()
            env["PIPELINE_SMOKE_KEEP_RECENT"] = "1"
            env["PIPELINE_SMOKE_CLEANUP_DRY_RUN"] = "0"
            result = subprocess.run(
                ["bash", str(script_path), missing],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(
                result.returncode,
                1,
                f"invalid PROJECT_ROOT={missing!r} must exit 1; "
                f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            # The only surfaced diagnostic should be the shell `cd`
            # failure echoing the exact missing path.
            self.assertIn("No such file or directory", result.stderr)
            self.assertIn(missing, result.stderr)
            # The script must exit before printing the header block.
            self.assertNotIn("Smoke root:", result.stdout)
            self.assertNotIn("Pattern:", result.stdout)
            self.assertNotIn("Found:", result.stdout)
            self.assertNotIn("Keep recent:", result.stdout)
            self.assertNotIn("Dry run:", result.stdout)
            self.assertNotIn("Cleanup disabled", result.stdout)
            self.assertNotIn("Nothing to clean.", result.stdout)
            self.assertNotIn("DELETE ", result.stdout)
            self.assertNotIn("PROTECT ", result.stdout)
            self.assertNotIn("KEEP ", result.stdout)
            # Existing smoke directories in the real repo must stay
            # untouched — the failed cd must never reach any prune path.
            self.assertTrue(older.exists())
            self.assertTrue(newer.exists())

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
