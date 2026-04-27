from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_runtime.operator_autonomy import PR_MERGE_GATE_REASON
from pipeline_runtime.pr_merge_state import PrMergeStatusCache


class PrMergeStatusCacheTest(unittest.TestCase):
    def _git(self, repo: Path, *args: str) -> None:
        result = subprocess.run(
            ["git", *args],
            cwd=str(repo),
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {result.stderr}")

    def _init_repo(self, repo: Path) -> None:
        self._git(repo, "init", "-q")
        self._git(repo, "config", "user.email", "test@example.invalid")
        self._git(repo, "config", "user.name", "Test User")
        self._git(repo, "checkout", "-q", "-b", "main")

    def _commit_file(self, repo: Path, name: str, content: str) -> str:
        path = repo / name
        path.write_text(content, encoding="utf-8")
        self._git(repo, "add", name)
        self._git(repo, "commit", "-q", "-m", f"commit {name}")
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo),
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def test_completed_pr_numbers_requires_matching_head_when_declared(self) -> None:
        cache = PrMergeStatusCache()
        control_meta = {"reason_code": PR_MERGE_GATE_REASON}
        control_text = "DECISION_REQUIRED: PR #27 merge approval\n- HEAD: `77d1827`\n"
        result = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "state": "MERGED",
                    "mergedAt": "2026-04-23T03:56:50Z",
                    "headRefOid": "1b23edfc47322c5821928646427c6b8a53fe5dd3",
                }
            ),
        )

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch("pipeline_runtime.pr_merge_state.shutil.which", return_value="/usr/bin/gh"),
            mock.patch("pipeline_runtime.pr_merge_state.subprocess.run", return_value=result),
        ):
            completed = cache.completed_pr_numbers(Path(tmp), control_text, control_meta)

        self.assertEqual(completed, [])

    def test_completed_pr_numbers_accepts_matching_head_prefix(self) -> None:
        cache = PrMergeStatusCache()
        control_meta = {"reason_code": PR_MERGE_GATE_REASON}
        control_text = "DECISION_REQUIRED: PR #27 merge approval\n- HEAD: `1b23edf`\n"
        result = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "state": "MERGED",
                    "mergedAt": "2026-04-23T03:56:50Z",
                    "headRefOid": "1b23edfc47322c5821928646427c6b8a53fe5dd3",
                }
            ),
        )

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch("pipeline_runtime.pr_merge_state.shutil.which", return_value="/usr/bin/gh"),
            mock.patch("pipeline_runtime.pr_merge_state.subprocess.run", return_value=result),
        ):
            completed = cache.completed_pr_numbers(Path(tmp), control_text, control_meta)

        self.assertEqual(completed, [27])

    def test_completed_pr_numbers_falls_back_to_local_merge_commit_when_gh_unavailable(self) -> None:
        cache = PrMergeStatusCache()
        control_meta = {"reason_code": PR_MERGE_GATE_REASON}
        control_text = "DECISION_REQUIRED: merge PR #46 → main\n"

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch("pipeline_runtime.pr_merge_state.shutil.which", return_value=None),
        ):
            repo = Path(tmp)
            self._init_repo(repo)
            self._commit_file(repo, "base.txt", "base\n")
            self._git(repo, "checkout", "-q", "-b", "feat/pr-46")
            self._commit_file(repo, "feature.txt", "feature\n")
            self._git(repo, "checkout", "-q", "main")
            self._git(repo, "merge", "--no-ff", "feat/pr-46", "-m", "Merge pull request #46 from test/feat")

            completed = cache.completed_pr_numbers(repo, control_text, control_meta)

        self.assertEqual(completed, [46])

    def test_completed_pr_numbers_uses_local_head_sha_when_gh_unavailable(self) -> None:
        cache = PrMergeStatusCache()
        control_meta = {"reason_code": PR_MERGE_GATE_REASON}

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch("pipeline_runtime.pr_merge_state.shutil.which", return_value=None),
        ):
            repo = Path(tmp)
            self._init_repo(repo)
            self._commit_file(repo, "base.txt", "base\n")
            self._git(repo, "checkout", "-q", "-b", "feat/pr-47")
            head_sha = self._commit_file(repo, "feature.txt", "feature\n")
            self._git(repo, "checkout", "-q", "main")
            self._git(repo, "merge", "--no-ff", "feat/pr-47", "-m", "integration merge")
            control_text = f"DECISION_REQUIRED: merge PR #47 → main\n- HEAD: `{head_sha[:8]}`\n"

            completed = cache.completed_pr_numbers(repo, control_text, control_meta)

        self.assertEqual(completed, [47])

    def test_completed_pr_numbers_local_fallback_stays_pending_without_merge_evidence(self) -> None:
        cache = PrMergeStatusCache()
        control_meta = {"reason_code": PR_MERGE_GATE_REASON}
        control_text = "DECISION_REQUIRED: merge PR #48 → main\n"

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch("pipeline_runtime.pr_merge_state.shutil.which", return_value=None),
        ):
            repo = Path(tmp)
            self._init_repo(repo)
            self._commit_file(repo, "base.txt", "base\n")

            completed = cache.completed_pr_numbers(repo, control_text, control_meta)

        self.assertEqual(completed, [])


if __name__ == "__main__":
    unittest.main()
