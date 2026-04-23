from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_runtime.operator_autonomy import PR_MERGE_GATE_REASON
from pipeline_runtime.pr_merge_state import PrMergeStatusCache


class PrMergeStatusCacheTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
