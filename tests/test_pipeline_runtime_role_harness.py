from __future__ import annotations

import unittest

from pipeline_runtime.role_harness import (
    role_harness_map,
    role_harness_path,
    role_harness_specs,
)


class PipelineRuntimeRoleHarnessTest(unittest.TestCase):
    def test_role_harness_paths_are_role_neutral(self) -> None:
        self.assertEqual(role_harness_path("implement"), ".pipeline/harness/implement.md")
        self.assertEqual(role_harness_path("verify"), ".pipeline/harness/verify.md")
        self.assertEqual(role_harness_path("advisory"), ".pipeline/harness/advisory.md")
        self.assertEqual(role_harness_path("council"), ".pipeline/harness/council.md")
        self.assertEqual(role_harness_path("Gemini"), "")

    def test_role_harness_specs_include_purposes(self) -> None:
        specs = role_harness_specs()
        self.assertEqual([item["role"] for item in specs], ["implement", "verify", "advisory", "council"])
        self.assertTrue(all(item["purpose"] for item in specs))
        self.assertEqual(
            role_harness_map(),
            {
                "implement": ".pipeline/harness/implement.md",
                "verify": ".pipeline/harness/verify.md",
                "advisory": ".pipeline/harness/advisory.md",
                "council": ".pipeline/harness/council.md",
            },
        )


if __name__ == "__main__":
    unittest.main()
