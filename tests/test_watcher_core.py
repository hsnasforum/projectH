import os
import subprocess
import tempfile
import time
import unittest
import json
import itertools
from pathlib import Path
from unittest import mock

import watcher_core
from pipeline_runtime.automation_health import (
    STALE_ADVISORY_GRACE_CYCLES,
    STALE_CONTROL_CYCLE_THRESHOLD,
)
from pipeline_runtime.operator_autonomy import (
    COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
    OPERATOR_APPROVAL_COMPLETED_REASON,
)
from pipeline_runtime.wrapper_events import append_wrapper_event


def _write_active_profile(root: Path, payload: dict | None = None) -> None:
    active_path = root / ".pipeline" / "config" / "agent_profile.json"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(
        json.dumps(
            payload
            or {
                "schema_version": 1,
                "selected_agents": ["Claude", "Codex", "Gemini"],
                "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
                "role_options": {
                    "advisory_enabled": True,
                    "operator_stop_enabled": True,
                    "session_arbitration_enabled": True,
                },
                "mode_flags": {
                    "single_agent_mode": False,
                    "self_verify_allowed": False,
                    "self_advisory_allowed": False,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _write_work_note(path: Path, changed_files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    changed_lines = "\n".join(f"- `{changed}`" for changed in changed_files) or "- 없음"
    path.write_text(
        "\n".join(
            [
                f"# {path.stem}",
                "",
                "## 변경 파일",
                changed_lines,
                "",
                "## 사용 skill",
                "- 없음",
                "",
                "## 변경 이유",
                "- 테스트",
                "",
                "## 핵심 변경",
                "- 테스트",
                "",
                "## 검증",
                "- 없음",
                "",
                "## 남은 리스크",
                "- 없음",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_verify_note(path: Path, changed_files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    changed_lines = "\n".join(f"- `{changed}`" for changed in changed_files) or "- 없음"
    path.write_text(
        "\n".join(
            [
                f"# {path.stem}",
                "",
                "## 변경 파일",
                changed_lines,
                "",
                "## 사용 skill",
                "- 없음",
                "",
                "## 변경 이유",
                "- 테스트",
                "",
                "## 핵심 변경",
                "- 테스트",
                "",
                "## 검증",
                "- 없음",
                "",
                "## 남은 리스크",
                "- 없음",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_verify_note_for_work(path: Path, work_ref: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"# {path.stem}",
                "",
                "## 변경 파일",
                "- 없음",
                "",
                "## 사용 skill",
                "- 없음",
                "",
                "## 변경 이유",
                f"- `{work_ref}` 검증",
                "",
                "## 핵심 변경",
                f"- `{work_ref}` 기준 재검증",
                "",
                "## 검증",
                "- 없음",
                "",
                "## 남은 리스크",
                "- 없음",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo_with_commit_push(tmp_root: Path, *, push: bool = True) -> tuple[Path, Path]:
    repo = tmp_root / "repo"
    remote = tmp_root / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    _run_git(repo, ["checkout", "-b", "main"])
    _write_active_profile(repo)
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    _run_git(repo, ["add", "."])
    _run_git(
        repo,
        [
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            "commit",
            "-m",
            "initial",
        ],
    )
    if push:
        _run_git(repo, ["remote", "add", "origin", str(remote)])
        _run_git(repo, ["push", "-u", "origin", "main"])
    return repo, remote


def _write_commit_push_operator_request(
    base_dir: Path,
    *,
    seq: int = 44,
    reason_code: str = "approval_required",
    operator_policy: str = "gate_24h",
    decision_class: str = "operator_only",
) -> Path:
    operator_path = base_dir / "operator_request.md"
    operator_path.write_text(
        "\n".join(
            [
                "STATUS: needs_operator",
                f"CONTROL_SEQ: {seq}",
                f"REASON_CODE: {reason_code}",
                f"OPERATOR_POLICY: {operator_policy}",
                f"DECISION_CLASS: {decision_class}",
                "DECISION_REQUIRED: approve completed commit and remote push follow-up",
                "",
                "- commit and push approved boundary",
            ]
        ),
        encoding="utf-8",
    )
    return operator_path


class WorkNoteFilteringTest(unittest.TestCase):
    def test_latest_work_path_skips_metadata_only_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            real_note = watch_dir / "4" / "9" / "2026-04-09-real-implementation.md"
            _write_work_note(real_note, ["docs/PRODUCT_PROPOSAL.md"])
            meta_note = watch_dir / "4" / "9" / "2026-04-09-claude-handoff-task-list-review.md"
            _write_work_note(meta_note, ["work/4/9/2026-04-09-claude-handoff-task-list-review.md"])
            os.utime(meta_note, (real_note.stat().st_atime + 5, real_note.stat().st_mtime + 5))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertEqual(core._get_latest_work_path(), real_note)
            self.assertTrue(core._is_metadata_only_work_note(meta_note))
            self.assertFalse(core._is_dispatchable_work_note(meta_note))

    def test_work_snapshot_ignores_metadata_only_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            meta_note = watch_dir / "4" / "9" / "2026-04-09-claude-handoff-task-list-review.md"
            _write_work_note(meta_note, ["work/4/9/2026-04-09-claude-handoff-task-list-review.md"])

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertEqual(core._get_work_tree_snapshot(), {})
            self.assertIn("4/9/2026-04-09-claude-handoff-task-list-review.md", core._get_work_tree_snapshot_broad())
            self.assertFalse(core._latest_work_needs_verify())

    def test_poll_creates_verify_job_for_latest_metadata_only_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\nCONTROL_SEQ: 8\n", encoding="utf-8")

            meta_note = watch_dir / "4" / "9" / "2026-04-09-claude-handoff-task-list-review.md"
            _write_work_note(meta_note, ["work/4/9/2026-04-09-claude-handoff-task-list-review.md"])

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IDLE, "test_setup")

            with mock.patch.object(core.sm, "step", wraps=core.sm.step) as advance:
                core._poll()

            job_jsons = list((base_dir / "state" / "jobs").glob("*.json"))
            self.assertTrue(any(job_jsons))
            self.assertGreaterEqual(advance.call_count, 1)
            state_payload = json.loads(job_jsons[0].read_text(encoding="utf-8"))
            self.assertEqual(state_payload["artifact_path"], str(meta_note))
            self.assertEqual(state_payload["run_id"], core.run_id)

    def test_claude_active_metadata_only_closeout_releases_to_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\nCONTROL_SEQ: 8\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            meta_note = watch_dir / "4" / "9" / "2026-04-09-claude-handoff-task-list-review.md"
            _write_work_note(meta_note, ["work/4/9/2026-04-09-claude-handoff-task-list-review.md"])

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="> "),
                mock.patch.object(core.sm, "step", wraps=core.sm.step) as advance,
            ):
                core._poll()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IDLE)
            self.assertGreaterEqual(advance.call_count, 1)
            job_jsons = list((base_dir / "state" / "jobs").glob("*.json"))
            self.assertTrue(any(job_jsons))
            state_payload = json.loads(job_jsons[0].read_text(encoding="utf-8"))
            self.assertEqual(state_payload["artifact_path"], str(meta_note))

    def test_latest_unverified_broad_work_ignores_newer_unrelated_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            older_work = watch_dir / "4" / "9" / "2026-04-09-older.md"
            latest_work = watch_dir / "4" / "9" / "2026-04-09-latest-meta.md"
            verify_note = verify_dir / "4" / "9" / "2026-04-09-older-verification.md"
            _write_work_note(older_work, ["docs/PRODUCT_PROPOSAL.md"])
            _write_work_note(latest_work, ["work/4/9/2026-04-09-latest-meta.md"])
            _write_verify_note_for_work(
                verify_note,
                "work/4/9/2026-04-09-older.md",
            )
            now = time.time()
            os.utime(older_work, (now - 30, now - 30))
            os.utime(latest_work, (now - 20, now - 20))
            os.utime(verify_note, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertTrue(core._latest_work_needs_verify_broad())
            self.assertEqual(core._get_latest_verify_candidate_path(), latest_work)

    def test_same_day_verify_lookup_accepts_direct_day_dir_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "4" / "9" / "2026-04-09-latest-meta.md"
            verify_note = verify_dir / "4" / "9" / "2026-04-09-latest-meta-verification.md"
            _write_work_note(work_note, ["work/4/9/2026-04-09-latest-meta.md"])
            _write_verify_note_for_work(
                verify_note,
                "work/4/9/2026-04-09-latest-meta.md",
            )
            now = time.time()
            os.utime(work_note, (now - 20, now - 20))
            os.utime(verify_note, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertEqual(core._get_latest_same_day_verify_path_for_work(work_note), verify_note)
            self.assertTrue(core._work_has_matching_verify(work_note))

    def test_verify_lookup_accepts_cross_day_note_when_it_references_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "4" / "19" / "2026-04-19-latest-meta.md"
            verify_note = verify_dir / "4" / "20" / "2026-04-20-latest-meta-verification.md"
            _write_work_note(work_note, ["work/4/19/2026-04-19-latest-meta.md"])
            _write_verify_note_for_work(
                verify_note,
                "work/4/19/2026-04-19-latest-meta.md",
            )
            now = time.time()
            os.utime(work_note, (now - 20, now - 20))
            os.utime(verify_note, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertEqual(core._get_latest_same_day_verify_path_for_work(work_note), verify_note)
            self.assertTrue(core._work_has_matching_verify(work_note))

    def test_same_day_verify_lookup_rejects_multiple_unrelated_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "4" / "9" / "2026-04-09-latest-meta.md"
            verify_a = verify_dir / "4" / "9" / "2026-04-09-a-verification.md"
            verify_b = verify_dir / "4" / "9" / "2026-04-09-b-verification.md"
            _write_work_note(work_note, ["work/4/9/2026-04-09-latest-meta.md"])
            verify_a.parent.mkdir(parents=True, exist_ok=True)
            verify_a.write_text("# verify a\n", encoding="utf-8")
            verify_b.write_text("# verify b\n", encoding="utf-8")
            now = time.time()
            os.utime(work_note, (now - 20, now - 20))
            os.utime(verify_a, (now - 10, now - 10))
            os.utime(verify_b, (now, now))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._get_latest_same_day_verify_path_for_work(work_note))
            self.assertFalse(core._work_has_matching_verify(work_note))

    def test_latest_verify_candidate_skips_work_with_same_day_matching_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "4" / "9" / "2026-04-09-latest-meta.md"
            verify_note = verify_dir / "4" / "9" / "2026-04-09-latest-meta-verification.md"
            _write_work_note(work_note, ["work/4/9/2026-04-09-latest-meta.md"])
            _write_verify_note_for_work(
                verify_note,
                "work/4/9/2026-04-09-latest-meta.md",
            )
            now = time.time()
            os.utime(work_note, (now - 20, now - 20))
            os.utime(verify_note, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertFalse(core._latest_work_needs_verify_broad())
            self.assertIsNone(core._get_latest_verify_candidate_path())

    def test_latest_verify_candidate_skips_work_with_cross_day_matching_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "4" / "19" / "2026-04-19-latest-meta.md"
            verify_note = verify_dir / "4" / "20" / "2026-04-20-latest-meta-verification.md"
            _write_work_note(work_note, ["work/4/19/2026-04-19-latest-meta.md"])
            _write_verify_note_for_work(
                verify_note,
                "work/4/19/2026-04-19-latest-meta.md",
            )
            now = time.time()
            os.utime(work_note, (now - 20, now - 20))
            os.utime(verify_note, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertFalse(core._latest_work_needs_verify_broad())
            self.assertIsNone(core._get_latest_verify_candidate_path())

    def test_latest_verify_candidate_ignores_older_unverified_backlog_when_latest_work_is_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            older_work = watch_dir / "4" / "19" / "2026-04-19-older.md"
            latest_work = watch_dir / "4" / "20" / "2026-04-20-latest.md"
            latest_verify = verify_dir / "4" / "20" / "2026-04-20-latest-verification.md"
            _write_work_note(older_work, ["watcher_core.py"])
            _write_work_note(latest_work, ["verify_fsm.py"])
            _write_verify_note_for_work(
                latest_verify,
                "work/4/20/2026-04-20-latest.md",
            )
            now = time.time()
            os.utime(older_work, (now - 30, now - 30))
            os.utime(latest_work, (now - 20, now - 20))
            os.utime(latest_verify, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertFalse(core._latest_work_needs_verify())
            self.assertFalse(core._latest_work_needs_verify_broad())
            self.assertIsNone(core._get_latest_verify_candidate_path())
            self.assertFalse(core._handoff_verify_blocker_exists(0.0))

    def test_poll_does_not_reopen_older_unverified_backlog_when_latest_work_is_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            older_work = watch_dir / "4" / "19" / "2026-04-19-older.md"
            latest_work = watch_dir / "4" / "20" / "2026-04-20-latest.md"
            latest_verify = verify_dir / "4" / "20" / "2026-04-20-latest-verification.md"
            _write_work_note(older_work, ["watcher_core.py"])
            _write_work_note(latest_work, ["verify_fsm.py"])
            _write_verify_note_for_work(
                latest_verify,
                "work/4/20/2026-04-20-latest.md",
            )
            now = time.time()
            os.utime(older_work, (now - 30, now - 30))
            os.utime(latest_work, (now - 20, now - 20))
            os.utime(latest_verify, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IDLE, "test_setup")

            with mock.patch.object(core.sm, "step", side_effect=AssertionError("stale backlog should not dispatch")):
                core._poll()

            self.assertFalse(any((base_dir / "state" / "jobs").glob("*.json")))

    def test_verify_feedback_sig_detects_cross_day_verify_tree_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "4" / "19" / "2026-04-19-latest-meta.md"
            _write_work_note(work_note, ["work/4/19/2026-04-19-latest-meta.md"])

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            job_id = watcher_core.make_job_id(watch_dir, work_note)
            job = watcher_core.JobState.from_artifact(job_id, str(work_note), run_id=core.run_id)

            _, before_sig = core._build_verify_feedback_sigs(job)

            verify_note = verify_dir / "4" / "20" / "2026-04-20-latest-meta-verification.md"
            _write_verify_note_for_work(
                verify_note,
                "work/4/19/2026-04-19-latest-meta.md",
            )

            _, after_sig = core._build_verify_feedback_sigs(job)

            self.assertNotEqual(before_sig, after_sig)


class StateArchiveCleanupTest(unittest.TestCase):
    def test_startup_archives_previous_run_nonterminal_job_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            stale_state = state_dir / "job-old.json"
            stale_state.write_text(
                json.dumps(
                    {
                        "job_id": "job-old",
                        "run_id": "run-old",
                        "status": "VERIFY_PENDING",
                        "artifact_path": str(watch_dir / "old.md"),
                        "updated_at": time.time() - 30.0,
                    }
                ),
                encoding="utf-8",
            )

            watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            archived = base_dir / "runs" / "run-old" / "state-archive" / "job-old.json"
            self.assertFalse(stale_state.exists())
            self.assertTrue(archived.exists())

    def test_startup_keeps_previous_run_verify_done_state_in_shared_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            done_state = state_dir / "job-done.json"
            done_state.write_text(
                json.dumps(
                    {
                        "job_id": "job-done",
                        "run_id": "run-old",
                        "status": "VERIFY_DONE",
                        "artifact_path": str(watch_dir / "done.md"),
                        "updated_at": time.time() - 30.0,
                    }
                ),
                encoding="utf-8",
            )

            watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            archived = base_dir / "runs" / "run-old" / "state-archive" / "job-done.json"
            self.assertTrue(done_state.exists())
            self.assertFalse(archived.exists())

    def test_startup_archives_old_legacy_nonterminal_job_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            legacy_state = state_dir / "job-legacy.json"
            legacy_state.write_text(
                json.dumps(
                    {
                        "job_id": "job-legacy",
                        "status": "VERIFY_RUNNING",
                        "artifact_path": str(watch_dir / "legacy.md"),
                        "updated_at": time.time() - 20.0,
                    }
                ),
                encoding="utf-8",
            )
            old_ts = time.time() - 20.0
            os.utime(legacy_state, (old_ts, old_ts))

            watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "state_cleanup_legacy_grace_sec": 1.0,
                }
            )

            archived = base_dir / "state-archive" / "legacy" / "job-legacy.json"
            self.assertFalse(legacy_state.exists())
            self.assertTrue(archived.exists())

    def test_runtime_run_id_env_overrides_generated_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "state").mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            with mock.patch.dict(
                os.environ,
                {
                    "PIPELINE_RUNTIME_DISABLE_EXPORTER": "1",
                    "PIPELINE_RUNTIME_RUN_ID": "run-sync-42",
                },
                clear=False,
            ):
                core = watcher_core.WatcherCore(
                    {
                        "watch_dir": str(watch_dir),
                        "base_dir": str(base_dir),
                        "repo_root": str(root),
                        "dry_run": True,
                    }
                )

            self.assertEqual(core.run_id, "run-sync-42")


class PanePromptDetectionTest(unittest.TestCase):
    def test_gemini_text_prompt_counts_as_input_ready(self) -> None:
        text = "\n".join(
            [
                "Gemini CLI",
                "Type your message",
                "workspace",
            ]
        )

        self.assertTrue(watcher_core._pane_text_has_input_cursor(text))

    def test_gemini_current_cli_prompt_counts_as_input_ready(self) -> None:
        text = "\n".join(
            [
                "Gemini CLI v0.38.1",
                "YOLO Ctrl+Y",
                "*   Type your message or @path/to/file",
                "workspace              sandbox",
            ]
        )

        self.assertTrue(watcher_core._pane_text_has_input_cursor(text))

    def test_non_prompt_text_does_not_count_as_input_ready(self) -> None:
        text = "\n".join(
            [
                "Recommendation:",
                "- proceed with the bounded implement handoff",
            ]
        )

        self.assertFalse(watcher_core._pane_text_has_input_cursor(text))

    def test_old_busy_scrollback_does_not_block_current_ready_prompt(self) -> None:
        text = "\n".join(
            [
                "• Working (22s • esc to interrupt)",
                *[f"older output line {idx}" for idx in range(24)],
                "How is Claude doing this session? (optional)",
                "❯ ",
                "  ⏵⏵ bypass permissions on (shift+tab to cycle)",
            ]
        )

        self.assertTrue(watcher_core._pane_text_has_input_cursor(text))
        self.assertFalse(watcher_core._pane_text_has_busy_indicator(text))
        self.assertTrue(watcher_core._pane_text_is_idle(text))

    def test_claude_code_prompt_after_busy_tail_counts_as_ready(self) -> None:
        text = "\n".join(
            [
                "Working (synthetic claude verify)",
                "Claude Code",
                "❯",
            ]
        )

        self.assertTrue(watcher_core._pane_text_has_input_cursor(text))
        self.assertFalse(watcher_core._pane_text_has_busy_indicator(text))
        self.assertTrue(watcher_core._pane_text_is_idle(text))


class LiveSessionEscalationTest(unittest.TestCase):
    def test_extract_live_session_escalation_detects_expected_reasons(self) -> None:
        text = """
이 세션에서 이미 28건의 동일 family smoke를 수행했고 context window가 매우 소진된 상태입니다.
새 세션에서 이어가시는 것을 강하게 권고드립니다.
그래도 진행을 원하시면 handoff를 확인하겠지만, 진행할까요?
"""
        signal = watcher_core._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )
        self.assertTrue(signal["fingerprint"])

    def test_extract_live_session_escalation_detects_additional_phrase_variants(self) -> None:
        text = """
The context exhausted warning says the window is nearly full.
Please start a new session for the next slice.
Should I continue here or handoff and continue in a fresh session?
"""
        signal = watcher_core._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )

    def test_extract_live_session_escalation_ignores_old_scrollback_matches(self) -> None:
        old_lines = [
            "context window is nearly full",
            "please start a new session",
            "should i continue here?",
        ]
        recent_lines = [f"recent output line {i}" for i in range(20)]
        text = "\n".join(old_lines + recent_lines)

        signal = watcher_core._extract_live_session_escalation(text)

        self.assertIsNone(signal)

    def test_extract_live_session_escalation_detects_semantic_fallback_combo(self) -> None:
        text = """
최근 답변이 너무 길어져서 이 대화는 거의 가득 찬 것 같습니다.
다음 세션에서 이어가는 편이 안전하겠습니다.
여기서 계속 진행할지, handoff로 넘길지 정할까요?
"""

        signal = watcher_core._extract_live_session_escalation(text)

        self.assertIsNotNone(signal)
        self.assertEqual(
            signal["reasons"],
            ["context_exhaustion", "session_rollover", "continue_vs_switch"],
        )

    def test_waiting_for_claude_writes_noncanonical_session_arbitration_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
>
""",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]), \
                 mock.patch("watcher_core._is_pane_dead", return_value=False):
                core._poll()

            draft_path = base_dir / "session_arbitration_draft.md"
            self.assertTrue(draft_path.exists())
            content = draft_path.read_text()
            self.assertIn("STATUS: draft_only", content)
            self.assertIn("non-canonical draft", content)
            self.assertIn(".pipeline/claude_handoff.md", content)
            self.assertFalse((base_dir / "gemini_request.md").exists())

    def test_waiting_for_claude_skips_draft_until_all_three_panes_are_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            busy_snapshots = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
>
""",
                "codex-pane": "• Working (36s • esc to interrupt)\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: busy_snapshots[target]):
                core._poll()

            self.assertFalse((base_dir / "session_arbitration_draft.md").exists())

    def test_waiting_for_claude_allows_settled_escalation_even_if_claude_prompt_lags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "session_arbitration_settle_sec": 3.0,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
""",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]), \
                 mock.patch("watcher_core._is_pane_dead", return_value=False):
                core._poll()
                self.assertFalse((base_dir / "session_arbitration_draft.md").exists())
                fingerprint = watcher_core.hashlib.sha1(
                    pane_texts["claude-pane"].encode("utf-8")
                ).hexdigest()
                core._session_arbitration_snapshot_fingerprints["claude"] = fingerprint
                core._session_arbitration_snapshot_changed_at["claude"] = 0.0
                with mock.patch("watcher_core.time.time", return_value=10.0):
                    core._poll()

            draft_path = base_dir / "session_arbitration_draft.md"
            self.assertTrue(draft_path.exists())

    def test_waiting_for_claude_clears_draft_when_claude_activity_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
>
""",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]), \
                 mock.patch("watcher_core._is_pane_dead", return_value=False):
                with mock.patch.object(core, "_get_work_tree_snapshot_broad", side_effect=[{}, {}, {"work.md": "changed"}, {"work.md": "changed"}]):
                    core._poll()
                    self.assertTrue((base_dir / "session_arbitration_draft.md").exists())
                    core._poll()

            draft_path = base_dir / "session_arbitration_draft.md"
            self.assertFalse(draft_path.exists())
            self.assertNotEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)

    def test_same_fingerprint_is_suppressed_during_cooldown_after_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "session_arbitration_cooldown_sec": 300.0,
                }
            )
            signal = {
                "reasons": ["context_exhaustion"],
                "excerpt_lines": ["context window is full"],
                "fingerprint": "same-fingerprint",
            }

            with mock.patch("watcher_core.time.time", return_value=100.0):
                self.assertTrue(core._write_session_arbitration_draft(signal))
                self.assertTrue(core.session_arbitration_draft_path.exists())
                core._clear_session_arbitration_draft("test_resolved")
                self.assertFalse(core.session_arbitration_draft_path.exists())

            with mock.patch("watcher_core.time.time", return_value=200.0):
                self.assertFalse(core._write_session_arbitration_draft(signal))
                self.assertFalse(core.session_arbitration_draft_path.exists())

            with mock.patch("watcher_core.time.time", return_value=450.0):
                self.assertTrue(core._write_session_arbitration_draft(signal))
                self.assertTrue(core.session_arbitration_draft_path.exists())

    def test_waiting_for_claude_skips_draft_when_any_lane_is_dead(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": """
이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.
context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.
진행할까요?
>
""",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            def fake_dead(target: str) -> bool:
                return target == "codex-pane"

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core._is_pane_dead", side_effect=fake_dead):
                    core._poll()

            self.assertFalse((base_dir / "session_arbitration_draft.md").exists())


class WatcherPromptAssemblyTest(unittest.TestCase):
    def test_claude_dispatch_spec_carries_notify_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 41\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            spec = core.prompt_assembler.build_claude_dispatch_spec("startup_turn_claude")

            self.assertEqual(spec.lane_role, "implement")
            self.assertEqual(spec.functional_role, "implement")
            self.assertEqual(spec.lane_id, "claude_implement")
            self.assertEqual(spec.agent_kind, "claude")
            self.assertEqual(spec.notify_label, "notify_implement_owner")
            self.assertEqual(spec.raw_event, "implement_notify")
            self.assertEqual(spec.raw_payload["reason"], "startup_turn_claude")
            self.assertEqual(spec.raw_payload["functional_role"], "implement")
            self.assertEqual(spec.raw_payload["lane_id"], "claude_implement")
            self.assertEqual(spec.raw_payload["agent_kind"], "claude")
            self.assertEqual(spec.expected_status, "implement")
            self.assertEqual(spec.control_seq, 41)

    def test_blocked_triage_spec_carries_raw_event_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 52\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            signal = {
                "reason": "handoff_already_completed",
                "reason_code": "already_implemented",
                "escalation_class": "codex_triage",
                "fingerprint": "block-123",
                "source": "sentinel",
            }

            spec = core.prompt_assembler.build_blocked_triage_dispatch_spec(signal, "claude_implement_blocked")

            self.assertEqual(spec.lane_role, "verify")
            self.assertEqual(spec.notify_label, "notify_verify_blocked_triage")
            self.assertEqual(spec.raw_event, "verify_blocked_triage_notify")
            self.assertEqual(spec.raw_payload["reason"], "claude_implement_blocked")
            self.assertEqual(spec.raw_payload["blocked_reason"], "handoff_already_completed")
            self.assertEqual(spec.raw_payload["blocked_reason_code"], "already_implemented")
            self.assertEqual(spec.raw_payload["blocked_escalation_class"], "codex_triage")
            self.assertEqual(spec.raw_payload["blocked_fingerprint"], "block-123")
            self.assertTrue(spec.raw_payload["handoff_sha"])

    def test_operator_retriage_prompt_keeps_commit_push_in_verify_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            prompt = core.prompt_assembler.format_operator_retriage_prompt(
                {
                    "control_seq": 713,
                    "reason": COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
                    "operator_wait_age_sec": 0,
                }
            )

            self.assertIn("commit_push_bundle_authorization + internal_only", prompt)
            self.assertIn("perform the scoped commit/push in this verify/handoff round", prompt)
            self.assertIn("do not hand commit/push work to the implement lane", prompt)

    def test_blocked_triage_prompt_rejects_commit_push_reissue_to_implement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            handoff = base_dir / "claude_handoff.md"
            handoff.write_text(
                "STATUS: implement\n"
                "CONTROL_SEQ: 714\n"
                "REASON_CODE: commit_push_bundle_authorization\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            spec = core.prompt_assembler.build_blocked_triage_dispatch_spec(
                {
                    "reason": "commit_push_forbidden_by_lane_rules",
                    "reason_code": "handoff_requires_commit_push_but_rules_forbid_commit_push",
                    "escalation_class": "codex_triage",
                    "fingerprint": "block-commit-push",
                    "source": "sentinel",
                },
                "claude_implement_blocked",
            )

            self.assertIn("commit/push is forbidden by implement-lane rules", spec.prompt)
            self.assertIn("do not reissue commit/push as `.pipeline/claude_handoff.md`", spec.prompt)

    def test_session_arbitration_draft_format_moves_body_to_assembler(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work" / "4" / "17"
            base_dir = root / ".pipeline"
            verify_dir = root / "verify" / "4" / "17"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\nCONTROL_SEQ: 61\n", encoding="utf-8")
            _write_work_note(watch_dir / "2026-04-17-sample-work.md", ["app/sample.py"])
            _write_verify_note(verify_dir / "2026-04-17-sample-verify.md", ["app/sample.py"])

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            signal = {
                "reasons": ["context_exhaustion", "continue_vs_switch"],
                "excerpt_lines": ["context window is full", "continue or switch?"],
                "fingerprint": "draft-1",
            }

            body = core.prompt_assembler.format_session_arbitration_draft(signal)

            self.assertIn("STATUS: draft_only", body)
            self.assertIn("non-canonical draft", body)
            self.assertIn("context_exhaustion", body)
            self.assertIn("continue_vs_switch", body)
            self.assertIn(".pipeline/claude_handoff.md", body)
            self.assertIn("latest `/work`", body)
            self.assertIn("latest `/verify`", body)

    def test_notify_codex_followup_wrapper_uses_dispatch_helper_with_assembler_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "gemini_advice.md").write_text(
                "STATUS: advice_ready\nCONTROL_SEQ: 77\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            with mock.patch.object(core, "_dispatch_notify_spec", return_value=True) as dispatch_notify:
                core._notify_codex_followup("gemini_advice_ready")

            dispatch_notify.assert_called_once()
            kwargs = dispatch_notify.call_args.kwargs
            spec = kwargs["spec"]
            self.assertEqual(kwargs["reason"], "gemini_advice_ready")
            self.assertEqual(spec.lane_role, "verify")
            self.assertEqual(spec.functional_role, "verify")
            self.assertEqual(spec.lane_id, "codex_verify")
            self.assertEqual(spec.agent_kind, "codex")
            self.assertEqual(spec.notify_kind, "gemini_advice_followup")
            self.assertEqual(spec.pending_key, "codex_verify:gemini_advice_followup:77")
            self.assertEqual(spec.notify_label, "notify_verify_followup")
            self.assertEqual(spec.raw_event, "verify_followup_notify")
            self.assertEqual(spec.raw_payload["reason"], "gemini_advice_ready")
            self.assertEqual(spec.raw_payload["functional_role"], "verify")
            self.assertEqual(spec.raw_payload["lane_id"], "codex_verify")
            self.assertEqual(spec.raw_payload["agent_kind"], "codex")
            self.assertEqual(spec.control_seq, 77)
            self.assertEqual(spec.expected_status, "advice_ready")
            self.assertEqual(spec.expected_control_path, "gemini_advice.md")
            self.assertEqual(spec.expected_control_seq, 77)
            self.assertTrue(spec.require_active_control)


class ClaudeImplementBlockedTest(unittest.TestCase):
    def test_extract_implement_blocked_accepts_bulleted_status_line(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "• STATUS: implement_blocked",
                    "  BLOCK_REASON: conflict_count_owner_out_of_scope",
                    "  BLOCK_REASON_CODE: scope_missing_owner",
                    "  REQUEST: codex_triage",
                    "  ESCALATION_CLASS: codex_triage",
                    "  HANDOFF: .pipeline/claude_handoff.md",
                    "  HANDOFF_SHA: abcdef1234567890",
                    "  BLOCK_ID: block-bullet-001",
                    "› Summarize recent commits",
                ]
            ),
            active_handoff_path=".pipeline/claude_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason"], "conflict_count_owner_out_of_scope")
        self.assertEqual(signal["reason_code"], "scope_missing_owner")
        self.assertEqual(signal["fingerprint"], "block-bullet-001")

    def test_extract_implement_blocked_tolerates_wrapped_handoff_fields(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: smoke_handoff_blocked",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/live-blocked-smoke-j3",
                    "YWbK/claude_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "fedcba0987654321",
                    "BLOCK_ID: abcdef1234567890fedc",
                    "ba0987654321:smoke_handoff_blocked",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/live-blocked-smoke-j3YWbK/claude_handoff.md",
            active_handoff_sha="abcdef1234567890fedcba0987654321",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason"], "smoke_handoff_blocked")
        self.assertEqual(signal["fingerprint"], "abcdef1234567890fedcba0987654321:smoke_handoff_blocked")

    def test_extract_implement_blocked_tolerates_wrapped_status_and_reason(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS:",
                    "implement_blocked",
                    "BLOCK_REASON:",
                    "renderResult follow-up",
                    "correctly drops review-outcome",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/claud",
                    "e_handoff.md",
                    "HANDOFF_SHA:",
                    "abcdef1234567890",
                    "fedcba0987654321",
                    "BLOCK_ID:",
                    "abcdef1234567890",
                    "fedcba0987654321:renderResult-follow-up",
                    "분석 결과:",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/claude_handoff.md",
            active_handoff_sha="abcdef1234567890fedcba0987654321",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason"], "renderresult follow-up correctly drops review-outcome")
        self.assertEqual(signal["fingerprint"], "abcdef1234567890fedcba0987654321:renderResult-follow-up")

    def test_extract_implement_blocked_prefers_structured_reason_code_and_escalation_class(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: context window exhausted after diff review",
                    "BLOCK_REASON_CODE: context_exhaustion",
                    "REQUEST: codex_triage",
                    "ESCALATION_CLASS: codex_triage",
                    "HANDOFF: .pipeline/claude_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "BLOCK_ID: block-structured-001",
                ]
            ),
            active_handoff_path=".pipeline/claude_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["reason_code"], "context_exhaustion")
        self.assertEqual(signal["escalation_class"], "codex_triage")
        self.assertEqual(signal["request"], "codex_triage")

    def test_extract_implement_blocked_ignores_prompt_template_example(self) -> None:
        signal = watcher_core._extract_claude_implement_blocked_signal(
            "\n".join(
                [
                    "- if the handoff is blocked or not actionable, emit the exact sentinel below and stop",
                    "BLOCKED_SENTINEL:",
                    "STATUS: implement_blocked",
                    "BLOCK_REASON: <short_reason>",
                    "REQUEST: verify_triage",
                    "HANDOFF: .pipeline/claude_handoff.md",
                    "HANDOFF_SHA: abcdef1234567890",
                    "BLOCK_ID: abcdef1234567890:<short_reason>",
                    ">",
                ]
            ),
            active_handoff_path=".pipeline/claude_handoff.md",
            active_handoff_sha="abcdef1234567890",
        )

        self.assertIsNone(signal)

    def test_waiting_for_claude_routes_explicit_implement_blocked_to_codex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            handoff_sha = watcher_core.compute_file_sha256(handoff_path)
            pane_texts = {
                "claude-pane": (
                    "STATUS: implement_blocked\n"
                    "BLOCK_REASON: handoff_not_actionable\n"
                    "BLOCK_REASON_CODE: codex_triage_only\n"
                    "REQUEST: codex_triage\n"
                    "ESCALATION_CLASS: codex_triage\n"
                    "HANDOFF: .pipeline/claude_handoff.md\n"
                    f"HANDOFF_SHA: {handoff_sha}\n"
                    "BLOCK_ID: block-001\n"
                ),
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    core._poll()

            send.assert_called_once()
            args, kwargs = send.call_args
            self.assertEqual(args[0], "codex-pane")
            self.assertIn("ROLE: verify_triage", args[1])
            self.assertIn("OWNER: Codex", args[1])
            self.assertIn("BLOCK_REASON: handoff_not_actionable", args[1])
            self.assertIn("BLOCK_REASON_CODE: codex_triage_only", args[1])
            self.assertIn("ESCALATION_CLASS: codex_triage", args[1])
            self.assertIn("BLOCK_ID: block-001", args[1])
            self.assertEqual(kwargs.get("pane_type"), "codex")
            self.assertEqual(core._last_claude_blocked_fingerprint, "block-001")

    def test_waiting_for_role_bound_implement_owner_routes_bulleted_blocked_signal_to_verify_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex", "Gemini"],
                    "role_bindings": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "role_options": {
                        "advisory_enabled": True,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": True,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            handoff_sha = watcher_core.compute_file_sha256(handoff_path)
            pane_texts = {
                "codex-pane": (
                    "• STATUS: implement_blocked\n"
                    "  BLOCK_REASON: conflict_count_owner_out_of_scope\n"
                    "  BLOCK_REASON_CODE: scope_missing_owner\n"
                    "  REQUEST: codex_triage\n"
                    "  ESCALATION_CLASS: codex_triage\n"
                    "  HANDOFF: .pipeline/claude_handoff.md\n"
                    f"  HANDOFF_SHA: {handoff_sha}\n"
                    "  BLOCK_ID: block-role-bound-001\n"
                    "› Summarize recent commits\n"
                ),
                "claude-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    core._poll()

            send.assert_called_once()
            args, kwargs = send.call_args
            self.assertEqual(args[0], "claude-pane")
            self.assertIn("ROLE: verify_triage", args[1])
            self.assertIn("OWNER: Claude", args[1])
            self.assertIn("BLOCK_REASON: conflict_count_owner_out_of_scope", args[1])
            self.assertIn("BLOCK_REASON_CODE: scope_missing_owner", args[1])
            self.assertIn("BLOCK_ID: block-role-bound-001", args[1])
            self.assertEqual(kwargs.get("pane_type"), "claude")
            self.assertEqual(core._last_claude_blocked_fingerprint, "block-role-bound-001")

    def test_same_block_id_is_not_redispatched_while_outstanding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            handoff_sha = watcher_core.compute_file_sha256(handoff_path)
            pane_texts = {
                "claude-pane": (
                    "STATUS: implement_blocked\n"
                    "BLOCK_REASON: handoff_not_actionable\n"
                    "REQUEST: codex_triage\n"
                    "HANDOFF: .pipeline/claude_handoff.md\n"
                    f"HANDOFF_SHA: {handoff_sha}\n"
                    "BLOCK_ID: block-dedupe\n"
                ),
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    core._poll()
                    core._poll()

            self.assertEqual(send.call_count, 1)
            self.assertEqual(core._last_claude_blocked_fingerprint, "block-dedupe")

    def test_uncorroborated_materialized_block_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            target_doc = root / "docs" / "projectH_pipeline_runtime_docs" / "05_운영_RUNBOOK.md"
            target_doc.parent.mkdir(parents=True, exist_ok=True)
            target_doc.write_text(
                "\n".join(
                    [
                        "## 3.5 현재 검증 원칙",
                        "현재 기본 검증은 아래 세 축입니다.",
                    ]
                ),
                encoding="utf-8",
            )

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text(
                "\n".join(
                    [
                        "STATUS: implement",
                        "CONTROL_SEQ: 581",
                        "EDIT EXACTLY ONE FILE:",
                        "- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`",
                        "CURRENT SENTENCE TO REPLACE (file line 74, byte-exact):",
                        "- `현재 기본 검증은 아래 세 축입니다.`",
                        "REPLACEMENT SENTENCE (byte-exact, keep the backticks around the command):",
                        "- `현재 기본 검증은 아래 세 축이며, thin-client/UI current-truth read-model 회귀의 focused baseline으로 \\`python3 -m unittest tests.test_pipeline_gui_backend\\` 46 green을 함께 유지합니다.`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            handoff_sha = watcher_core.compute_file_sha256(handoff_path)
            pane_texts = {
                "claude-pane": (
                    "STATUS: implement_blocked\n"
                    "BLOCK_REASON: slice_already_materialized\n"
                    "BLOCK_REASON_CODE: handoff_already_applied\n"
                    "REQUEST: codex_triage\n"
                    "ESCALATION_CLASS: codex_triage\n"
                    "HANDOFF: .pipeline/claude_handoff.md\n"
                    f"HANDOFF_SHA: {handoff_sha}\n"
                    "BLOCK_ID: block-materialized-false-positive\n"
                ),
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    core._poll()

            send.assert_not_called()
            self.assertEqual(core._last_claude_blocked_fingerprint, "")
            raw_events = [
                json.loads(line)
                for line in (core.events_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertFalse(any(event["event"] == "implement_blocked_detected" for event in raw_events))
            ignored = [event for event in raw_events if event["event"] == "implement_blocked_ignored"]
            self.assertEqual(len(ignored), 1)
            self.assertEqual(ignored[0]["ignore_reason"], "materialization_uncorroborated")

    def test_deferred_blocked_triage_is_not_redispatched_while_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            handoff_sha = watcher_core.compute_file_sha256(handoff_path)
            pane_texts = {
                "claude-pane": (
                    "STATUS: implement_blocked\n"
                    "BLOCK_REASON: handoff_not_actionable\n"
                    "REQUEST: codex_triage\n"
                    "HANDOFF: .pipeline/claude_handoff.md\n"
                    f"HANDOFF_SHA: {handoff_sha}\n"
                    "BLOCK_ID: block-deferred-dedupe\n"
                ),
                "codex-pane": "• Working (22s • esc to interrupt)\n",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    core._poll()
                    core._poll()

            send.assert_not_called()
            self.assertEqual(core._last_claude_blocked_fingerprint, "block-deferred-dedupe")
            self.assertEqual(len(core.dispatch_queue.pending_notifications), 1)
            pending_key = next(iter(core.dispatch_queue.pending_notifications))
            self.assertEqual(pending_key, "codex_verify:codex_blocked_triage:na")
            raw_events = [
                json.loads(line)
                for line in (core.events_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            detected = [event for event in raw_events if event["event"] == "implement_blocked_detected"]
            self.assertEqual(len(detected), 1)

    def test_forbidden_operator_menu_soft_blocks_after_settle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                    "implement_blocked_settle_sec": 3.0,
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": "진행 전에 다음 중 하나를 선택해 주세요.\n1. operator에게 묻기\n2. 나중에 진행\n> ",
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    with mock.patch("watcher_core.time.time", return_value=10.0):
                        core._poll()
                    self.assertEqual(send.call_count, 0)
                    with mock.patch("watcher_core.time.time", return_value=20.0):
                        core._poll()

            self.assertEqual(send.call_count, 1)
            args, _ = send.call_args
            self.assertIn("BLOCK_REASON: forbidden_operator_menu", args[1])

    def test_already_completed_handoff_soft_blocks_after_settle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                    "implement_blocked_settle_sec": 3.0,
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "claude-pane": (
                    "No uncommitted changes in either file. Let me check if the latest commit already addressed these.\n"
                    "The work described in the handoff was already completed in commits 2edf687 and 43e6099.\n"
                    "이 슬라이스에 추가로 변경할 파일이 없으므로 구현 작업 없이 완료입니다.\n> "
                ),
                "codex-pane": "• Done\n> ",
                "gemini-pane": "✦ Finished\n> ",
            }

            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts[target]):
                with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                    with mock.patch("watcher_core.time.time", return_value=10.0):
                        core._poll()
                    self.assertEqual(send.call_count, 0)
                    with mock.patch("watcher_core.time.time", return_value=20.0):
                        core._poll()
                    with mock.patch("watcher_core.time.time", return_value=21.0):
                        core._poll()

            self.assertEqual(send.call_count, 1)
            args, _ = send.call_args
            self.assertIn("BLOCK_REASON: handoff_already_completed", args[1])
            raw_events = [
                json.loads(line)
                for line in (core.events_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            notify = [event for event in raw_events if event.get("event") == "verify_blocked_triage_notify"]
            self.assertEqual(len(notify), 1)
            self.assertTrue(str(notify[0].get("handoff_sha") or ""))
            self.assertNotIn("legacy_event", notify[0])

    def test_newer_handoff_remains_active_when_older_operator_request_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            operator_path = base_dir / "operator_request.md"
            handoff_path = base_dir / "claude_handoff.md"
            operator_path.write_text("STATUS: needs_operator\n")
            handoff_path.write_text("STATUS: implement\n")
            os.utime(operator_path, (100.0, 100.0))
            os.utime(handoff_path, (200.0, 200.0))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, handoff_path)
            self.assertEqual(core._get_pending_operator_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "claude")

    def test_higher_control_seq_beats_newer_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            request_path = base_dir / "gemini_request.md"
            handoff_path = base_dir / "claude_handoff.md"
            request_path.write_text("STATUS: request_open\nCONTROL_SEQ: 8\n")
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 7\n")
            os.utime(request_path, (100.0, 100.0))
            os.utime(handoff_path, (200.0, 200.0))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, request_path)
            self.assertEqual(active.control_seq, 8)
            self.assertEqual(core._resolve_turn(), "gemini")

    def test_stale_gemini_slots_do_not_block_newer_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            request_path = base_dir / "gemini_request.md"
            advice_path = base_dir / "gemini_advice.md"
            handoff_path = base_dir / "claude_handoff.md"
            request_path.write_text("STATUS: request_open\nCONTROL_SEQ: 2\n")
            advice_path.write_text("STATUS: advice_ready\nCONTROL_SEQ: 3\n")
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 4\n")
            os.utime(request_path, (300.0, 300.0))
            os.utime(advice_path, (200.0, 200.0))
            os.utime(handoff_path, (100.0, 100.0))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, handoff_path)
            self.assertEqual(core._get_pending_gemini_request_mtime(), 0.0)
            self.assertEqual(core._get_pending_gemini_advice_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "claude")


class PaneLeaseOwnerPidWiringTest(unittest.TestCase):
    def test_watchercore_wires_owner_pid_path_even_when_supervisor_pid_missing(self) -> None:
        # owner_pid_path는 watcher init 시점의 supervisor.pid 존재 여부와 무관하게 항상
        # 동일 경로를 가리켜야 한다. 이전에는 init 시점에 파일이 없으면 None으로 영구 고정되어
        # supervisor가 나중에 떠도/죽어도 stale lease가 TTL까지 안 풀렸다.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.assertFalse((base_dir / "supervisor.pid").exists())
            _write_active_profile(root)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            self.assertEqual(core.lease.owner_pid_path, base_dir / "supervisor.pid")

    def test_owner_dead_returns_false_when_supervisor_pid_missing(self) -> None:
        # supervisor.pid 파일 부재를 "owner dead"로 해석하면 standalone watcher 경로에서
        # 매 check마다 lease가 즉시 clear되어 verify active detection이 영구적으로 False가
        # 된다. 파일 부재는 "감시 대상 없음"으로 보수적으로 다룬다.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            lock_dir = base_dir / "locks"
            base_dir.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir(parents=True, exist_ok=True)

            supervisor_pid = base_dir / "supervisor.pid"
            self.assertFalse(supervisor_pid.exists())

            lease = watcher_core.PaneLease(
                lock_dir,
                default_ttl=900,
                dry_run=False,
                owner_pid_path=supervisor_pid,
            )
            self.assertFalse(lease._owner_dead())

            self.assertTrue(lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900))
            # supervisor.pid가 없어도 lease는 계속 active로 남아야 한다.
            self.assertTrue(lease.is_active("slot_verify"))
            self.assertTrue((lock_dir / "slot_verify.lock").exists())

    def test_owner_dead_returns_false_when_supervisor_pid_empty_or_invalid(self) -> None:
        # supervisor가 pid 파일을 쓰는 중 부분적으로만 기록되거나 손상된 상태를 "dead"로
        # 확정하면 실제로는 살아 있는 supervisor를 착각해 lease를 성급히 clear한다.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            lock_dir = base_dir / "locks"
            base_dir.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir(parents=True, exist_ok=True)

            supervisor_pid = base_dir / "supervisor.pid"
            lease = watcher_core.PaneLease(
                lock_dir,
                default_ttl=900,
                dry_run=False,
                owner_pid_path=supervisor_pid,
            )

            supervisor_pid.write_text("", encoding="utf-8")
            self.assertFalse(lease._owner_dead())

            supervisor_pid.write_text("not-a-pid\n", encoding="utf-8")
            self.assertFalse(lease._owner_dead())

            self.assertTrue(lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900))
            self.assertTrue(lease.is_active("slot_verify"))

    def test_owner_dead_returns_true_when_supervisor_pid_no_longer_exists_as_process(self) -> None:
        # 정상 동작 경로: supervisor.pid가 있고 내용이 valid pid이지만 해당 process가
        # 이미 사라진 경우에만 dead로 판정하고 lease를 clear한다.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            lock_dir = base_dir / "locks"
            base_dir.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir(parents=True, exist_ok=True)

            supervisor_pid = base_dir / "supervisor.pid"
            supervisor_pid.write_text("4242\n", encoding="utf-8")

            lease = watcher_core.PaneLease(
                lock_dir,
                default_ttl=900,
                dry_run=False,
                owner_pid_path=supervisor_pid,
            )
            self.assertTrue(lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900))

            with mock.patch("watcher_core.os.kill", side_effect=ProcessLookupError):
                self.assertTrue(lease._owner_dead())
                # is_active가 호출되면 dead owner로 감지해 stale lock을 즉시 clear해야 한다.
                self.assertFalse(lease.is_active("slot_verify"))
                self.assertFalse((lock_dir / "slot_verify.lock").exists())

    def test_owner_pid_appearing_after_watcher_start_still_detects_dead_owner(self) -> None:
        # watcher가 supervisor보다 먼저 뜨는 start-up race 시나리오: init 시점에
        # supervisor.pid가 없어도 나중에 supervisor가 떠서 pid를 쓰고, 이후 비정상 종료해
        # process가 사라지는 흐름에서 owner_dead 감지가 계속 유효해야 한다.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            lock_dir = base_dir / "locks"
            base_dir.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir(parents=True, exist_ok=True)

            supervisor_pid = base_dir / "supervisor.pid"
            self.assertFalse(supervisor_pid.exists())

            lease = watcher_core.PaneLease(
                lock_dir,
                default_ttl=900,
                dry_run=False,
                owner_pid_path=supervisor_pid,
            )
            self.assertTrue(lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900))
            self.assertTrue(lease.is_active("slot_verify"))

            supervisor_pid.write_text("4242\n", encoding="utf-8")
            with mock.patch("watcher_core.os.kill", side_effect=ProcessLookupError):
                self.assertFalse(lease.is_active("slot_verify"))
                self.assertFalse((lock_dir / "slot_verify.lock").exists())

    def test_lease_persists_owner_pid_and_clears_after_owner_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            lock_dir = base_dir / "locks"
            base_dir.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir(parents=True, exist_ok=True)

            supervisor_pid = base_dir / "supervisor.pid"
            supervisor_pid.write_text("4242\n", encoding="utf-8")

            lease = watcher_core.PaneLease(
                lock_dir,
                default_ttl=900,
                dry_run=False,
                owner_pid_path=supervisor_pid,
            )
            self.assertTrue(lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900))

            lock_data = json.loads((lock_dir / "slot_verify.lock").read_text(encoding="utf-8"))
            self.assertEqual(lock_data["owner_pid"], 4242)

            supervisor_pid.write_text("7777\n", encoding="utf-8")

            def _kill(pid: int, _sig: int) -> None:
                if pid == 4242:
                    raise ProcessLookupError
                return None

            with mock.patch("watcher_core.os.kill", side_effect=_kill):
                self.assertFalse(lease.is_active("slot_verify"))
                self.assertFalse((lock_dir / "slot_verify.lock").exists())

    def test_legacy_lease_without_owner_pid_clears_when_supervisor_restarts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            lock_dir = base_dir / "locks"
            base_dir.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir(parents=True, exist_ok=True)

            supervisor_pid = base_dir / "supervisor.pid"
            supervisor_pid.write_text("7777\n", encoding="utf-8")
            os.utime(supervisor_pid, (200.0, 200.0))

            legacy_lock = lock_dir / "slot_verify.lock"
            legacy_lock.write_text(
                json.dumps(
                    {
                        "job_id": "job-legacy",
                        "round": 1,
                        "started_at": 100.0,
                        "lease_ttl_sec": 900,
                        "pane_target": "codex-pane",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            lease = watcher_core.PaneLease(
                lock_dir,
                default_ttl=900,
                dry_run=False,
                owner_pid_path=supervisor_pid,
            )

            with mock.patch("watcher_core.os.kill", return_value=None):
                self.assertFalse(lease.is_active("slot_verify"))
                self.assertFalse(legacy_lock.exists())


class WatcherDispatchQueueControlMismatchTest(unittest.TestCase):
    def test_flush_pending_rechecks_active_control_for_each_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt_path = root / ".pipeline" / "operator_request.md"
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text("STATUS: needs_operator\n", encoding="utf-8")

            def get_path_sig(path: Path) -> str:
                if not path.exists():
                    return ""
                return path.read_text(encoding="utf-8")

            active_controls = [
                watcher_core.ControlSignal(
                    kind="operator",
                    path=prompt_path,
                    status="needs_operator",
                    mtime=10.0,
                    sig="sig-10",
                    control_seq=10,
                ),
                watcher_core.ControlSignal(
                    kind="operator",
                    path=prompt_path,
                    status="needs_operator",
                    mtime=11.0,
                    sig="sig-11",
                    control_seq=11,
                ),
            ]
            send_prompt = mock.Mock(return_value=True)
            log_raw = mock.Mock()
            append_runtime_event = mock.Mock()
            queue = watcher_core.WatcherDispatchQueue(
                lane_input_defer_cooldown_sec=0.0,
                capture_pane_text=mock.Mock(return_value="› \n tab to queue message\n55% context left\n"),
                send_keys=send_prompt,
                get_path_sig=get_path_sig,
                role_owner=lambda role: role,
                log_raw=log_raw,
                append_runtime_event=append_runtime_event,
                get_active_control_signal=mock.Mock(side_effect=active_controls),
                is_active_control=mock.Mock(return_value=True),
            )
            queue.pending_notifications = {
                "pending-10": {
                    "notify_kind": "notify_pending_10",
                    "lane_role": "verify",
                    "reason": "operator_wait_idle_retriage",
                    "prompt": "prompt 10",
                    "prompt_path": str(prompt_path),
                    "target": "codex-pane",
                    "pane_type": "codex",
                    "control_seq": 10,
                    "expected_status": "needs_operator",
                    "expected_control_path": "operator_request.md",
                    "expected_control_seq": 10,
                    "require_active_control": False,
                    "sig": "",
                },
                "pending-11": {
                    "notify_kind": "notify_pending_11",
                    "lane_role": "verify",
                    "reason": "operator_wait_idle_retriage",
                    "prompt": "prompt 11",
                    "prompt_path": str(prompt_path),
                    "target": "codex-pane",
                    "pane_type": "codex",
                    "control_seq": 11,
                    "expected_status": "needs_operator",
                    "expected_control_path": "operator_request.md",
                    "expected_control_seq": 11,
                    "require_active_control": False,
                    "sig": "",
                },
            }

            queue.flush_pending()

            self.assertEqual(send_prompt.call_count, 2)
            self.assertEqual(queue.pending_notifications, {})
            log_raw.assert_not_called()
            append_runtime_event.assert_not_called()

    def test_flush_pending_logs_structured_control_seq_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt_path = root / ".pipeline" / "operator_request.md"
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text("STATUS: needs_operator\n", encoding="utf-8")

            active_control = watcher_core.ControlSignal(
                kind="operator",
                path=prompt_path,
                status="needs_operator",
                mtime=21.0,
                sig="sig-21",
                control_seq=21,
            )
            send_prompt = mock.Mock(return_value=True)
            log_raw = mock.Mock()
            append_runtime_event = mock.Mock()
            queue = watcher_core.WatcherDispatchQueue(
                lane_input_defer_cooldown_sec=0.0,
                capture_pane_text=mock.Mock(return_value="› \n tab to queue message\n55% context left\n"),
                send_keys=send_prompt,
                get_path_sig=lambda path: path.read_text(encoding="utf-8") if path.exists() else "",
                role_owner=lambda role: role,
                log_raw=log_raw,
                append_runtime_event=append_runtime_event,
                get_active_control_signal=mock.Mock(return_value=active_control),
                is_active_control=mock.Mock(return_value=True),
            )
            queue.pending_notifications = {
                "pending-20": {
                    "notify_kind": "codex_operator_retriage",
                    "lane_role": "verify",
                    "reason": "operator_wait_idle_retriage",
                    "prompt": "prompt 20",
                    "prompt_path": str(prompt_path),
                    "target": "codex-pane",
                    "pane_type": "codex",
                    "control_seq": 20,
                    "expected_status": "needs_operator",
                    "expected_control_path": "operator_request.md",
                    "expected_control_seq": 20,
                    "require_active_control": False,
                    "sig": "",
                }
            }

            queue.flush_pending()

            send_prompt.assert_not_called()
            self.assertEqual(queue.pending_notifications, {})
            log_raw.assert_called_once()
            event, path, job_id, payload = log_raw.call_args.args
            self.assertEqual(event, "lane_input_deferred_dropped")
            self.assertEqual(path, str(prompt_path))
            self.assertEqual(job_id, "turn_signal")
            self.assertEqual(payload["notify_kind"], "codex_operator_retriage")
            self.assertEqual(payload["reason"], "control_mismatch")
            self.assertEqual(payload["reason_code"], "control_seq_drift")
            self.assertEqual(payload["expected_control_seq"], 20)
            self.assertEqual(payload["active_control_seq"], 21)
            self.assertEqual(payload["expected_prompt_path"], str(prompt_path))
            self.assertEqual(payload["active_prompt_path"], str(prompt_path))
            self.assertEqual(payload["expected_status"], "needs_operator")
            self.assertEqual(payload["active_status"], "needs_operator")
            self.assertEqual(payload["active_control"], "operator")
            append_runtime_event.assert_called_once_with("lane_input_deferred_dropped", payload)

    def test_dispatch_signal_mismatch_supervisor_working_without_wrapper_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            prompt_path = base_dir / "claude_handoff.md"
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text("STATUS: implement\nCONTROL_SEQ: 236\n", encoding="utf-8")
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "events.jsonl").write_text(
                json.dumps(
                    {
                        "seq": 236,
                        "ts": "2026-04-20T14:27:43.555105Z",
                        "run_id": "run-1",
                        "event_type": "lane_working",
                        "source": "supervisor",
                        "payload": {
                            "lane": "Claude",
                            "state": "WORKING",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            append_wrapper_event(
                wrapper_dir,
                "Claude",
                "HEARTBEAT",
                {"pid": 818464},
                source="wrapper",
                derived_from="process_alive",
            )

            active_control = watcher_core.ControlSignal(
                kind="claude_handoff",
                path=prompt_path,
                status="implement",
                mtime=236.0,
                sig="sig-236",
                control_seq=236,
            )
            send_prompt = mock.Mock(return_value=True)
            log_raw = mock.Mock()
            append_runtime_event = mock.Mock()
            queue = watcher_core.WatcherDispatchQueue(
                lane_input_defer_cooldown_sec=0.0,
                capture_pane_text=mock.Mock(return_value="› \n tab to queue message\n55% context left\n"),
                send_keys=send_prompt,
                get_path_sig=lambda path: path.read_text(encoding="utf-8") if path.exists() else "",
                role_owner=lambda role: role,
                log_raw=log_raw,
                append_runtime_event=append_runtime_event,
                get_active_control_signal=mock.Mock(return_value=active_control),
                is_active_control=mock.Mock(return_value=True),
            )
            queue.pending_notifications = {
                "claude_implement:claude_handoff:236": {
                    "notify_kind": "claude_handoff",
                    "lane_role": "implement",
                    "functional_role": "implement",
                    "lane_id": "claude_implement",
                    "agent_kind": "claude",
                    "reason": "handoff_dispatch",
                    "prompt": "prompt 236",
                    "prompt_path": str(prompt_path),
                    "target": "claude-pane",
                    "pane_type": "claude",
                    "control_seq": 236,
                    "expected_status": "implement",
                    "expected_control_path": "claude_handoff.md",
                    "expected_control_seq": 236,
                    "require_active_control": False,
                    "sig": "",
                }
            }

            queue.flush_pending()

            send_prompt.assert_not_called()
            self.assertEqual(queue.pending_notifications, {})
            log_raw.assert_called_once()
            event, path, job_id, payload = log_raw.call_args.args
            self.assertEqual(event, "lane_input_deferred_dropped")
            self.assertEqual(path, str(prompt_path))
            self.assertEqual(job_id, "turn_signal")
            self.assertEqual(payload["reason"], "control_mismatch")
            self.assertEqual(payload["reason_code"], "signal_mismatch")
            append_runtime_event.assert_called_once_with("lane_input_deferred_dropped", payload)

    def test_signal_mismatch_does_not_drop_verify_followup_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            prompt_path = base_dir / "gemini_advice.md"
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text("STATUS: advice_ready\nCONTROL_SEQ: 237\n", encoding="utf-8")
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "events.jsonl").write_text(
                json.dumps(
                    {
                        "seq": 237,
                        "ts": "2026-04-20T14:27:43.555105Z",
                        "run_id": "run-1",
                        "event_type": "lane_working",
                        "source": "supervisor",
                        "payload": {
                            "lane": "Claude",
                            "state": "WORKING",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            append_wrapper_event(
                wrapper_dir,
                "Claude",
                "HEARTBEAT",
                {"pid": 818464},
                source="wrapper",
                derived_from="process_alive",
            )

            active_control = watcher_core.ControlSignal(
                kind="gemini_advice",
                path=prompt_path,
                status="advice_ready",
                mtime=237.0,
                sig="sig-237",
                control_seq=237,
            )
            send_prompt = mock.Mock(return_value=True)
            log_raw = mock.Mock()
            append_runtime_event = mock.Mock()
            queue = watcher_core.WatcherDispatchQueue(
                lane_input_defer_cooldown_sec=0.0,
                capture_pane_text=mock.Mock(return_value="› \n tab to queue message\n55% context left\n"),
                send_keys=send_prompt,
                get_path_sig=lambda path: path.read_text(encoding="utf-8") if path.exists() else "",
                role_owner=lambda role: role,
                log_raw=log_raw,
                append_runtime_event=append_runtime_event,
                get_active_control_signal=mock.Mock(return_value=active_control),
                is_active_control=mock.Mock(return_value=True),
            )
            queue.pending_notifications = {
                "claude_verify:gemini_advice_followup:237": {
                    "notify_kind": "gemini_advice_followup",
                    "lane_role": "verify",
                    "functional_role": "verify",
                    "lane_id": "claude_verify",
                    "agent_kind": "claude",
                    "reason": "gemini_advice_updated",
                    "prompt": "prompt 237",
                    "prompt_path": str(prompt_path),
                    "target": "claude-pane",
                    "pane_type": "claude",
                    "control_seq": 237,
                    "expected_status": "advice_ready",
                    "expected_control_path": "gemini_advice.md",
                    "expected_control_seq": 237,
                    "require_active_control": False,
                    "sig": "",
                }
            }

            queue.flush_pending()

            send_prompt.assert_called_once()
            self.assertEqual(queue.pending_notifications, {})
            log_raw.assert_not_called()
            append_runtime_event.assert_not_called()


class ClaudeHandoffDispatchTest(unittest.TestCase):
    def test_verify_lease_is_reclaimed_when_supervisor_pid_is_dead(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / ".pipeline"
            lock_dir = base_dir / "locks"
            base_dir.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir(parents=True, exist_ok=True)

            supervisor_pid = base_dir / "supervisor.pid"
            supervisor_pid.write_text("4242\n", encoding="utf-8")

            lease = watcher_core.PaneLease(
                lock_dir,
                default_ttl=900,
                dry_run=False,
                owner_pid_path=supervisor_pid,
            )
            self.assertTrue(lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900))
            self.assertTrue((lock_dir / "slot_verify.lock").exists())

            with mock.patch("watcher_core.os.kill", side_effect=ProcessLookupError):
                self.assertFalse(lease.is_active("slot_verify"))
                self.assertFalse((lock_dir / "slot_verify.lock").exists())
                self.assertTrue(lease.acquire("slot_verify", "job-2", 2, "codex-pane", ttl=900))

    def test_handoff_update_waits_until_verify_lease_released(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work" / "4" / "8"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 10\n")
            core.lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900)

            with mock.patch.object(core, "_notify_claude") as notify:
                core._check_pipeline_signal_updates()
                notify.assert_not_called()
                # Handoff detected but verify active, so stays at current state
                self.assertNotEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)

                core.lease.release("slot_verify")
                core._check_pipeline_signal_updates()
                notify.assert_called_once()
                self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)

    def test_handoff_update_releases_when_supervisor_pid_is_dead(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work" / "4" / "8"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            (base_dir / "supervisor.pid").write_text("4242\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 10\n")
            core.lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900)

            with (
                mock.patch("watcher_core.os.kill", side_effect=ProcessLookupError),
                mock.patch.object(core, "_notify_claude") as notify,
            ):
                core._check_pipeline_signal_updates()
                notify.assert_called_once()
                self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)
                self.assertFalse((base_dir / "locks" / "slot_verify.lock").exists())

    def test_running_verify_job_finishes_before_older_unverified_work_is_discovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            old_work = watch_dir / "4" / "9" / "2026-04-09-stale.md"
            current_work = watch_dir / "4" / "18" / "2026-04-18-current.md"
            _write_work_note(old_work, ["docs/OLD.md"])
            _write_work_note(current_work, ["README.md"])

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core.started_at = time.time() - core.startup_grace_sec - 1.0
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IDLE, "test_setup")

            job = watcher_core.JobState.from_artifact("job-current", str(current_work))
            job.run_id = core.run_id
            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            core.lease.acquire("slot_verify", job.job_id, job.round, "codex-pane", ttl=900)

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 292\n", encoding="utf-8")
            verify_note = root / "verify" / "4" / "18" / "2026-04-18-current-verification.md"
            _write_verify_note_for_work(verify_note, "work/4/18/2026-04-18-current.md")

            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 5.0
            job.done_dispatch_id = job.dispatch_id
            job.done_at = time.time() - 1.0
            job.done_deadline_at = time.time() + 30.0
            job.save(core.state_dir)

            stale_job_id = watcher_core.make_job_id(watch_dir, old_work)

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="$ "),
                mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False),
                mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True),
            ):
                core._poll()

            current_job = watcher_core.JobState.load(core.state_dir, job.job_id)
            self.assertIsNotNone(current_job)
            assert current_job is not None
            self.assertEqual(current_job.status, watcher_core.JobStatus.VERIFY_DONE)
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)
            self.assertFalse((core.state_dir / f"{stale_job_id}.json").exists())

    def test_handoff_update_releases_from_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work" / "4" / "8"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "poll_interval": 0.1,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 10\n")
            core._transition_turn(
                watcher_core.WatcherTurnState.VERIFY_FOLLOWUP,
                "test_followup_active",
                active_control_file="gemini_advice.md",
                active_control_seq=9,
            )
            core.lease.acquire("slot_verify", "job-1", 1, "codex-pane", ttl=900)

            with mock.patch.object(core, "_notify_claude") as notify:
                core._check_pipeline_signal_updates()
                notify.assert_not_called()
                self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)

                core.lease.release("slot_verify")
                core._check_pipeline_signal_updates()
                notify.assert_called_once()
                self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)


class RuntimePlanConsumptionTest(unittest.TestCase):
    def test_prompt_contract_follows_nondefault_role_owners(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex", "Gemini"],
                    "role_bindings": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "role_options": {
                        "advisory_enabled": True,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": True,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n", encoding="utf-8")
            work_note = watch_dir / "2026-04-09-runtime-role-neutral.md"
            work_note.write_text("## 변경 파일\n- watcher_core.py\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            job = watcher_core.JobState.from_artifact("job-role-neutral", str(work_note))

            implement_prompt = core.prompt_assembler.format_implement_prompt(handoff_path)
            verify_prompt = core.sm.normalize_prompt_text(
                core.sm.verify_prompt_template.format(
                    **core.prompt_assembler.build_verify_prompt_context(job.artifact_path)
                )
            )
            advisory_prompt = core.prompt_assembler.format_runtime_prompt(core.advisory_prompt)
            followup_prompt = core.prompt_assembler.format_runtime_prompt(core.followup_prompt)

            self.assertIn("ROLE: implement", implement_prompt)
            self.assertIn("OWNER: Codex", implement_prompt)
            self.assertNotIn("claude_implement", implement_prompt)
            self.assertIn("AGENTS.md", implement_prompt)
            self.assertNotIn("OWNER: Claude", implement_prompt)
            self.assertNotIn("work/README.md", implement_prompt)
            self.assertIn("GOAL:", implement_prompt)
            self.assertIn("do only the handoff; if done, leave one `/work` closeout and stop", implement_prompt)
            self.assertIn("no commit, push, branch/PR publish, or next-slice choice", implement_prompt)
            self.assertNotIn(".pipeline/README.md", implement_prompt)

            self.assertIn("ROLE: verify", verify_prompt)
            self.assertIn("OWNER: Claude", verify_prompt)
            self.assertNotIn("codex_verify", verify_prompt)
            self.assertIn("CLAUDE.md", verify_prompt)
            self.assertIn("GOAL:", verify_prompt)
            self.assertIn("verify the latest `/work`, update `/verify`, then write exactly one next control", verify_prompt)
            self.assertIn("keep `READ_FIRST` to the listed verify-owner root doc only", verify_prompt)
            self.assertIn("after 3+ same-day same-family docs-only truth-sync rounds", verify_prompt)
            self.assertIn("do not route commit/push publish work to `.pipeline/claude_handoff.md`", verify_prompt)
            self.assertIn("keep its `READ_FIRST` to the implement-owner root doc only", verify_prompt)
            self.assertNotIn("work/README.md", verify_prompt)
            self.assertNotIn("verify/README.md", verify_prompt)
            self.assertNotIn("VERIFY: 없음", verify_prompt)
            self.assertNotIn("\n- 없음", verify_prompt)
            self.assertIn(".pipeline/claude_handoff.md [implement]", verify_prompt)
            self.assertIn("CONTROL_SEQ:", verify_prompt)
            self.assertNotIn(".pipeline/README.md", verify_prompt)
            self.assertNotIn("never route needs_operator to Claude", verify_prompt)

            self.assertIn("ROLE: advisory", advisory_prompt)
            self.assertIn("OWNER: Gemini", advisory_prompt)
            self.assertNotIn("gemini_arbitrate", advisory_prompt)
            self.assertIn("GEMINI.md", advisory_prompt)
            self.assertIn("keep `READ_FIRST` to the listed advisory-owner root doc only", advisory_prompt)
            self.assertIn("if the request cites exact shipped docs or a current runtime-doc family", advisory_prompt)
            self.assertIn("do not widen to `docs/superpowers/**`, `plandoc/**`, or historical planning docs", advisory_prompt)
            self.assertIn("GOAL:", advisory_prompt)
            self.assertIn("pane-only answer is not completion", advisory_prompt)
            self.assertNotIn("(없음)", advisory_prompt)

            self.assertIn("ROLE: followup", followup_prompt)
            self.assertIn("OWNER: Claude", followup_prompt)
            self.assertNotIn("codex_followup", followup_prompt)
            self.assertIn("CLAUDE.md", followup_prompt)
            self.assertIn("keep `READ_FIRST` to the listed verify-owner root doc only", followup_prompt)
            self.assertIn("do not route commit/push publish work to `.pipeline/claude_handoff.md`", followup_prompt)
            self.assertIn("keep its `READ_FIRST` to the implement-owner root doc only", followup_prompt)
            self.assertNotIn("verify/README.md", followup_prompt)
            self.assertIn("GOAL:", followup_prompt)
            self.assertIn("turn the advisory into exactly one next control", followup_prompt)
            self.assertNotIn("(없음)", followup_prompt)

    def test_gemini_request_dispatch_allows_advisory_without_session_arbitration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex", "Gemini"],
                    "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
                    "role_options": {
                        "advisory_enabled": True,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            gemini_request = base_dir / "gemini_request.md"
            gemini_request.write_text("STATUS: request_open\nCONTROL_SEQ: 5\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._last_gemini_request_sig = ""

            with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                with mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="Gemini CLI v0.38.0\nType your message\nworkspace\n",
                ):
                    core._check_pipeline_signal_updates()

            args, kwargs = send.call_args
            self.assertEqual(args[0], "gemini-pane")
            self.assertEqual(kwargs.get("pane_type"), "gemini")

    def test_operator_request_disabled_is_not_active_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex"],
                    "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": ""},
                    "role_options": {
                        "advisory_enabled": False,
                        "operator_stop_enabled": False,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            operator_path = base_dir / "operator_request.md"
            handoff_path = base_dir / "claude_handoff.md"
            operator_path.write_text("STATUS: needs_operator\nCONTROL_SEQ: 9\n", encoding="utf-8")
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 8\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, handoff_path)
            self.assertEqual(core._get_pending_operator_mtime(), 0.0)

    def test_gemini_request_disabled_without_advisory_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex"],
                    "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": ""},
                    "role_options": {
                        "advisory_enabled": False,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": False,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            gemini_request = base_dir / "gemini_request.md"
            handoff_path = base_dir / "claude_handoff.md"
            gemini_request.write_text("STATUS: request_open\nCONTROL_SEQ: 9\n", encoding="utf-8")
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 8\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            active = core._get_active_control_signal()
            self.assertIsNotNone(active)
            self.assertEqual(active.path, handoff_path)
            self.assertEqual(core._get_gemini_request_mtime(), 0.0)

    def test_verify_owner_updates_runtime_verify_target_and_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude"],
                    "role_bindings": {"implement": "Claude", "verify": "Claude", "advisory": ""},
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
                },
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            self.assertEqual(core.sm.verify_pane_target, "claude-pane")
            self.assertEqual(core.sm.verify_pane_type, "claude")

    def test_implement_notify_routes_to_bound_implement_owner_pane_when_claude_lane_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex", "Gemini"],
                    "role_bindings": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "role_options": {
                        "advisory_enabled": True,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": True,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                with mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="OpenAI Codex\n› Type your message\n",
                ):
                    core._notify_claude("test-runtime-implement", handoff_path)

            args, kwargs = send.call_args
            self.assertEqual(args[0], "codex-pane")
            self.assertEqual(kwargs.get("pane_type"), "codex")

    def test_implement_notify_falls_back_to_runtime_owner_when_claude_lane_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
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
                },
            )
            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send:
                with mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="OpenAI Codex\n› Type your message\n",
                ):
                    core._notify_claude("test-runtime-implement", handoff_path)

            args, kwargs = send.call_args
            self.assertEqual(args[0], "codex-pane")
            self.assertEqual(kwargs.get("pane_type"), "codex")

    def test_session_arbitration_disabled_skips_live_escalation_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
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
                },
            )
            (base_dir / "claude_handoff.md").write_text("STATUS: implement\n", encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                    "gemini_pane_target": "gemini-pane",
                }
            )
            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE, "test_setup")
            core._work_baseline_snapshot = {}

            pane_texts = {
                "codex-pane": (
                    "이 세션에서 이미 20개 이상의 슬라이스를 연속으로 구현했습니다.\n"
                    "context window가 상당히 차 있어 새 세션에서 이어가시는 것을 권장합니다.\n"
                    "진행할까요?\n>\n"
                ),
            }
            with mock.patch("watcher_core._capture_pane_text", side_effect=lambda target: pane_texts.get(target, "> ")):
                core._poll()

            self.assertFalse((base_dir / "session_arbitration_draft.md").exists())


class VerifyPromptScopeHintTest(unittest.TestCase):
    def test_docs_only_round_gets_docs_only_fast_path_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_dir = root / "work" / "4" / "9"
            work_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            work_note = work_dir / "2026-04-09-docs-only.md"
            work_note.write_text(
                "## 변경 파일\n"
                "- docs/PRODUCT_SPEC.md\n"
                "- docs/ACCEPTANCE_CRITERIA.md\n"
                "\n"
                "## 검증\n"
                "- git diff --check\n"
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            job = watcher_core.JobState.from_artifact("job-docs", str(work_note))

            context = core.prompt_assembler.build_verify_prompt_context(job.artifact_path)

            self.assertEqual(context["verify_scope_label"], "docs_only")
            self.assertIn("docs-only truth-sync", context["verify_scope_hint"])
            self.assertIn("git diff --check", context["verify_scope_hint"])

    def test_code_mixed_round_keeps_standard_verify_scope_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_dir = root / "work" / "4" / "9"
            work_dir.mkdir(parents=True, exist_ok=True)
            base_dir = root / ".pipeline"
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)
            work_note = work_dir / "2026-04-09-mixed.md"
            work_note.write_text(
                "## 변경 파일\n"
                "- app/static/app.js\n"
                "- docs/PRODUCT_SPEC.md\n"
                "\n"
                "## 검증\n"
                "- python3 -m unittest -v tests.test_web_app\n"
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(root / "work"),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            job = watcher_core.JobState.from_artifact("job-mixed", str(work_note))

            context = core.prompt_assembler.build_verify_prompt_context(job.artifact_path)

            self.assertEqual(context["verify_scope_label"], "standard")
            self.assertIn("standard verification", context["verify_scope_hint"])
            self.assertNotIn("docs-only truth-sync", context["verify_scope_hint"])


class TurnStateEnumTest(unittest.TestCase):
    def test_turn_state_values(self) -> None:
        from watcher_core import WatcherTurnState
        expected = {"IDLE", "IMPLEMENT_ACTIVE", "VERIFY_ACTIVE", "VERIFY_FOLLOWUP",
                    "ADVISORY_ACTIVE", "OPERATOR_WAIT"}
        self.assertEqual(set(e.value for e in WatcherTurnState), expected)


class TurnResolutionTest(unittest.TestCase):
    def test_codex_verify_before_claude_when_work_exists(self) -> None:
        """When work needs verify and handoff is active, Codex goes first."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            work_note = watch_dir / "4" / "10" / "2026-04-10-some-work.md"
            _write_work_note(work_note, ["controller/server.py"])

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "codex")

    def test_claude_active_when_no_pending_verify(self) -> None:
        """When no work needs verify and handoff is active, Claude goes."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "claude")

    def test_older_unverified_work_does_not_block_newer_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "4" / "10" / "2026-04-10-older-unverified-work.md"
            _write_work_note(work_note, ["controller/server.py"])
            old_mtime = time.time() - 60.0
            os.utime(work_note, (old_mtime, old_mtime))

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            dispatch_state = core._claude_handoff_dispatch_state(handoff.stat().st_mtime)

            self.assertEqual(turn, "claude")
            self.assertFalse(dispatch_state["pending_verify"])
            self.assertTrue(dispatch_state["dispatchable"])

    def test_idle_fallback_when_nothing_pending(self) -> None:
        """When no control signals and no work, state is IDLE."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "idle")

    def test_stale_operator_request_resolves_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 20",
                        "REASON_CODE: truth_sync_required",
                        "OPERATOR_POLICY: immediate_publish",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: confirm blocker closeout",
                        "BASED_ON_WORK: work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "",
                        "Stop now:",
                        "- `work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md`",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "job-1.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-1",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "artifact_hash": "hash-1",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._stale_operator_control_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(core._get_pending_operator_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_aged_operator_request_resolves_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 23",
                        "",
                        "Reason:",
                        "- still waiting",
                    ]
                ),
                encoding="utf-8",
            )
            old = time.time() - 30
            os.utime(operator_path, (old, old))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "operator_wait_retriage_sec": 5,
                }
            )

            marker = core._operator_control_recovery_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "operator_wait_idle_retriage")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_satisfied_commit_push_operator_request_routes_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _remote = _init_repo_with_commit_push(root)
            watch_dir = repo / "work"
            base_dir = repo / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_commit_push_operator_request(base_dir, seq=44)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(repo),
                    "dry_run": True,
                }
            )

            marker = core._operator_control_recovery_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], OPERATOR_APPROVAL_COMPLETED_REASON)
            self.assertEqual(marker["branch"], "main")
            self.assertEqual(marker["upstream"], "origin/main")
            self.assertEqual(core._get_pending_operator_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "codex_followup")

            core._last_operator_request_sig = ""
            with mock.patch.object(core, "_notify_codex_control_recovery") as notify:
                core._check_pipeline_signal_updates()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)
            events = [
                json.loads(line)
                for line in (base_dir / "runs" / core.run_id / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            approval_events = [
                event for event in events if event.get("event_type") == OPERATOR_APPROVAL_COMPLETED_REASON
            ]
            self.assertEqual(len(approval_events), 1)
            payload = approval_events[0]["payload"]
            self.assertEqual(payload["control_seq"], 44)
            self.assertEqual(payload["branch"], "main")
            self.assertEqual(payload["upstream"], "origin/main")
            self.assertIn("head_sha", payload)
            raw_text = (base_dir / "logs" / "experimental" / "raw.jsonl").read_text(encoding="utf-8")
            self.assertIn(OPERATOR_APPROVAL_COMPLETED_REASON, raw_text)

    def test_satisfied_commit_push_bundle_authorization_routes_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _remote = _init_repo_with_commit_push(root)
            watch_dir = repo / "work"
            base_dir = repo / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_commit_push_operator_request(
                base_dir,
                seq=49,
                reason_code=COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
                operator_policy="internal_only",
                decision_class="release_gate",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(repo),
                    "dry_run": True,
                }
            )

            marker = core._operator_control_recovery_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], OPERATOR_APPROVAL_COMPLETED_REASON)
            self.assertEqual(marker["control_seq"], 49)
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_dirty_commit_push_bundle_authorization_routes_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _remote = _init_repo_with_commit_push(root)
            watch_dir = repo / "work"
            base_dir = repo / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            (repo / "dirty-source.txt").write_text("dirty\n", encoding="utf-8")
            _write_commit_push_operator_request(
                base_dir,
                seq=50,
                reason_code=COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON,
                operator_policy="internal_only",
                decision_class="release_gate",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(repo),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_control_recovery_marker())
            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON)
            self.assertEqual(marker["mode"], "triage")
            self.assertEqual(marker["routed_to"], "codex_followup")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_commit_push_operator_request_without_upstream_stays_operator_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _remote = _init_repo_with_commit_push(root, push=False)
            watch_dir = repo / "work"
            base_dir = repo / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            _write_commit_push_operator_request(base_dir, seq=45)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(repo),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_control_recovery_marker())
            self.assertGreater(core._get_pending_operator_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "operator")

    def test_commit_push_operator_request_upstream_behind_stays_operator_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _remote = _init_repo_with_commit_push(root)
            watch_dir = repo / "work"
            base_dir = repo / ".pipeline"
            (repo / "README.md").write_text("local ahead\n", encoding="utf-8")
            _run_git(repo, ["add", "README.md"])
            _run_git(
                repo,
                [
                    "-c",
                    "user.email=test@example.com",
                    "-c",
                    "user.name=Test User",
                    "commit",
                    "-m",
                    "local ahead",
                ],
            )
            watch_dir.mkdir(parents=True, exist_ok=True)
            _write_commit_push_operator_request(base_dir, seq=46)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(repo),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_control_recovery_marker())
            self.assertGreater(core._get_pending_operator_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "operator")

    def test_commit_push_operator_request_dirty_source_stays_operator_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _remote = _init_repo_with_commit_push(root)
            watch_dir = repo / "work"
            base_dir = repo / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            (repo / "untracked-source.txt").write_text("dirty\n", encoding="utf-8")
            _write_commit_push_operator_request(base_dir, seq=47)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(repo),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_control_recovery_marker())
            self.assertGreater(core._get_pending_operator_mtime(), 0.0)
            self.assertEqual(core._resolve_turn(), "operator")

    def test_commit_push_operator_request_allows_rolling_pipeline_dirty_slots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, _remote = _init_repo_with_commit_push(root)
            watch_dir = repo / "work"
            base_dir = repo / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            _write_commit_push_operator_request(base_dir, seq=48)
            for filename, status in {
                "claude_handoff.md": "STATUS: implement\nCONTROL_SEQ: 1\n",
                "gemini_request.md": "STATUS: request_open\nCONTROL_SEQ: 2\n",
                "gemini_advice.md": "STATUS: advice_ready\nCONTROL_SEQ: 3\n",
            }.items():
                (base_dir / filename).write_text(status, encoding="utf-8")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(repo),
                    "dry_run": True,
                }
            )

            marker = core._operator_control_recovery_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], OPERATOR_APPROVAL_COMPLETED_REASON)

    def test_fresh_slice_ambiguity_operator_request_routes_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 26\n"
                "REASON_CODE: slice_ambiguity\n"
                "OPERATOR_POLICY: gate_24h\n"
                "DECISION_CLASS: operator_only\n"
                "DECISION_REQUIRED: choose exact next slice\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "slice_ambiguity")
            self.assertEqual(marker["operator_policy"], "gate_24h")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_next_slice_alias_operator_request_stays_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 26\n"
                "REASON_CODE: gemini_axis_switch_without_exact_slice\n"
                "OPERATOR_POLICY: stop_until_exact_slice_selected\n"
                "DECISION_CLASS: next_slice_selection\n"
                "DECISION_REQUIRED: choose exact next slice\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "slice_ambiguity")
            self.assertEqual(marker["reason_code"], "slice_ambiguity")
            self.assertEqual(marker["operator_policy"], "gate_24h")
            self.assertEqual(marker["classification_source"], "operator_policy")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_choice_menu_operator_request_routes_to_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 27",
                        "REASON_CODE: branch_commit_and_milestone_transition",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: choose A/B/C from docs and verify notes",
                        "",
                        "Operator decision A: continue runtime follow-up.",
                        "Operator decision B: open advisory arbitration.",
                        "Operator decision C: pause for evidence validation.",
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "slice_ambiguity")
            self.assertEqual(marker["decision_class"], "next_slice_selection")
            self.assertEqual(marker["operator_policy"], "gate_24h")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_numbered_choice_menu_operator_request_routes_to_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 28",
                        "REASON_CODE: branch_commit_and_milestone_transition",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: 선택지 1/2/3 중 docs and verify notes로 고르기",
                        "",
                        "1안: continue runtime follow-up.",
                        "2안: open advisory arbitration.",
                        "3안: pause for evidence validation.",
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "slice_ambiguity")
            self.assertEqual(marker["decision_class"], "next_slice_selection")
            self.assertEqual(marker["operator_policy"], "gate_24h")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_parenthesized_inline_choice_operator_request_routes_to_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 29",
                        "REASON_CODE: approval_required",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: operator_only",
                        (
                            "DECISION_REQUIRED: (B) runtime live validation; "
                            "(C) evidence follow-up; "
                            "(D) docs reconciliation"
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "slice_ambiguity")
            self.assertEqual(marker["decision_class"], "next_slice_selection")
            self.assertEqual(marker["operator_policy"], "gate_24h")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_real_approval_required_gate_stays_operator_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 30",
                        "REASON_CODE: approval_required",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: approve dirty worktree commit and remote push",
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_gate_marker())
            self.assertEqual(core._resolve_turn(), "operator")

    def test_real_operator_boundary_supersedes_lower_seq_advisory_slots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            gemini_request_path = base_dir / "gemini_request.md"
            gemini_request_path.write_text(
                "\n".join(
                    [
                        "STATUS: request_open",
                        "CONTROL_SEQ: 28",
                        "REQUEST: stale advisory request",
                    ]
                ),
                encoding="utf-8",
            )
            gemini_advice_path = base_dir / "gemini_advice.md"
            gemini_advice_path.write_text(
                "\n".join(
                    [
                        "STATUS: advice_ready",
                        "CONTROL_SEQ: 29",
                        "RECOMMEND: needs_operator (C) approve commit and push",
                    ]
                ),
                encoding="utf-8",
            )
            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 30",
                        "REASON_CODE: approval_required",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: approve dirty worktree commit and remote push",
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )
            core._last_operator_request_sig = ""

            core._check_pipeline_signal_updates()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.OPERATOR_WAIT)
            self.assertEqual(core._get_pending_gemini_request_mtime(), 0.0)
            self.assertEqual(core._get_pending_gemini_advice_mtime(), 0.0)
            self.assertEqual(core._last_gemini_request_sig, core._get_path_sig(gemini_request_path))
            self.assertEqual(core._last_gemini_advice_sig, core._get_path_sig(gemini_advice_path))
            self.assertIn("STATUS: superseded", gemini_request_path.read_text(encoding="utf-8"))
            self.assertIn("STATUS: superseded", gemini_advice_path.read_text(encoding="utf-8"))
            self.assertIn("SUPERSEDED_BY_SEQ: 30", gemini_request_path.read_text(encoding="utf-8"))
            self.assertIn("SUPERSEDED_BY_SEQ: 30", gemini_advice_path.read_text(encoding="utf-8"))

    def test_choice_menu_operator_request_ignores_explanatory_body_blocker_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 30",
                        "REASON_CODE: slice_ambiguity",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: next_slice_selection",
                        (
                            "DECISION_REQUIRED: (B) runtime live validation; "
                            "(C) evidence follow-up; "
                            "(D) docs reconciliation"
                        ),
                        "",
                        "---",
                        "",
                        "- approval_record/safety/destructive/auth/credential marker docs are explanatory.",
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "slice_ambiguity")
            self.assertEqual(marker["decision_class"], "next_slice_selection")
            self.assertEqual(marker["operator_policy"], "gate_24h")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_slice_ambiguity_operator_request_with_verified_work_stays_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 26",
                        "REASON_CODE: slice_ambiguity",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: next_slice_selection",
                        "DECISION_REQUIRED: choose exact next slice",
                        "BASED_ON_WORK: work/4/19/2026-04-19-legacy-active-context-summary-hint-basis-backfill.md",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "job-26.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-26",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/19/2026-04-19-legacy-active-context-summary-hint-basis-backfill.md",
                        "artifact_hash": "hash-26",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_control_recovery_marker())
            gate = core._operator_gate_marker()
            self.assertIsNotNone(gate)
            self.assertEqual(gate["reason"], "slice_ambiguity")

            core._last_operator_request_sig = ""
            with (
                mock.patch.object(core, "_notify_codex_control_recovery") as recovery_notify,
                mock.patch.object(core, "_notify_codex_operator_retriage") as retriage_notify,
            ):
                core._check_pipeline_signal_updates()

            recovery_notify.assert_not_called()
            retriage_notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)

    def test_truth_sync_operator_request_stays_operator_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 27\n"
                "REASON_CODE: truth_sync_required\n"
                "OPERATOR_POLICY: immediate_publish\n"
                "DECISION_CLASS: operator_only\n"
                "DECISION_REQUIRED: confirm truth sync\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_gate_marker())
            self.assertEqual(core._resolve_turn(), "operator")

    def test_fresh_idle_operator_request_hibernates_instead_of_operator_wait(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 28\n"
                "REASON_CODE: idle_hibernate\n"
                "OPERATOR_POLICY: internal_only\n"
                "DECISION_CLASS: internal_only\n"
                "DECISION_REQUIRED: wait for next control\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["mode"], "hibernate")
            self.assertEqual(core._resolve_turn(), "idle")

    def test_waiting_next_control_next_slice_selection_routes_to_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 29\n"
                "REASON_CODE: waiting_next_control\n"
                "OPERATOR_POLICY: internal_only\n"
                "DECISION_CLASS: next_slice_selection\n"
                "DECISION_REQUIRED: choose exact next slice\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["reason"], "waiting_next_control")
            self.assertEqual(marker["operator_policy"], "internal_only")
            self.assertEqual(marker["mode"], "triage")
            self.assertEqual(marker["routed_to"], "codex_followup")
            self.assertEqual(core._resolve_turn(), "codex_followup")

    def test_operator_request_missing_structured_headers_stays_fail_safe_operator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 29\n\nReason:\n- slice_ambiguity\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertIsNone(core._operator_gate_marker())
            self.assertEqual(core._resolve_turn(), "operator")

    def test_codex_verify_before_claude_even_for_metadata_only_note(self) -> None:
        """Metadata-only work note still triggers Codex verify before Claude."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            meta_note = watch_dir / "4" / "10" / "2026-04-10-meta-only.md"
            _write_work_note(meta_note, ["work/4/10/2026-04-10-meta-only.md"])

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            turn = core._resolve_turn()
            self.assertEqual(turn, "codex")

    def test_unverified_latest_work_beats_stale_operator_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 20",
                        "REASON_CODE: newer_unverified_work_present",
                        "OPERATOR_POLICY: stop_until_truth_sync",
                        "DECISION_CLASS: truth_sync_scope",
                        "DECISION_REQUIRED: verify newer work first",
                        "BASED_ON_WORK: work/4/10/2026-04-10-older.md",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "job-1.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-1",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/10/2026-04-10-older.md",
                        "artifact_hash": "hash-1",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            older_work = watch_dir / "4" / "10" / "2026-04-10-older.md"
            latest_work = watch_dir / "4" / "10" / "2026-04-10-latest-meta.md"
            verify_note = verify_dir / "4" / "10" / "2026-04-10-older-verification.md"
            _write_work_note(older_work, ["docs/PRODUCT_PROPOSAL.md"])
            _write_work_note(latest_work, ["work/4/10/2026-04-10-latest-meta.md"])
            _write_verify_note_for_work(
                verify_note,
                "work/4/10/2026-04-10-older.md",
            )
            now = time.time()
            os.utime(older_work, (now - 30, now - 30))
            os.utime(latest_work, (now - 20, now - 20))
            os.utime(verify_note, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            self.assertEqual(core._resolve_turn(), "codex")

    def test_newer_unverified_work_operator_request_routes_to_codex_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            older_work = watch_dir / "4" / "10" / "2026-04-10-older.md"
            latest_work = watch_dir / "4" / "10" / "2026-04-10-latest-meta.md"
            verify_note = verify_dir / "4" / "10" / "2026-04-10-older-verification.md"
            _write_work_note(older_work, ["docs/PRODUCT_PROPOSAL.md"])
            _write_work_note(latest_work, ["work/4/10/2026-04-10-latest-meta.md"])
            _write_verify_note_for_work(
                verify_note,
                "work/4/10/2026-04-10-older.md",
            )
            now = time.time()
            os.utime(older_work, (now - 30, now - 30))
            os.utime(latest_work, (now - 20, now - 20))
            os.utime(verify_note, (now - 10, now - 10))

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 21",
                        "REASON_CODE: newer_unverified_work_present",
                        "OPERATOR_POLICY: stop_until_truth_sync",
                        "DECISION_CLASS: truth_sync_scope",
                        "DECISION_REQUIRED: verify latest work first",
                        "BASED_ON_WORK: work/4/10/2026-04-10-latest-meta.md",
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                }
            )

            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            self.assertEqual(marker["operator_policy"], "gate_24h")
            self.assertEqual(marker["reason_code"], "newer_unverified_work_present")
            self.assertEqual(core._resolve_turn(), "codex")


class ControlSeqAgeTrackerTest(unittest.TestCase):
    def _make_core(self, root: Path) -> watcher_core.WatcherCore:
        watch_dir = root / "work"
        base_dir = root / ".pipeline"
        watch_dir.mkdir(parents=True, exist_ok=True)
        base_dir.mkdir(parents=True, exist_ok=True)
        _write_active_profile(root)
        return watcher_core.WatcherCore(
            {
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            }
        )

    def test_same_control_seq_increments_age_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = self._make_core(root)
            (root / ".pipeline" / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 31\n",
                encoding="utf-8",
            )

            observed = [core._refresh_control_seq_age() for _ in range(4)]

            self.assertEqual(observed, [0, 1, 2, 3])
            self.assertEqual(core._last_seen_control_seq, 31)
            self.assertEqual(core._control_seq_age_cycles, 3)

    def test_different_control_seq_resets_age_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = self._make_core(root)
            handoff = root / ".pipeline" / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 41\n", encoding="utf-8")
            self.assertEqual(core._refresh_control_seq_age(), 0)
            self.assertEqual(core._refresh_control_seq_age(), 1)

            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 42\n", encoding="utf-8")

            self.assertEqual(core._refresh_control_seq_age(), 0)
            self.assertEqual(core._last_seen_control_seq, 42)
            self.assertEqual(core._control_seq_age_cycles, 0)

    def test_missing_or_unreadable_control_slot_returns_zero_age(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = self._make_core(root)

            self.assertEqual(core._refresh_control_seq_age(), 0)
            self.assertIsNone(core._last_seen_control_seq)
            with mock.patch.object(core, "_highest_control_seq_for_age", side_effect=OSError("unreadable")):
                self.assertEqual(core._refresh_control_seq_age(), 0)
            self.assertFalse(core._control_seq_age_cycles)

    def test_stale_control_advisory_writes_after_grace_period(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = self._make_core(root)
            base_dir = root / ".pipeline"
            handoff_path = base_dir / "claude_handoff.md"
            handoff_text = "STATUS: implement\nCONTROL_SEQ: 31\n"
            handoff_path.write_text(handoff_text, encoding="utf-8")

            core._last_seen_control_seq = 31
            core._control_seq_age_cycles = (
                STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES
            )

            with mock.patch.object(core, "_notify_gemini") as notify:
                wrote = core._maybe_write_stale_control_advisory_request()

            self.assertTrue(wrote)
            notify.assert_called_once_with("stale_control_advisory")
            self.assertEqual(handoff_path.read_text(encoding="utf-8"), handoff_text)
            self.assertFalse((base_dir / "operator_request.md").exists())
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.ADVISORY_ACTIVE)
            self.assertEqual(core._turn_active_control_seq, 32)
            request_text = (base_dir / "gemini_request.md").read_text(encoding="utf-8")
            self.assertIn("STATUS: request_open", request_text)
            self.assertIn("CONTROL_SEQ: 32", request_text)
            self.assertIn("REASON_CODE: stale_control_advisory", request_text)
            self.assertIn("SUPERSEDES: .pipeline/claude_handoff.md CONTROL_SEQ 31", request_text)
            raw_text = (base_dir / "logs" / "experimental" / "raw.jsonl").read_text(encoding="utf-8")
            self.assertIn("stale_control_advisory_written", raw_text)

    def test_stale_control_advisory_waits_for_grace_period(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = self._make_core(root)
            base_dir = root / ".pipeline"
            (base_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 31\n",
                encoding="utf-8",
            )

            core._last_seen_control_seq = 31
            core._control_seq_age_cycles = (
                STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES - 1
            )

            with mock.patch.object(core, "_notify_gemini") as notify:
                wrote = core._maybe_write_stale_control_advisory_request()

            self.assertFalse(wrote)
            notify.assert_not_called()
            self.assertFalse((base_dir / "gemini_request.md").exists())

    def test_stale_control_advisory_skips_when_operator_request_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = self._make_core(root)
            base_dir = root / ".pipeline"
            operator_path = base_dir / "operator_request.md"
            operator_text = (
                "STATUS: needs_operator\n"
                "CONTROL_SEQ: 55\n"
                "REASON_CODE: approval_required\n"
            )
            operator_path.write_text(operator_text, encoding="utf-8")

            core._last_seen_control_seq = 55
            core._control_seq_age_cycles = (
                STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES
            )

            with mock.patch.object(core, "_notify_gemini") as notify:
                wrote = core._maybe_write_stale_control_advisory_request()

            self.assertFalse(wrote)
            notify.assert_not_called()
            self.assertFalse((base_dir / "gemini_request.md").exists())
            self.assertEqual(operator_path.read_text(encoding="utf-8"), operator_text)

    def test_stale_control_advisory_preserves_current_existing_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = self._make_core(root)
            base_dir = root / ".pipeline"
            (base_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 31\n",
                encoding="utf-8",
            )
            request_path = base_dir / "gemini_request.md"
            request_text = (
                "STATUS: request_open\n"
                "CONTROL_SEQ: 40\n"
                "REASON_CODE: stale_control_advisory\n"
            )
            request_path.write_text(request_text, encoding="utf-8")

            core._last_seen_control_seq = 31
            core._control_seq_age_cycles = (
                STALE_CONTROL_CYCLE_THRESHOLD + STALE_ADVISORY_GRACE_CYCLES
            )

            with mock.patch.object(core, "_notify_gemini") as notify:
                wrote = core._maybe_write_stale_control_advisory_request()

            self.assertFalse(wrote)
            notify.assert_not_called()
            self.assertEqual(request_path.read_text(encoding="utf-8"), request_text)


class RollingSignalTransitionTest(unittest.TestCase):
    def test_stale_control_seq_does_not_trigger_transition(self) -> None:
        """A signal with lower control_seq than current should not cause transition."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            # Set current state with seq 17
            core._transition_turn(
                watcher_core.WatcherTurnState.CODEX_VERIFY,
                "test_setup",
                active_control_seq=17,
            )

            # A handoff with lower seq should not override
            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 15\n", encoding="utf-8")
            # Reset sig tracking so change is detected
            core._last_claude_handoff_sig = ""
            core._check_pipeline_signal_updates()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.CODEX_VERIFY)

    def test_higher_seq_handoff_transitions_to_claude(self) -> None:
        """A handoff with higher seq should trigger Claude transition."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IDLE,
                "test_setup",
                active_control_seq=15,
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 18\n", encoding="utf-8")
            core._last_claude_handoff_sig = ""

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                core._check_pipeline_signal_updates()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)

    def test_stale_operator_request_update_routes_to_codex_control_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 21",
                        "REASON_CODE: truth_sync_required",
                        "OPERATOR_POLICY: immediate_publish",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: confirm blocker closeout",
                        "BASED_ON_WORK: work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "",
                        "Stop now:",
                        "- `work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md`",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "job-2.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-2",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "artifact_hash": "hash-2",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })
            core._last_operator_request_sig = ""

            with mock.patch.object(core, "_notify_codex_control_recovery") as notify:
                core._check_pipeline_signal_updates()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)

    def test_startup_turn_uses_codex_control_recovery_for_stale_operator_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            state_dir = base_dir / "state"
            watch_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 22",
                        "REASON_CODE: truth_sync_required",
                        "OPERATOR_POLICY: immediate_publish",
                        "DECISION_CLASS: operator_only",
                        "DECISION_REQUIRED: confirm blocker closeout",
                        "BASED_ON_WORK: work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "",
                        "Stop now:",
                        "- `work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md`",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "job-3.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-3",
                        "status": "VERIFY_DONE",
                        "artifact_path": "work/4/10/2026-04-10-review-queue-source-message-review-outcome-visibility.md",
                        "artifact_hash": "hash-3",
                        "round": 1,
                    }
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })
            core.started_at = time.time() - core.startup_grace_sec - 1.0

            with mock.patch.object(core, "_notify_codex_control_recovery") as notify:
                core._poll()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)

    def test_startup_turn_uses_codex_operator_retriage_for_aged_operator_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 25\n\nReason:\n- still pending\n",
                encoding="utf-8",
            )
            old = time.time() - 30
            os.utime(operator_path, (old, old))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "operator_wait_retriage_sec": 5,
                }
            )
            core.started_at = time.time() - core.startup_grace_sec - 1.0

            with mock.patch.object(core, "_notify_codex_operator_retriage") as notify:
                core._poll()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)

    def test_operator_wait_idle_timeout_routes_to_codex_operator_retriage_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 24\n\nReason:\n- still pending\n",
                encoding="utf-8",
            )
            old = time.time() - 30
            os.utime(operator_path, (old, old))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "operator_wait_retriage_sec": 5,
                }
            )
            core._transition_turn(
                watcher_core.WatcherTurnState.OPERATOR_WAIT,
                "test_setup_operator_wait",
                active_control_file="operator_request.md",
                active_control_seq=24,
            )

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="$ "),
                mock.patch("watcher_core._pane_text_is_idle", return_value=True),
                mock.patch.object(core, "_notify_codex_operator_retriage") as notify,
            ):
                core._check_operator_wait_idle_timeout()
                core._check_operator_wait_idle_timeout()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)
            self.assertEqual(core._turn_active_control_seq, 24)

    def test_operator_retriage_no_next_control_promotes_to_gemini_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            operator_path.write_text(
                "\n".join(
                    [
                        "STATUS: needs_operator",
                        "CONTROL_SEQ: 31",
                        "REASON_CODE: slice_ambiguity",
                        "OPERATOR_POLICY: gate_24h",
                        "DECISION_CLASS: next_slice_selection",
                        (
                            "DECISION_REQUIRED: (B) runtime live validation; "
                            "(C) docs reconciliation; "
                            "(D) focused verification"
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "operator_retriage_no_control_sec": 0,
                }
            )
            core._last_operator_retriage_sig = core._get_path_sig(operator_path)
            core._transition_turn(
                watcher_core.WatcherTurnState.VERIFY_FOLLOWUP,
                "test_setup_operator_retriage",
                active_control_file="operator_request.md",
                active_control_seq=31,
            )

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="openai codex\n› "),
                mock.patch.object(core, "_notify_gemini") as notify,
            ):
                promoted = core._promote_operator_retriage_no_next_control()

            self.assertTrue(promoted)
            notify.assert_called_once_with("operator_retriage_no_next_control")
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.ADVISORY_ACTIVE)
            self.assertEqual(core._turn_active_control_seq, 32)
            request_text = (base_dir / "gemini_request.md").read_text(encoding="utf-8")
            self.assertIn("STATUS: request_open", request_text)
            self.assertIn("CONTROL_SEQ: 32", request_text)
            self.assertIn("SOURCE: watcher operator_retriage_no_next_control", request_text)
            self.assertIn("SUPERSEDES: .pipeline/operator_request.md CONTROL_SEQ 31", request_text)
            raw_text = (base_dir / "logs" / "experimental" / "raw.jsonl").read_text(encoding="utf-8")
            self.assertIn("operator_retriage_no_next_control", raw_text)

    def test_operator_retriage_seq_only_bump_preserves_no_next_control_age(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_path = base_dir / "operator_request.md"
            base_now = time.time()

            def write_operator_request(seq: int, mtime: float) -> None:
                operator_path.write_text(
                    "\n".join(
                        [
                            "STATUS: needs_operator",
                            f"CONTROL_SEQ: {seq}",
                            "REASON_CODE: slice_ambiguity",
                            "OPERATOR_POLICY: gate_24h",
                            "DECISION_CLASS: next_slice_selection",
                            (
                                "DECISION_REQUIRED: (B) runtime live validation; "
                                "(C) docs reconciliation"
                            ),
                        ]
                    ),
                    encoding="utf-8",
                )
                os.utime(operator_path, (mtime, mtime))

            write_operator_request(31, base_now)
            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "operator_retriage_no_control_sec": 45,
                }
            )
            marker = core._operator_gate_marker()
            self.assertIsNotNone(marker)
            core._last_operator_retriage_sig = core._get_path_sig(operator_path)
            core._last_operator_retriage_fingerprint = str((marker or {}).get("fingerprint") or "")
            core._operator_retriage_started_at = base_now
            core._transition_turn(
                watcher_core.WatcherTurnState.VERIFY_FOLLOWUP,
                "test_setup_operator_retriage",
                active_control_file="operator_request.md",
                active_control_seq=31,
            )
            core._turn_entered_at = base_now

            write_operator_request(32, base_now + 30)
            with (
                mock.patch("watcher_core.time.time", return_value=base_now + 35),
                mock.patch.object(core, "_notify_codex_operator_retriage") as retriage_notify,
            ):
                core._check_pipeline_signal_updates()

            retriage_notify.assert_not_called()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)
            self.assertEqual(core._operator_retriage_started_at, base_now)
            self.assertEqual(core._last_operator_retriage_sig, core._get_path_sig(operator_path))

            with mock.patch("watcher_core.time.time", return_value=base_now + 44):
                self.assertIsNone(core._operator_retriage_no_next_control_marker())

            with (
                mock.patch("watcher_core.time.time", return_value=base_now + 46),
                mock.patch("watcher_core._capture_pane_text", return_value="openai codex\n› "),
                mock.patch.object(core, "_notify_gemini") as notify,
            ):
                promoted = core._promote_operator_retriage_no_next_control()

            self.assertTrue(promoted)
            notify.assert_called_once_with("operator_retriage_no_next_control")
            request_text = (base_dir / "gemini_request.md").read_text(encoding="utf-8")
            self.assertIn("CONTROL_SEQ: 33", request_text)
            self.assertIn("SUPERSEDES: .pipeline/operator_request.md CONTROL_SEQ 32", request_text)

    def test_higher_seq_handoff_is_deferred_while_claude_round_is_active(self) -> None:
        """An updated handoff should not hot-swap into an already active Claude round."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
                "test_setup",
                active_control_seq=17,
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 18\n", encoding="utf-8")
            core._last_claude_handoff_sig = ""

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="running tests...\n"),
                mock.patch("watcher_core._pane_text_is_idle", return_value=False),
                mock.patch.object(core, "_notify_claude") as notify,
            ):
                core._check_pipeline_signal_updates()

            notify.assert_not_called()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)
            self.assertIsNotNone(core._pending_idle_release_handoff)

    # origin: implement handoff idle-release deferred-candidate replay (출처 work note 미기록)
    def test_deferred_handoff_releases_after_implement_lane_becomes_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_pane_target": "claude-pane",
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
                "test_setup",
                active_control_seq=17,
            )
            core._work_baseline_snapshot = core._get_work_tree_snapshot_broad()

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 18\n", encoding="utf-8")
            core._last_claude_handoff_sig = ""

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="running tests...\n"),
                mock.patch("watcher_core._pane_text_is_idle", return_value=False),
                mock.patch.object(core, "_notify_claude") as notify,
            ):
                core._check_pipeline_signal_updates()
                notify.assert_not_called()

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="$ "),
                mock.patch("watcher_core._pane_text_is_idle", return_value=True),
                mock.patch.object(core, "_notify_claude") as notify,
            ):
                self.assertTrue(core._check_pending_idle_release_handoff())

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)
            self.assertEqual(core._turn_active_control_seq, 18)
            self.assertIsNone(core._pending_idle_release_handoff)

    def test_higher_seq_handoff_releases_when_implement_lane_is_idle(self) -> None:
        """A newer handoff should recover when the previous active implement pane is idle."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_pane_target": "claude-pane",
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
                "test_setup",
                active_control_seq=17,
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 18\n", encoding="utf-8")
            core._last_claude_handoff_sig = ""

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="$ "),
                mock.patch("watcher_core._pane_text_is_idle", return_value=True),
                mock.patch.object(core, "_notify_claude") as notify,
            ):
                core._check_pipeline_signal_updates()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)
            self.assertEqual(core._turn_active_control_seq, 18)

    def test_deferred_handoff_flushes_after_active_claude_round_exits(self) -> None:
        """A deferred handoff should dispatch once the active Claude round exits."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
                "test_setup",
                active_control_seq=17,
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 18\n", encoding="utf-8")
            core._last_claude_handoff_sig = ""

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="running tests...\n"),
                mock.patch("watcher_core._pane_text_is_idle", return_value=False),
                mock.patch.object(core, "_notify_claude") as notify,
            ):
                core._check_pipeline_signal_updates()
                notify.assert_not_called()

                core._transition_turn(
                    watcher_core.WatcherTurnState.IDLE,
                    "test_round_exit",
                    active_control_seq=17,
                )
                core._check_pipeline_signal_updates()

            notify.assert_called_once()
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)


class ClaudeIdleTimeoutTest(unittest.TestCase):
    def test_claude_idle_timeout_transitions_to_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
                "test_setup",
            )
            import hashlib as _hlib
            idle_fingerprint = _hlib.md5(b"$ ").hexdigest()
            core._last_active_pane_fingerprint = idle_fingerprint
            core._last_progress_at = time.time() - 10
            core._work_baseline_snapshot = {}

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "):
                with mock.patch("watcher_core._pane_text_is_idle", return_value=True):
                    core._check_claude_idle_timeout()

            self.assertEqual(
                core._current_turn_state,
                watcher_core.WatcherTurnState.IDLE,
            )

    def test_claude_progress_resets_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
                "test_setup",
            )
            core._last_progress_at = time.time() - 10
            core._last_active_pane_fingerprint = "old_fingerprint"

            with mock.patch("watcher_core._capture_pane_text", return_value="running tests..."):
                with mock.patch("watcher_core._pane_text_is_idle", return_value=False):
                    core._check_claude_idle_timeout()

            self.assertEqual(
                core._current_turn_state,
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
            )
            self.assertGreater(core._last_progress_at, time.time() - 2)

    def test_idle_release_cooldown_prevents_redispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_active_idle_timeout_sec": 5,
            })

            handoff_sig = core._get_path_sig(handoff)
            core._last_idle_release_handoff_sig = handoff_sig
            core._last_idle_release_at = time.time()

            self.assertTrue(core._is_idle_release_cooldown_active())


class TransitionTurnTest(unittest.TestCase):
    def test_write_current_run_pointer_records_watcher_pid_and_fingerprint(self) -> None:
        from pipeline_runtime import schema as schema_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            # Drive the shared fingerprint helper through a stable non-empty
            # value via the same stub seam the empty-path regression uses, so
            # this positive pointer-writer assertion no longer depends on the
            # host actually exposing /proc/<pid>/stat. Watcher_pid stays live
            # because os.getpid() is independent of the helper.
            non_empty_fingerprint = "Mon Apr 18 12:34:56 2026"
            with (
                mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
                mock.patch.object(
                    schema_module,
                    "_ps_lstart_fingerprint",
                    return_value=non_empty_fingerprint,
                ),
            ):
                core._write_current_run_pointer()

            current_run_path = base_dir / "current_run.json"
            self.assertTrue(current_run_path.exists())
            data = json.loads(current_run_path.read_text())
            self.assertEqual(data["run_id"], core.run_id)
            self.assertEqual(data["watcher_pid"], os.getpid())
            self.assertEqual(data.get("watcher_fingerprint", ""), non_empty_fingerprint)

    def test_write_current_run_pointer_records_empty_fingerprint_when_both_sources_fail(self) -> None:
        from pipeline_runtime import schema as schema_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            # On a minimal host where /proc/<pid>/stat, `ps -p <pid> -o
            # lstart=`, and os.stat(f"/proc/{pid}") all fail the shared
            # fingerprint helper falls all the way through to "". The watcher
            # exporter must still write the watcher_fingerprint field
            # explicitly as "" rather than silently dropping it, so supervisor
            # inheritance can recognise the safe-degradation path instead of
            # treating the pointer as a legacy/no-owner record.
            with (
                mock.patch.object(schema_module, "_proc_starttime_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_ps_lstart_fingerprint", return_value=""),
                mock.patch.object(schema_module, "_proc_ctime_fingerprint", return_value=""),
            ):
                core._write_current_run_pointer()

            current_run_path = base_dir / "current_run.json"
            self.assertTrue(current_run_path.exists())
            data = json.loads(current_run_path.read_text())
            self.assertEqual(data["run_id"], core.run_id)
            self.assertEqual(data["watcher_pid"], os.getpid())
            self.assertIn("watcher_fingerprint", data)
            self.assertEqual(data["watcher_fingerprint"], "")

    def test_transition_writes_turn_state_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.CODEX_VERIFY,
                "work_needs_verify",
                active_control_file="claude_handoff.md",
                active_control_seq=17,
                verify_job_id="test-job-1",
            )

            state_path = base_dir / "state" / "turn_state.json"
            self.assertTrue(state_path.exists())
            data = json.loads(state_path.read_text())
            self.assertEqual(data["state"], "VERIFY_ACTIVE")
            self.assertEqual(data["legacy_state"], "CODEX_VERIFY")
            self.assertEqual(data["reason"], "work_needs_verify")
            self.assertEqual(data["active_control_file"], "claude_handoff.md")
            self.assertEqual(data["active_control_seq"], 17)
            self.assertEqual(data["active_role"], "verify")
            self.assertEqual(data["active_lane"], "Codex")
            self.assertEqual(data["verify_job_id"], "test-job-1")
            self.assertIn("entered_at", data)

            current_run_path = base_dir / "current_run.json"
            self.assertTrue(current_run_path.exists())
            current_run = json.loads(current_run_path.read_text())
            self.assertEqual(current_run["run_id"], core.run_id)

            status_path = base_dir / "runs" / core.run_id / "status.json"
            self.assertTrue(status_path.exists())
            status = json.loads(status_path.read_text())
            self.assertEqual(status["run_id"], core.run_id)
            self.assertEqual(status["runtime_state"], "RUNNING")
            self.assertEqual(status["turn_state"], "VERIFY_ACTIVE")
            self.assertEqual(status["legacy_turn_state"], "CODEX_VERIFY")
            self.assertEqual(status["control"]["active_control_file"], ".pipeline/claude_handoff.md")
            self.assertEqual(status["control"]["active_control_seq"], 17)

            events_path = base_dir / "runs" / core.run_id / "events.jsonl"
            self.assertTrue(events_path.exists())
            events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
            self.assertGreaterEqual(len(events), 2)
            self.assertEqual(events[0]["event_type"], "runtime_started")
            self.assertEqual(events[-1]["event_type"], "control_changed")
            self.assertEqual(events[-1]["payload"]["active_role"], "verify")
            self.assertEqual(events[-1]["payload"]["active_lane"], "Codex")

    def test_transition_writes_role_bound_turn_owner_for_nondefault_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(
                root,
                {
                    "schema_version": 1,
                    "selected_agents": ["Claude", "Codex", "Gemini"],
                    "role_bindings": {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
                    "role_options": {
                        "advisory_enabled": True,
                        "operator_stop_enabled": True,
                        "session_arbitration_enabled": True,
                    },
                    "mode_flags": {
                        "single_agent_mode": False,
                        "self_verify_allowed": False,
                        "self_advisory_allowed": False,
                    },
                },
            )

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
                "claude_pane_target": "claude-pane",
                "verify_pane_target": "codex-pane",
                "gemini_pane_target": "gemini-pane",
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
                "startup_turn_claude",
                active_control_file="claude_handoff.md",
                active_control_seq=23,
            )

            state_path = base_dir / "state" / "turn_state.json"
            data = json.loads(state_path.read_text())
            self.assertEqual(data["state"], "IMPLEMENT_ACTIVE")
            self.assertEqual(
                data["legacy_state"],
                watcher_core.legacy_turn_state_name(watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE.value),
            )
            self.assertEqual(data["active_role"], "implement")
            self.assertEqual(data["active_lane"], "Codex")

    def test_runtime_export_keeps_claude_working_while_implement_control_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            with mock.patch("watcher_core._capture_pane_text", return_value="• Working (12s • esc to interrupt)\n"):
                core._transition_turn(
                    watcher_core.WatcherTurnState.CODEX_VERIFY,
                    "work_needs_verify",
                    active_control_file="claude_handoff.md",
                    active_control_seq=17,
                    verify_job_id="test-job-1",
                )

            status_path = base_dir / "runs" / core.run_id / "status.json"
            status = json.loads(status_path.read_text())
            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            codex = next(lane for lane in status["lanes"] if lane["name"] == "Codex")

            self.assertEqual(status["control"]["active_control_status"], "implement")
            self.assertEqual(claude["state"], "WORKING")
            self.assertEqual(codex["state"], "WORKING")

    def test_runtime_export_keeps_idle_claude_ready_during_verify_follow_on(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            handoff_path = base_dir / "claude_handoff.md"
            handoff_path.write_text("STATUS: implement\nCONTROL_SEQ: 17\n", encoding="utf-8")

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            with mock.patch(
                "watcher_core._capture_pane_text",
                return_value=(
                    "❯ \n"
                    "───────────────────────────────────────────────────────────────────────────────\n"
                    "  ⏵⏵ bypass permissions on (shift+tab to cycle) · esc to interrupt\n"
                ),
            ):
                core._transition_turn(
                    watcher_core.WatcherTurnState.CODEX_VERIFY,
                    "work_needs_verify",
                    active_control_file="claude_handoff.md",
                    active_control_seq=17,
                    verify_job_id="test-job-1",
                )

            status_path = base_dir / "runs" / core.run_id / "status.json"
            status = json.loads(status_path.read_text())
            claude = next(lane for lane in status["lanes"] if lane["name"] == "Claude")
            codex = next(lane for lane in status["lanes"] if lane["name"] == "Codex")

            self.assertEqual(status["control"]["active_control_status"], "implement")
            self.assertEqual(claude["state"], "READY")
            self.assertEqual(codex["state"], "WORKING")

    def test_transition_updates_internal_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            core = watcher_core.WatcherCore({
                "watch_dir": str(watch_dir),
                "base_dir": str(base_dir),
                "repo_root": str(root),
                "dry_run": True,
            })

            core._transition_turn(
                watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE,
                "startup",
            )
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)

            core._transition_turn(
                watcher_core.WatcherTurnState.IDLE,
                "claude_idle_timeout",
            )
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IDLE)


class BusyLaneNotificationDeferTest(unittest.TestCase):
    def test_gemini_request_idle_retry_redispatches_when_advice_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            request_path = base_dir / "gemini_request.md"
            advice_path = base_dir / "gemini_advice.md"
            request_path.write_text("STATUS: request_open\nCONTROL_SEQ: 18\n", encoding="utf-8")
            advice_path.write_text("STATUS: advice_ready\nCONTROL_SEQ: 17\n", encoding="utf-8")
            old = time.time() - 10.0
            os.utime(request_path, (old, old))
            os.utime(advice_path, (old, old))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "gemini_pane_target": "gemini-pane",
                    "gemini_advisory_retry_sec": 5.0,
                }
            )
            core._initial_turn_checked = True
            core._last_gemini_request_sig = core._get_path_sig(request_path)
            core._last_gemini_advice_sig = core._get_path_sig(advice_path)
            core._transition_turn(
                watcher_core.WatcherTurnState.ADVISORY_ACTIVE,
                "test_setup_gemini",
                active_control_file="gemini_request.md",
                active_control_seq=18,
            )
            core._turn_entered_at = time.time() - 10.0

            with (
                mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="› \n tab to queue message\n55% context left\n",
                ),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core._poll()

            send_prompt.assert_called_once()
            args, kwargs = send_prompt.call_args
            self.assertEqual(args[0], "gemini-pane")
            self.assertEqual(kwargs.get("pane_type"), "gemini")
            events = [
                json.loads(line)
                for line in core.run_events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(event.get("event_type") == "gemini_advisory_retry" for event in events))

    def test_gemini_request_idle_retry_skips_when_current_advice_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            request_path = base_dir / "gemini_request.md"
            advice_path = base_dir / "gemini_advice.md"
            request_path.write_text("STATUS: request_open\nCONTROL_SEQ: 18\n", encoding="utf-8")
            advice_path.write_text("STATUS: advice_ready\nCONTROL_SEQ: 18\n", encoding="utf-8")
            old = time.time() - 10.0
            os.utime(advice_path, (old, old))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "gemini_pane_target": "gemini-pane",
                    "gemini_advisory_retry_sec": 5.0,
                }
            )
            core._initial_turn_checked = True
            core._last_gemini_request_sig = core._get_path_sig(request_path)
            core._last_gemini_advice_sig = core._get_path_sig(advice_path)
            core._transition_turn(
                watcher_core.WatcherTurnState.ADVISORY_ACTIVE,
                "test_setup_gemini",
                active_control_file="gemini_request.md",
                active_control_seq=18,
            )
            core._turn_entered_at = time.time() - 10.0

            with (
                mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="› \n tab to queue message\n55% context left\n",
                ),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core._poll()

            send_prompt.assert_not_called()

    def test_gemini_advice_followup_defers_until_codex_prompt_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            (base_dir / "gemini_advice.md").write_text(
                "STATUS: advice_ready\nCONTROL_SEQ: 18\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )
            core._last_gemini_advice_sig = ""

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="• Working (18s • esc to interrupt)\n"),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core._check_pipeline_signal_updates()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.VERIFY_FOLLOWUP)
            pending_key = "codex_verify:gemini_advice_followup:18"
            self.assertIn(pending_key, core.dispatch_queue.pending_notifications)
            send_prompt.assert_not_called()
            events = [
                json.loads(line)
                for line in core.run_events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(event.get("event_type") == "lane_input_deferred" for event in events))

            with (
                mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="› \n tab to queue message\n55% context left\n",
                ),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core._check_pipeline_signal_updates()

            send_prompt.assert_called_once()
            self.assertNotIn(pending_key, core.dispatch_queue.pending_notifications)

    def test_claude_handoff_notify_defers_until_prompt_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            (base_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 19\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                }
            )
            core._last_claude_handoff_sig = ""

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="Discombobulating... (22s)\n"),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core._check_pipeline_signal_updates()

            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)
            pending_key = "claude_implement:claude_handoff:19"
            self.assertIn(pending_key, core.dispatch_queue.pending_notifications)
            send_prompt.assert_not_called()

            with (
                mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="How is Claude doing this session? (optional)\n❯ \n  ⏵⏵ bypass permissions on (shift+tab to cycle)\n",
                ),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core._check_pipeline_signal_updates()

            send_prompt.assert_called_once()
            self.assertNotIn(pending_key, core.dispatch_queue.pending_notifications)

    def test_claude_handoff_dispatches_when_busy_marker_is_only_old_scrollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            (base_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 19\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                }
            )
            core._last_claude_handoff_sig = ""
            pane_text = "\n".join(
                [
                    "• Working (22s • esc to interrupt)",
                    *[f"older output line {idx}" for idx in range(24)],
                    "How is Claude doing this session? (optional)",
                    "❯ ",
                    "  ⏵⏵ bypass permissions on (shift+tab to cycle)",
                ]
            )

            with (
                mock.patch("watcher_core._capture_pane_text", return_value=pane_text),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core._check_pipeline_signal_updates()

            send_prompt.assert_called_once()
            self.assertEqual(send_prompt.call_args.args[0], "claude-pane")
            self.assertNotIn("claude_implement:claude_handoff:19", core.dispatch_queue.pending_notifications)

    def test_blocked_triage_defers_until_codex_prompt_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            (base_dir / "claude_handoff.md").write_text(
                "STATUS: implement\nCONTROL_SEQ: 20\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            signal = {
                "reason": "handoff_already_completed",
                "reason_code": "already_implemented",
                "escalation_class": "codex_triage",
                "fingerprint": "block-123",
                "source": "sentinel",
            }

            with (
                mock.patch("watcher_core._capture_pane_text", return_value="• Working (22s • esc to interrupt)\n"),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                ok = core._notify_codex_blocked_triage(signal, "claude_implement_blocked")

            self.assertTrue(ok)
            pending_key = "codex_verify:codex_blocked_triage:20"
            self.assertIn(pending_key, core.dispatch_queue.pending_notifications)
            send_prompt.assert_not_called()
            events = [
                json.loads(line)
                for line in core.run_events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(event.get("event_type") == "lane_input_deferred" for event in events))

            with (
                mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="› \n tab to queue message\n55% context left\n",
                ),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core.dispatch_queue.flush_pending()

            send_prompt.assert_called_once()
            self.assertNotIn(pending_key, core.dispatch_queue.pending_notifications)

    def test_stale_codex_pending_notification_is_dropped_before_claude_handoff_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            operator_request = base_dir / "operator_request.md"
            operator_request.write_text(
                "STATUS: needs_operator\nCONTROL_SEQ: 20\nREASON_CODE: slice_ambiguity\n",
                encoding="utf-8",
            )
            handoff = base_dir / "claude_handoff.md"
            handoff.write_text(
                "STATUS: implement\nCONTROL_SEQ: 21\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "claude_pane_target": "claude-pane",
                    "verify_pane_target": "codex-pane",
                }
            )
            core._last_operator_request_sig = core._get_path_sig(operator_request)
            core._last_claude_handoff_sig = ""
            core.dispatch_queue.pending_notifications["codex_operator_retriage"] = {
                "notify_kind": "codex_operator_retriage",
                "lane_role": "verify",
                "reason": "operator_wait_idle_retriage",
                "prompt": "stale codex retriage",
                "prompt_path": str(operator_request),
                "target": "codex-pane",
                "pane_type": "codex",
                "control_seq": 20,
                "expected_status": "needs_operator",
                "expected_control_path": "operator_request.md",
                "expected_control_seq": 20,
                "require_active_control": False,
                "sig": core._get_path_sig(operator_request),
            }

            with (
                mock.patch(
                    "watcher_core._capture_pane_text",
                    return_value="How is Claude doing this session? (optional)\n❯ \n  ⏵⏵ bypass permissions on (shift+tab to cycle)\n",
                ),
                mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_prompt,
            ):
                core._check_pipeline_signal_updates()

            send_prompt.assert_called_once()
            self.assertEqual(send_prompt.call_args.args[0], "claude-pane")
            self.assertNotIn("codex_operator_retriage", core.dispatch_queue.pending_notifications)
            self.assertEqual(core._current_turn_state, watcher_core.WatcherTurnState.IMPLEMENT_ACTIVE)
            raw_events = [
                json.loads(line)
                for line in (core.events_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            drop_event = next(
                event for event in raw_events if event.get("event") == "lane_input_deferred_dropped"
            )
            self.assertEqual(drop_event["reason"], "control_mismatch")
            self.assertEqual(drop_event["reason_code"], "control_file_drift")
            self.assertEqual(drop_event["expected_control_seq"], 20)
            self.assertEqual(drop_event["active_control_seq"], 21)
            self.assertEqual(
                drop_event["expected_prompt_path"],
                str(operator_request),
            )
            self.assertEqual(
                drop_event["active_prompt_path"],
                str(handoff),
            )


class VerifyCompletionContractTest(unittest.TestCase):
    def test_control_slot_change_without_verify_note_keeps_verify_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            verify_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["docs/ACCEPTANCE_CRITERIA.md"])
            job = watcher_core.JobState.from_artifact("job-verify-contract", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 5
            job.done_deadline_at = time.time() + 30

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 19\n", encoding="utf-8")

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

            verify_note = root / "verify" / "4" / "10" / "2026-04-10-slice-verification.md"
            _write_verify_note(verify_note, ["verify/4/10/2026-04-10-slice-verification.md"])

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

            job.done_dispatch_id = job.dispatch_id
            job.done_at = time.time() - 1
            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)
            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_DONE)
            self.assertEqual(job.verify_result, "passed_by_feedback")
            self.assertTrue(job.verify_manifest_path)
            manifest_path = Path(job.verify_manifest_path)
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["role"], "slot_verify")
            self.assertEqual(
                manifest["feedback_path"],
                "verify/4/10/2026-04-10-slice-verification.md",
            )

    def test_verify_tree_change_without_current_round_receipt_keeps_verify_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            verify_day = verify_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            verify_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            old_verify_note = verify_day / "2026-04-10-old-verification.md"
            _write_verify_note(old_verify_note, ["verify/4/10/2026-04-10-old-verification.md"])
            os.utime(old_verify_note, (10.0, 10.0))
            job = watcher_core.JobState.from_artifact("job-verify-receipt", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

    def test_idle_timeout_with_incomplete_outputs_requeues_verify_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-retry", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 400
            job.done_dispatch_id = job.dispatch_id
            job.done_at = time.time() - 395
            job.last_activity_at = time.time() - 400
            job.last_dispatch_at = time.time() - 400
            job.last_pane_snapshot = "$ "
            core.sm.runtime_started_at = time.time() - 800

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertGreater(job.last_failed_dispatch_at, 0.0)
            self.assertEqual(job.last_failed_dispatch_snapshot, "")
            self.assertGreaterEqual(job.dispatch_fail_count, 1)
            self.assertEqual(job.completion_stall_count, 1)
            self.assertEqual(job.completion_stall_stage, "receipt_close_missing")
            self.assertEqual(job.lane_note, "waiting_receipt_close_after_task_done")
            self.assertEqual(job.verify_receipt_baseline_path, "")
            self.assertFalse(
                core.dedupe.is_duplicate(job.job_id, job.round, job.artifact_hash, "slot_verify")
            )

            job.last_failed_dispatch_at = time.time() - 30
            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

    def test_idle_prompt_with_incomplete_outputs_requeues_before_long_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-quick-idle", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_incomplete_idle_retry_sec": 20.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)

            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = time.time() - 35
            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 30
            job.done_dispatch_id = job.dispatch_id
            job.done_at = time.time() - 25
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertGreater(job.last_failed_dispatch_at, 0.0)
            self.assertEqual(job.last_failed_dispatch_snapshot, "")
            self.assertEqual(job.dispatch_stall_count, 0)
            self.assertEqual(job.completion_stall_count, 1)
            self.assertEqual(job.completion_stall_stage, "receipt_close_missing")
            self.assertEqual(job.degraded_reason, "")
            self.assertEqual(job.lane_note, "waiting_receipt_close_after_task_done")
            self.assertIn("TASK_DONE", job.history[-1]["reason"])

    def test_repeated_dispatch_stall_marks_job_degraded_after_one_requeue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-stall-repeat", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_incomplete_idle_retry_sec": 20.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            first_dispatch_at = time.time() - 35
            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = first_dispatch_at
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.dispatch_stall_count, 1)
            self.assertEqual(job.degraded_reason, "")

            job.last_failed_dispatch_at = time.time() - 30
            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.dispatch_stall_count, 1)
            self.assertEqual(job.degraded_reason, "")

            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = time.time() - 35
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = "› prompt"

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.dispatch_stall_count, 2)
            self.assertEqual(job.degraded_reason, "dispatch_stall")
            self.assertEqual(job.dispatch_stall_stage, "dispatch_seen_missing")
            self.assertEqual(job.lane_note, "waiting_dispatch_seen_after_dispatch")

            with mock.patch("watcher_core.tmux_send_keys", return_value=True) as send_keys:
                same_job = core.sm._handle_verify_pending(job)

            self.assertIs(same_job, job)
            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            send_keys.assert_not_called()

    def test_delayed_task_accepted_does_not_false_stall_before_accept_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-delayed-accept", str(work_note))

            with mock.patch.dict(os.environ, {"PIPELINE_RUNTIME_DISABLE_EXPORTER": "1"}):
                core = watcher_core.WatcherCore(
                    {
                        "watch_dir": str(watch_dir),
                        "base_dir": str(base_dir),
                        "repo_root": str(root),
                        "dry_run": True,
                        "verify_pane_target": "codex-pane",
                        "verify_incomplete_idle_retry_sec": 20.0,
                        "verify_accept_deadline_sec": 30.0,
                    }
                )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "READY",
                {"reason": "prompt_visible"},
                source="wrapper",
                derived_from="vendor_output",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "HEARTBEAT",
                {},
                source="wrapper",
                derived_from="process_alive",
            )

            job.last_activity_at = time.time() - 25
            job.last_dispatch_at = time.time() - 25
            job.accept_deadline_at = time.time() + 5
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.degraded_reason, "")
            self.assertEqual(job.accepted_dispatch_id, "")

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "DISPATCH_SEEN",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="task_hint",
            )

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.seen_dispatch_id, job.dispatch_id)
            self.assertEqual(job.accepted_dispatch_id, "")
            self.assertEqual(job.degraded_reason, "")

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="vendor_output",
            )

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.accepted_dispatch_id, job.dispatch_id)
            self.assertEqual(job.degraded_reason, "")

    def test_verify_dispatch_persists_round_scoped_control_seq_across_requeue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-dispatch-seq", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.dispatch_control_seq, 1)
            first_dispatch_id = job.dispatch_id

            job = core.sm._requeue_verify_pending(
                job,
                current_pane="› prompt",
                reason="retry verify dispatch",
            )
            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.dispatch_control_seq, 1)

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.dispatch_control_seq, 1)
            self.assertNotEqual(job.dispatch_id, first_dispatch_id)

    def test_task_done_missing_requeues_then_degrades_same_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-task-done-missing", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_done_deadline_sec": 45.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 60
            job.done_deadline_at = time.time() - 1
            job.last_activity_at = time.time() - 60
            job.last_dispatch_at = time.time() - 60
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.completion_stall_count, 1)
            self.assertEqual(job.completion_stall_stage, "task_done_missing")
            self.assertEqual(job.lane_note, "waiting_task_done_after_accept")
            self.assertEqual(job.degraded_reason, "")

            job.last_failed_dispatch_at = time.time() - 30
            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.completion_stall_count, 1)
            self.assertEqual(job.degraded_reason, "")

            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 60
            job.done_deadline_at = time.time() - 1
            job.last_activity_at = time.time() - 60
            job.last_dispatch_at = time.time() - 60
            job.last_pane_snapshot = "› prompt"

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.completion_stall_count, 2)
            self.assertEqual(job.completion_stall_stage, "task_done_missing")
            self.assertEqual(job.degraded_reason, "post_accept_completion_stall")
            self.assertEqual(job.lane_note, "waiting_task_done_after_accept")

    def test_background_terminal_wait_does_not_trigger_task_done_stall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-background-wait", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_done_deadline_sec": 45.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            original_deadline = time.time() - 1
            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 60
            job.done_deadline_at = original_deadline
            job.last_activity_at = time.time() - 60
            job.last_dispatch_at = time.time() - 60
            job.last_pane_snapshot = (
                "Waiting for background terminal (3m 33s) · 1 background terminal running /ps to view /stop to close\n"
                "› Type your message\n"
            )
            core.sm.runtime_started_at = time.time() - 120

            current_pane = (
                "Waiting for background terminal (3m 38s) · 1 background terminal running /ps to view /stop to close\n"
                "› Type your message\n"
            )
            with mock.patch("watcher_core._capture_pane_text", return_value=current_pane), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=True), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.completion_stall_count, 0)
            self.assertEqual(job.degraded_reason, "")
            self.assertGreater(job.done_deadline_at, original_deadline)
            self.assertGreater(job.last_activity_at, time.time() - 10)

    def test_task_done_without_receipt_close_uses_post_done_machine_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-receipt-close-missing", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_incomplete_idle_retry_sec": 20.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 35
            job.done_dispatch_id = job.dispatch_id
            job.done_at = time.time() - 30
            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = time.time() - 35
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.completion_stall_count, 1)
            self.assertEqual(job.completion_stall_stage, "receipt_close_missing")
            self.assertEqual(job.lane_note, "waiting_receipt_close_after_task_done")
            self.assertEqual(job.degraded_reason, "")

    # added before AXIS-G14 (seq 613) run; undocumented scope addition (dirty worktree, origin seq unknown)
    def test_late_old_task_done_does_not_close_new_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            verify_day = verify_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            verify_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-stale-task-done", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_done_deadline_sec": 45.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 10
            job.done_deadline_at = time.time() + 30
            self.assertEqual(job.done_dispatch_id, "")

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_DONE",
                {
                    "job_id": job.job_id,
                    "dispatch_id": "old-dispatch",
                    "control_seq": 19,
                    "reason": "duplicate_handoff",
                },
                source="wrapper",
                derived_from="vendor_output",
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 19\n", encoding="utf-8")
            verify_note = verify_day / "2026-04-10-slice-verification.md"
            _write_verify_note(verify_note, ["verify/4/10/2026-04-10-slice-verification.md"])

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.done_dispatch_id, "")
            self.assertEqual(job.degraded_reason, "")
            self.assertEqual(job.verify_result, "")

    # added during seq 613 verify_fsm output-close fallback round
    def test_outputs_complete_infers_task_done_after_done_deadline_when_wrapper_misses_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            verify_day = verify_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            verify_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["watcher_core.py"])
            job = watcher_core.JobState.from_artifact("job-verify-output-close", str(work_note))

            with mock.patch.dict(os.environ, {"PIPELINE_RUNTIME_DISABLE_EXPORTER": "1"}):
                core = watcher_core.WatcherCore(
                    {
                        "watch_dir": str(watch_dir),
                        "base_dir": str(base_dir),
                        "repo_root": str(root),
                        "dry_run": True,
                        "verify_pane_target": "codex-pane",
                        "verify_done_deadline_sec": 45.0,
                    }
                )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "DISPATCH_SEEN",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="task_hint",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="vendor_output",
            )

            handoff = base_dir / "claude_handoff.md"
            handoff.write_text("STATUS: implement\nCONTROL_SEQ: 19\n", encoding="utf-8")
            verify_note = verify_day / "2026-04-10-slice-verification.md"
            _write_verify_note_for_work(verify_note, "work/4/10/2026-04-10-slice.md")

            job.accepted_dispatch_id = job.dispatch_id
            job.accepted_at = time.time() - 60
            job.done_deadline_at = time.time() - 1
            job.last_activity_at = time.time() - 60
            job.last_dispatch_at = time.time() - 60
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_DONE)
            self.assertEqual(job.done_dispatch_id, job.dispatch_id)
            self.assertEqual(job.verify_result, "passed_by_feedback")
            self.assertEqual(job.completion_stall_count, 0)
            self.assertEqual(job.degraded_reason, "")
            self.assertTrue(
                any("inferred TASK_DONE" in str(entry.get("reason") or "") for entry in job.history)
            )

    def test_matching_task_done_implies_accept_when_wrapper_model_already_folded_accept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_watcher_core.py"])
            job = watcher_core.JobState.from_artifact("job-verify-folded-accept", str(work_note))

            with mock.patch.dict(os.environ, {"PIPELINE_RUNTIME_DISABLE_EXPORTER": "1"}):
                core = watcher_core.WatcherCore(
                    {
                        "watch_dir": str(watch_dir),
                        "base_dir": str(base_dir),
                        "repo_root": str(root),
                        "dry_run": True,
                        "verify_pane_target": "codex-pane",
                        "verify_accept_deadline_sec": 30.0,
                        "verify_done_deadline_sec": 45.0,
                    }
                )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "DISPATCH_SEEN",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="task_hint",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_ACCEPTED",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="vendor_output",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "TASK_DONE",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                },
                source="wrapper",
                derived_from="vendor_output",
            )
            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "READY",
                {"reason": "prompt_visible"},
                source="wrapper",
                derived_from="vendor_output",
            )

            job.last_activity_at = time.time() - 35
            job.last_dispatch_at = time.time() - 35
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = ""
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            self.assertEqual(job.accepted_dispatch_id, job.dispatch_id)
            self.assertEqual(job.done_dispatch_id, job.dispatch_id)
            self.assertEqual(job.dispatch_stall_count, 0)
            self.assertEqual(job.dispatch_stall_stage, "")
            self.assertEqual(job.lane_note, "")

    def test_dispatch_seen_missing_uses_distinct_machine_note_before_degrade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-seen-missing", str(work_note))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_incomplete_idle_retry_sec": 20.0,
                    "verify_accept_deadline_sec": 30.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = time.time() - 35
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.dispatch_stall_count, 1)
            self.assertEqual(job.dispatch_stall_stage, "dispatch_seen_missing")
            self.assertEqual(job.lane_note, "waiting_dispatch_seen_after_dispatch")

    def test_dispatch_seen_without_accept_uses_task_accept_machine_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-verify-task-accept-missing", str(work_note))

            with mock.patch.dict(os.environ, {"PIPELINE_RUNTIME_DISABLE_EXPORTER": "1"}):
                core = watcher_core.WatcherCore(
                    {
                        "watch_dir": str(watch_dir),
                        "base_dir": str(base_dir),
                        "repo_root": str(root),
                        "dry_run": True,
                        "verify_pane_target": "codex-pane",
                        "verify_accept_deadline_sec": 30.0,
                    }
                )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "DISPATCH_SEEN",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="task_hint",
            )

            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = time.time() - 35
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = "› prompt"
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value="› prompt"), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.dispatch_stall_count, 1)
            self.assertEqual(job.dispatch_stall_stage, "task_accept_missing")
            self.assertEqual(job.lane_note, "waiting_task_accept_after_dispatch")

    def test_verify_running_startup_recovery_requeues_stale_idle_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["tests/test_web_app.py"])
            job = watcher_core.JobState.from_artifact("job-startup-recovery", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_RUNNING
            job.artifact_hash = "artifact-hash"
            job.dispatch_id = "dispatch-startup-recovery"
            job.last_dispatch_at = time.time() - 30
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = "$ "
            job.last_activity_at = time.time() - 5

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "restart_recovery_grace_sec": 5.0,
                }
            )
            core.sm.runtime_started_at = time.time() - 10
            core.sm.dedupe.mark_dispatch(
                job.job_id,
                job.round,
                job.artifact_hash,
                "slot_verify",
                "codex-pane",
                True,
            )

            with mock.patch("watcher_core._capture_pane_text", return_value="$ "), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.last_dispatch_slot, "")
            self.assertFalse(
                core.dedupe.is_duplicate(job.job_id, job.round, job.artifact_hash, "slot_verify")
            )

    def test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            verify_day = verify_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            verify_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            older_work = work_day / "2026-04-10-older.md"
            latest_work = work_day / "2026-04-10-latest.md"
            _write_work_note(older_work, ["watcher_dispatch.py"])
            _write_work_note(latest_work, ["tests/test_pipeline_runtime_gate.py"])
            verify_note = verify_day / "2026-04-10-latest-verification.md"
            _write_verify_note_for_work(verify_note, "work/4/10/2026-04-10-latest.md")

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            pending_job_id = watcher_core.make_job_id(watch_dir, older_work)
            pending_job = watcher_core.JobState.from_artifact(
                pending_job_id,
                str(older_work),
                run_id=core.run_id,
            )
            pending_job.status = watcher_core.JobStatus.VERIFY_PENDING
            pending_job.save(core.state_dir)

            core._initial_turn_checked = True
            core._current_turn_state = watcher_core.WatcherTurnState.CODEX_VERIFY

            with mock.patch.object(core.sm, "step", side_effect=lambda job: job) as step_mock:
                core._poll()

            step_mock.assert_called_once()
            stepped_job = step_mock.call_args.args[0]
            self.assertEqual(stepped_job.job_id, pending_job_id)
            self.assertEqual(stepped_job.status, watcher_core.JobStatus.VERIFY_PENDING)

    def test_poll_archives_verified_pending_job_before_latest_unverified_work_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            verify_dir = root / "verify"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            verify_day = verify_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            verify_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            old_work = work_day / "2026-04-10-old.md"
            latest_work = work_day / "2026-04-10-latest.md"
            old_verify = verify_day / "2026-04-10-old-verification.md"
            _write_work_note(old_work, ["watcher_core.py"])
            _write_verify_note_for_work(old_verify, "work/4/10/2026-04-10-old.md")
            _write_work_note(latest_work, ["tests/test_watcher_core.py"])
            now = time.time()
            os.utime(old_work, (now - 30, now - 30))
            os.utime(old_verify, (now - 20, now - 20))
            os.utime(latest_work, (now - 10, now - 10))

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            old_job_id = watcher_core.make_job_id(watch_dir, old_work)
            old_job = watcher_core.JobState.from_artifact(
                old_job_id,
                str(old_work),
                run_id=core.run_id,
            )
            old_job.status = watcher_core.JobStatus.VERIFY_PENDING
            old_job.save(core.state_dir)
            latest_job_id = watcher_core.make_job_id(watch_dir, latest_work)

            core._initial_turn_checked = True
            core._transition_turn(watcher_core.WatcherTurnState.IDLE, "test_setup")

            with mock.patch.object(core.sm, "step", side_effect=lambda job: job) as step_mock:
                core._poll()

            step_mock.assert_called_once()
            stepped_job = step_mock.call_args.args[0]
            self.assertEqual(stepped_job.job_id, latest_job_id)
            self.assertIsNone(watcher_core.JobState.load(core.state_dir, old_job_id))
            archived = (
                base_dir
                / "runs"
                / core.run_id
                / "state-archive"
                / f"{old_job_id}.json"
            )
            self.assertTrue(archived.exists())

    def test_poll_steps_current_run_verify_running_before_pending_gemini_advice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["watcher_core.py"])
            (base_dir / "gemini_advice.md").write_text(
                "STATUS: advice_ready\nCONTROL_SEQ: 7\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            running_job_id = watcher_core.make_job_id(watch_dir, work_note)
            running_job = watcher_core.JobState.from_artifact(
                running_job_id,
                str(work_note),
                run_id=core.run_id,
            )
            running_job.status = watcher_core.JobStatus.VERIFY_RUNNING
            running_job.save(core.state_dir)

            core._initial_turn_checked = True
            core._current_turn_state = watcher_core.WatcherTurnState.VERIFY_FOLLOWUP

            with (
                mock.patch.object(core, "_check_pipeline_signal_updates"),
                mock.patch.object(core, "_retry_gemini_advisory_if_idle") as retry_mock,
                mock.patch.object(core.sm, "step", side_effect=lambda job: job) as step_mock,
            ):
                core._poll()

            step_mock.assert_called_once()
            stepped_job = step_mock.call_args.args[0]
            self.assertEqual(stepped_job.job_id, running_job_id)
            self.assertEqual(stepped_job.status, watcher_core.JobStatus.VERIFY_RUNNING)
            retry_mock.assert_not_called()

    def test_poll_defers_current_run_verify_pending_while_gemini_request_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-slice.md"
            _write_work_note(work_note, ["watcher_core.py"])
            (base_dir / "gemini_request.md").write_text(
                "STATUS: request_open\nCONTROL_SEQ: 8\n",
                encoding="utf-8",
            )

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            pending_job_id = watcher_core.make_job_id(watch_dir, work_note)
            pending_job = watcher_core.JobState.from_artifact(
                pending_job_id,
                str(work_note),
                run_id=core.run_id,
            )
            pending_job.status = watcher_core.JobStatus.VERIFY_PENDING
            pending_job.save(core.state_dir)

            core._initial_turn_checked = True
            core._current_turn_state = watcher_core.WatcherTurnState.ADVISORY_ACTIVE

            with (
                mock.patch.object(core, "_check_pipeline_signal_updates"),
                mock.patch.object(core, "_retry_gemini_advisory_if_idle") as retry_mock,
                mock.patch.object(core.sm, "step", side_effect=lambda job: job) as step_mock,
            ):
                core._poll()

            step_mock.assert_not_called()
            retry_mock.assert_called_once_with()
            persisted_job = watcher_core.JobState.load(core.state_dir, pending_job_id)
            self.assertIsNotNone(persisted_job)
            self.assertEqual(persisted_job.status, watcher_core.JobStatus.VERIFY_PENDING)

    def test_poll_skips_new_verify_candidate_scan_during_codex_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            work_day = watch_dir / "4" / "10"
            work_day.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = work_day / "2026-04-10-stale.md"
            _write_work_note(work_note, ["watcher_core.py"])
            job_id = watcher_core.make_job_id(watch_dir, work_note)

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            core._initial_turn_checked = True
            core._current_turn_state = watcher_core.WatcherTurnState.VERIFY_FOLLOWUP

            with (
                mock.patch.object(core, "_check_pipeline_signal_updates"),
                mock.patch.object(core, "_check_operator_wait_idle_timeout"),
                mock.patch.object(core.sm, "step", side_effect=lambda job: job) as step_mock,
            ):
                core._poll()

            step_mock.assert_not_called()
            self.assertIsNone(watcher_core.JobState.load(core.state_dir, job_id))


class CodexDispatchConfirmationTest(unittest.TestCase):
    def test_dispatch_codex_clears_existing_prompt_input_before_paste(self) -> None:
        snapshots = iter([
            "› stale draft",
            "processing view without prompt",
        ])
        run_calls: list[list[str]] = []

        def _run(cmd, **kwargs):
            run_calls.append(list(cmd))
            return mock.Mock(stdout="", stderr=b"")

        with mock.patch("watcher_core.subprocess.run", side_effect=_run), \
             mock.patch("watcher_core._capture_pane_text", side_effect=lambda _pane: next(snapshots)), \
             mock.patch("watcher_core._pane_has_working_indicator", return_value=True), \
             mock.patch("watcher_core.time.sleep", return_value=None):
            result = watcher_core._dispatch_codex("%1", "ROLE: verify")

        self.assertTrue(result)
        self.assertGreaterEqual(len(run_calls), 3)
        self.assertEqual(run_calls[0], ["tmux", "send-keys", "-t", "%1", "C-u"])

    def test_dispatch_codex_returns_true_when_prompt_is_consumed_without_immediate_confirmation(self) -> None:
        snapshots = itertools.chain(
            [
                "› prompt pasted",
                "processing view without prompt",
            ],
            itertools.repeat("processing view without prompt"),
        )

        with mock.patch("watcher_core.subprocess.run") as run_mock, \
             mock.patch("watcher_core._capture_pane_text", side_effect=lambda _pane: next(snapshots)), \
             mock.patch("watcher_core._pane_has_working_indicator", return_value=False), \
             mock.patch("watcher_core._pane_text_has_codex_activity", return_value=False), \
             mock.patch("watcher_core.time.sleep", return_value=None):
            result = watcher_core._dispatch_codex("%1", "ROLE: verify")

        self.assertTrue(result)
        self.assertGreaterEqual(run_mock.call_count, 3)

    def test_dispatch_codex_returns_false_when_prompt_never_consumes(self) -> None:
        snapshots = itertools.repeat("› prompt pasted")

        with mock.patch("watcher_core.subprocess.run") as run_mock, \
             mock.patch("watcher_core._capture_pane_text", side_effect=lambda _pane: next(snapshots)), \
             mock.patch("watcher_core._pane_text_has_codex_activity", return_value=False), \
             mock.patch("watcher_core.time.sleep", return_value=None):
            result = watcher_core._dispatch_codex("%1", "ROLE: verify")

        self.assertFalse(result)
        self.assertGreaterEqual(run_mock.call_count, 3)

    def test_dispatch_codex_returns_true_when_working_indicator_appears(self) -> None:
        snapshots = iter([
            "› prompt pasted",
            "processing view without prompt",
        ])

        with mock.patch("watcher_core.subprocess.run"), \
             mock.patch("watcher_core._capture_pane_text", side_effect=lambda _pane: next(snapshots)), \
             mock.patch("watcher_core._pane_has_working_indicator", side_effect=[True]), \
             mock.patch("watcher_core.time.sleep", return_value=None):
            result = watcher_core._dispatch_codex("%1", "ROLE: verify")

        self.assertTrue(result)

    def test_tmux_send_keys_skips_when_same_pane_dispatch_lock_is_busy(self) -> None:
        class _BusyLock:
            def acquire(self, timeout=None):
                self.timeout = timeout
                return False

            def release(self) -> None:
                raise AssertionError("release should not be called when acquire fails")

        busy_lock = _BusyLock()
        with mock.patch("watcher_core._dispatch_lock_for", return_value=busy_lock), \
             mock.patch("watcher_core._wait_for_dispatch_window") as wait_window:
            result = watcher_core.tmux_send_keys("%1", "ROLE: verify", pane_type="codex")

        self.assertFalse(result)
        self.assertEqual(busy_lock.timeout, watcher_core._DISPATCH_LOCK_TIMEOUT_SEC)
        wait_window.assert_not_called()

    def test_tmux_send_keys_releases_dispatch_lock_after_dispatch(self) -> None:
        class _TrackingLock:
            def __init__(self) -> None:
                self.released = False

            def acquire(self, timeout=None):
                self.timeout = timeout
                return True

            def release(self) -> None:
                self.released = True

        tracking_lock = _TrackingLock()
        with mock.patch("watcher_core._dispatch_lock_for", return_value=tracking_lock), \
             mock.patch("watcher_core._wait_for_dispatch_window", return_value=True), \
             mock.patch("watcher_core._dispatch_codex", return_value=True) as dispatch_codex:
            result = watcher_core.tmux_send_keys("%1", "ROLE: verify", pane_type="codex")

        self.assertTrue(result)
        self.assertEqual(tracking_lock.timeout, watcher_core._DISPATCH_LOCK_TIMEOUT_SEC)
        self.assertTrue(tracking_lock.released)
        dispatch_codex.assert_called_once_with("%1", "ROLE: verify")

    def test_tmux_send_keys_propagates_claude_dispatch_failure(self) -> None:
        class _TrackingLock:
            def __init__(self) -> None:
                self.released = False

            def acquire(self, timeout=None):
                self.timeout = timeout
                return True

            def release(self) -> None:
                self.released = True

        tracking_lock = _TrackingLock()
        with mock.patch("watcher_core._dispatch_lock_for", return_value=tracking_lock), \
             mock.patch("watcher_core._wait_for_dispatch_window", return_value=True), \
             mock.patch("watcher_core._dispatch_claude", return_value=False) as dispatch_claude:
            result = watcher_core.tmux_send_keys("%1", "ROLE: implement", pane_type="claude")

        self.assertFalse(result)
        self.assertEqual(tracking_lock.timeout, watcher_core._DISPATCH_LOCK_TIMEOUT_SEC)
        self.assertTrue(tracking_lock.released)
        dispatch_claude.assert_called_once_with("%1", "ROLE: implement")

    def test_tmux_send_keys_propagates_gemini_dispatch_failure(self) -> None:
        class _TrackingLock:
            def __init__(self) -> None:
                self.released = False

            def acquire(self, timeout=None):
                self.timeout = timeout
                return True

            def release(self) -> None:
                self.released = True

        tracking_lock = _TrackingLock()
        with mock.patch("watcher_core._dispatch_lock_for", return_value=tracking_lock), \
             mock.patch("watcher_core._wait_for_dispatch_window", return_value=True), \
             mock.patch("watcher_core._dispatch_gemini", return_value=False) as dispatch_gemini:
            result = watcher_core.tmux_send_keys("%1", "ROLE: advisory", pane_type="gemini")

        self.assertFalse(result)
        self.assertEqual(tracking_lock.timeout, watcher_core._DISPATCH_LOCK_TIMEOUT_SEC)
        self.assertTrue(tracking_lock.released)
        dispatch_gemini.assert_called_once_with("%1", "ROLE: advisory")

    def test_dispatch_gemini_returns_false_when_prompt_stays_visible(self) -> None:
        snapshots = iter([
            "› prompt pasted",
            "› prompt still visible",
            "› prompt still visible",
            "› prompt still visible",
        ])

        with mock.patch("watcher_core.subprocess.run"), \
             mock.patch("watcher_core._capture_pane_text", side_effect=lambda _pane: next(snapshots)), \
             mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True), \
             mock.patch("watcher_core._pane_text_has_gemini_activity", return_value=False), \
             mock.patch("watcher_core.time.sleep", return_value=None):
            result = watcher_core._dispatch_gemini("%1", "ROLE: advisory")

        self.assertFalse(result)


class VerifyPendingBackoffTest(unittest.TestCase):
    def test_failed_dispatch_sets_retry_backoff_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-10-slice.md"
            _write_work_note(work_note, ["e2e/tests/web-smoke.spec.mjs"])
            job = watcher_core.JobState.from_artifact("job-backoff", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_PENDING
            job.artifact_hash = "hash-1"

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=False), \
                 mock.patch("watcher_core._capture_pane_text", return_value="› pasted prompt placeholder"):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertGreater(job.last_failed_dispatch_at, 0.0)
            self.assertEqual(job.last_failed_dispatch_snapshot, "› pasted prompt placeholder")
            self.assertEqual(job.dispatch_fail_count, 1)

    def test_failed_dispatch_backoff_skips_immediate_redispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-10-slice.md"
            _write_work_note(work_note, ["e2e/tests/web-smoke.spec.mjs"])
            job = watcher_core.JobState.from_artifact("job-backoff", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_PENDING
            job.artifact_hash = "hash-1"
            job.last_failed_dispatch_at = time.time()
            job.last_failed_dispatch_snapshot = "› pasted prompt placeholder"

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch.object(core.lease, "acquire", side_effect=AssertionError("lease should not be acquired")), \
                 mock.patch("watcher_core.tmux_send_keys", side_effect=AssertionError("dispatch should not run")):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)

    def test_failed_dispatch_same_snapshot_skips_retry_after_backoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-10-slice.md"
            _write_work_note(work_note, ["e2e/tests/web-smoke.spec.mjs"])
            job = watcher_core.JobState.from_artifact("job-backoff", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_PENDING
            job.artifact_hash = "hash-1"
            job.last_failed_dispatch_at = time.time() - 30
            job.last_failed_dispatch_snapshot = "› pasted prompt placeholder"

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            with mock.patch.object(core.lease, "acquire", side_effect=AssertionError("lease should not be acquired")), \
                 mock.patch("watcher_core.tmux_send_keys", side_effect=AssertionError("dispatch should not run")), \
                 mock.patch("watcher_core._capture_pane_text", return_value="› pasted prompt placeholder"):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)

    def test_failed_dispatch_visible_prompt_skips_retry_after_backoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            work_note = watch_dir / "2026-04-10-slice.md"
            _write_work_note(work_note, ["e2e/tests/web-smoke.spec.mjs"])
            job = watcher_core.JobState.from_artifact("job-backoff", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_PENDING
            job.artifact_hash = "hash-1"
            job.last_failed_dispatch_at = time.time() - 30
            job.last_failed_dispatch_snapshot = "› stale snapshot placeholder"

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                }
            )

            _, prompt = core.sm._build_verify_prompt(job)
            visible_prompt = "\n".join(
                [
                    "Tip: use /compact when context gets long",
                    prompt,
                    "* Blanching...",
                ]
            )
            previous_failed_at = job.last_failed_dispatch_at

            with mock.patch.object(core.lease, "acquire", side_effect=AssertionError("lease should not be acquired")), \
                 mock.patch.object(core.sm, "send_keys", side_effect=AssertionError("dispatch should not run")), \
                 mock.patch.object(core.sm, "capture_pane_text", return_value=visible_prompt):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertGreater(job.last_failed_dispatch_at, previous_failed_at)
            self.assertEqual(job.last_failed_dispatch_snapshot, visible_prompt.rstrip())

    def test_dispatch_stall_pasted_content_snapshot_skips_retry_after_backoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_dir = root / "work"
            base_dir = root / ".pipeline"
            watch_dir.mkdir(parents=True, exist_ok=True)
            base_dir.mkdir(parents=True, exist_ok=True)
            _write_active_profile(root)

            run_dir = base_dir / "runs" / "run-1"
            wrapper_dir = run_dir / "wrapper-events"
            wrapper_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "current_run.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-1",
                        "events_path": ".pipeline/runs/run-1/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )

            work_note = watch_dir / "2026-04-10-slice.md"
            _write_work_note(work_note, ["watcher_core.py"])
            job = watcher_core.JobState.from_artifact("job-dispatch-stall-backoff", str(work_note))
            job.status = watcher_core.JobStatus.VERIFY_PENDING
            job.artifact_hash = "hash-1"

            core = watcher_core.WatcherCore(
                {
                    "watch_dir": str(watch_dir),
                    "base_dir": str(base_dir),
                    "repo_root": str(root),
                    "dry_run": True,
                    "verify_pane_target": "codex-pane",
                    "verify_accept_deadline_sec": 30.0,
                }
            )

            with mock.patch("watcher_core.tmux_send_keys", return_value=True):
                job = core.sm._handle_verify_pending(job)

            append_wrapper_event(
                wrapper_dir,
                "Codex",
                "DISPATCH_SEEN",
                {
                    "job_id": job.job_id,
                    "dispatch_id": job.dispatch_id,
                    "control_seq": 19,
                    "attempt": 1,
                },
                source="wrapper",
                derived_from="task_hint",
            )

            stale_snapshot = "\n".join(
                [
                    "[Pasted Content 1024 chars] #12ED, BASED_ON_WORK, and BASED_ON_VERIFY near the top",
                    "- use .pipeline/gemini_request.md before .pipeline/operator_request.md",
                    "›",
                ]
            )
            job.last_activity_at = time.time() - 30
            job.last_dispatch_at = time.time() - 35
            job.accept_deadline_at = time.time() - 1
            job.last_pane_snapshot = stale_snapshot
            core.sm.runtime_started_at = time.time() - 120

            with mock.patch("watcher_core._capture_pane_text", return_value=stale_snapshot), \
                 mock.patch("watcher_core._pane_text_has_busy_indicator", return_value=False), \
                 mock.patch("watcher_core._pane_text_has_input_cursor", return_value=True):
                job = core.sm._handle_verify_running(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)
            self.assertEqual(job.dispatch_stall_count, 1)
            self.assertEqual(job.last_failed_dispatch_snapshot, stale_snapshot)

            job.last_failed_dispatch_at = time.time() - 30

            with mock.patch.object(core.lease, "acquire", side_effect=AssertionError("lease should not be acquired")), \
                 mock.patch("watcher_core.tmux_send_keys", side_effect=AssertionError("dispatch should not run")), \
                 mock.patch("watcher_core._capture_pane_text", return_value=stale_snapshot):
                job = core.sm._handle_verify_pending(job)

            self.assertEqual(job.status, watcher_core.JobStatus.VERIFY_PENDING)


if __name__ == "__main__":
    unittest.main()
