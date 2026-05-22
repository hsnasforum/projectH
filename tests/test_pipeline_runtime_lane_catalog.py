from __future__ import annotations

import unittest

from pipeline_runtime.lane_catalog import (
    AgentProfileSpec,
    _build_from_spec,
    build_agent_profile_payload,
)


class AgentProfilePayloadTest(unittest.TestCase):
    def test_build_agent_profile_payload_keeps_existing_keyword_shape(self) -> None:
        payload = build_agent_profile_payload(
            selected_agents=["Codex"],
            role_bindings={"implement": "Codex", "verify": "Codex", "unknown": "Claude"},
            advisory_enabled=False,
            operator_stop_enabled=True,
            session_arbitration_enabled=True,
            single_agent_mode=None,
            self_verify_allowed=True,
            self_advisory_allowed=True,
            schema_version=2,
        )

        self.assertEqual(
            payload,
            {
                "schema_version": 2,
                "selected_agents": ["Codex"],
                "role_bindings": {
                    "implement": "Codex",
                    "verify": "Codex",
                    "advisory": "",
                },
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

    def test_build_from_spec_matches_existing_public_builder(self) -> None:
        kwargs = {
            "selected_agents": ("Claude", "Codex"),
            "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Claude"},
            "advisory_enabled": True,
            "operator_stop_enabled": False,
            "session_arbitration_enabled": None,
            "single_agent_mode": False,
            "self_verify_allowed": False,
            "self_advisory_allowed": True,
            "schema_version": 3,
        }

        self.assertEqual(
            build_agent_profile_payload(**kwargs),
            _build_from_spec(AgentProfileSpec(**kwargs)),
        )


if __name__ == "__main__":
    unittest.main()
