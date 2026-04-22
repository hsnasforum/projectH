from __future__ import annotations

import json
import unittest
from pathlib import Path
import tempfile

from pipeline_gui.setup_profile import (
    active_profile_fingerprint,
    build_last_applied_record,
    classify_setup_entry,
    cleanup_stale_setup_artifacts,
    canonical_setup_payload_for_fingerprint,
    display_resolver_messages,
    fingerprint_payload,
    join_display_resolver_messages,
    join_resolver_messages,
    reconcile_last_applied,
    resolve_active_profile,
    resolve_active_profile_path,
    resolve_project_active_profile,
    resolve_project_runtime_adapter,
    runtime_adapter_from_resolved,
    support_policy_for_level,
)


def _profile(
    *,
    selected_agents=None,
    implement="Claude",
    verify="Codex",
    advisory="Gemini",
    advisory_enabled=True,
    self_verify_allowed=False,
    self_advisory_allowed=False,
    schema_version=1,
):
    return {
        "schema_version": schema_version,
        "selected_agents": list(selected_agents or ["Claude", "Codex", "Gemini"]),
        "role_bindings": {
            "implement": implement,
            "verify": verify,
            "advisory": advisory,
        },
        "role_options": {
            "advisory_enabled": advisory_enabled,
            "operator_stop_enabled": True,
            "session_arbitration_enabled": advisory_enabled,
        },
        "mode_flags": {
            "single_agent_mode": len(list(selected_agents or ["Claude", "Codex", "Gemini"])) == 1,
            "self_verify_allowed": self_verify_allowed,
            "self_advisory_allowed": self_advisory_allowed,
        },
    }


class PipelineGuiSetupProfileTest(unittest.TestCase):
    def test_support_policy_maps_blocked_to_preview_only(self) -> None:
        policy = support_policy_for_level("blocked")
        self.assertTrue(policy["preview_allowed"])
        self.assertFalse(policy["apply_allowed"])
        self.assertFalse(policy["launch_allowed"])
        self.assertTrue(policy["banner_required"])

    def test_fingerprint_payload_normalizes_crlf(self) -> None:
        left = {"note": "line1\r\nline2"}
        right = {"note": "line1\nline2"}
        self.assertEqual(fingerprint_payload(left), fingerprint_payload(right))

    def test_resolve_active_profile_returns_supported_for_default_three_lane(self) -> None:
        resolved = resolve_active_profile(_profile())
        self.assertEqual(resolved["resolution_state"], "ready")
        self.assertEqual(resolved["support_level"], "supported")
        self.assertTrue(resolved["controls"]["apply_allowed"])
        self.assertEqual(
            resolved["effective_runtime_plan"]["enabled_lanes"],
            ["Claude", "Codex", "Gemini"],
        )

    def test_runtime_adapter_preserves_lane_order_and_role_owners(self) -> None:
        adapter = runtime_adapter_from_resolved(resolve_active_profile(_profile()))
        self.assertEqual(adapter["enabled_lanes"], ["Claude", "Codex", "Gemini"])
        self.assertEqual(
            adapter["role_owners"],
            {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
        )
        self.assertEqual(
            adapter["prompt_owners"],
            {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
        )
        self.assertEqual(
            [lane["name"] for lane in adapter["lane_configs"]],
            ["Claude", "Codex", "Gemini"],
        )
        self.assertEqual(
            [lane["roles"] for lane in adapter["lane_configs"]],
            [["implement"], ["verify"], ["advisory"]],
        )
        lane_map = {lane["name"]: lane for lane in adapter["lane_configs"]}
        self.assertEqual(lane_map["Claude"]["read_first_doc"], "CLAUDE.md")
        self.assertEqual(lane_map["Codex"]["read_first_doc"], "AGENTS.md")
        self.assertEqual(lane_map["Gemini"]["token_source_root"], "~/.gemini/tmp")
        self.assertEqual(lane_map["Codex"]["support_rank"], 3)
        harness_map = {
            item["role"]: item["path"]
            for item in adapter["role_harnesses"]
        }
        self.assertEqual(harness_map["implement"], ".pipeline/harness/implement.md")
        self.assertEqual(harness_map["verify"], ".pipeline/harness/verify.md")
        self.assertEqual(harness_map["advisory"], ".pipeline/harness/advisory.md")
        self.assertEqual(harness_map["council"], ".pipeline/harness/council.md")

    def test_runtime_adapter_preserves_swapped_role_bindings(self) -> None:
        adapter = runtime_adapter_from_resolved(
            resolve_active_profile(_profile(implement="Codex", verify="Claude", advisory="Gemini"))
        )
        self.assertEqual(
            adapter["role_owners"],
            {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
        )
        self.assertEqual(
            adapter["prompt_owners"],
            {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
        )
        self.assertEqual(
            [lane["roles"] for lane in adapter["lane_configs"]],
            [["verify"], ["implement"], ["advisory"]],
        )

    def test_resolve_active_profile_returns_supported_for_swapped_three_lane(self) -> None:
        resolved = resolve_active_profile(
            _profile(implement="Codex", verify="Claude", advisory="Gemini")
        )
        self.assertEqual(resolved["resolution_state"], "ready")
        self.assertEqual(resolved["support_level"], "supported")

    def test_resolve_active_profile_returns_experimental_for_codex_only_self_verify(self) -> None:
        resolved = resolve_active_profile(
            _profile(
                selected_agents=["Codex"],
                implement="Codex",
                verify="Codex",
                advisory="",
                advisory_enabled=False,
                self_verify_allowed=True,
            )
        )
        self.assertEqual(resolved["resolution_state"], "ready")
        self.assertEqual(resolved["support_level"], "experimental")
        self.assertTrue(resolved["controls"]["banner_required"])
        self.assertTrue(resolved["effective_runtime_plan"]["controls"]["banner_required"])

    def test_runtime_adapter_marks_disabled_lanes_and_verify_owner_for_codex_only(self) -> None:
        adapter = runtime_adapter_from_resolved(
            resolve_active_profile(
                _profile(
                    selected_agents=["Codex"],
                    implement="Codex",
                    verify="Codex",
                    advisory="",
                    advisory_enabled=False,
                    self_verify_allowed=True,
                )
            )
        )
        self.assertEqual(adapter["enabled_lanes"], ["Codex"])
        self.assertEqual(
            adapter["role_owners"],
            {"implement": "Codex", "verify": "Codex", "advisory": None},
        )
        self.assertEqual(
            adapter["prompt_owners"],
            {"implement": "Codex", "verify": "Codex", "advisory": None},
        )
        lane_map = {lane["name"]: lane for lane in adapter["lane_configs"]}
        self.assertFalse(lane_map["Claude"]["enabled"])
        self.assertTrue(lane_map["Codex"]["enabled"])
        self.assertFalse(lane_map["Gemini"]["enabled"])
        self.assertEqual(lane_map["Codex"]["roles"], ["implement", "verify"])
        self.assertFalse(adapter["controls"]["advisory_enabled"])
        self.assertFalse(adapter["controls"]["session_arbitration_enabled"])

    def test_runtime_adapter_routes_prompt_owners_from_role_bindings_when_lanes_exist(self) -> None:
        adapter = runtime_adapter_from_resolved(
            resolve_active_profile(
                _profile(
                    selected_agents=["Claude", "Codex", "Gemini"],
                    implement="Codex",
                    verify="Claude",
                    advisory="Gemini",
                    advisory_enabled=True,
                )
            )
        )
        self.assertEqual(
            adapter["role_owners"],
            {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
        )
        self.assertEqual(
            adapter["prompt_owners"],
            {"implement": "Codex", "verify": "Claude", "advisory": "Gemini"},
        )

    def test_resolve_active_profile_blocks_invalid_same_agent_without_self_verify(self) -> None:
        resolved = resolve_active_profile(
            _profile(
                selected_agents=["Codex"],
                implement="Codex",
                verify="Codex",
                advisory="",
                advisory_enabled=False,
                self_verify_allowed=False,
            )
        )
        self.assertEqual(resolved["resolution_state"], "broken")
        self.assertEqual(resolved["support_level"], "blocked")
        self.assertFalse(resolved["controls"]["apply_allowed"])
        self.assertIsNone(resolved["effective_runtime_plan"])

    def test_resolve_active_profile_marks_old_schema_for_migration(self) -> None:
        resolved = resolve_active_profile(_profile(schema_version=0))
        self.assertEqual(resolved["resolution_state"], "needs_migration")
        self.assertEqual(resolved["support_level"], "blocked")

    def test_resolve_active_profile_path_reports_unreadable_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            active_path = Path(td) / "agent_profile.json"
            active_path.write_text("{", encoding="utf-8")
            resolved = resolve_active_profile_path(active_path)
            self.assertEqual(resolved["resolution_state"], "broken")
            self.assertEqual(resolved["support_level"], "blocked")
            self.assertEqual(join_resolver_messages(resolved), "Active profile is unreadable.")

    def test_display_resolver_messages_localizes_missing_active_profile(self) -> None:
        resolved = resolve_active_profile(None)
        self.assertEqual(
            display_resolver_messages(resolved),
            ["active profile이 없습니다 (.pipeline/config/agent_profile.json). 설정 탭에서 미리보기 생성 후 적용을 완료해 주세요."],
        )
        self.assertIn("active profile이 없습니다", join_display_resolver_messages(resolved))

    def test_resolve_project_active_profile_reads_repo_config_location(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            active_path = project / ".pipeline" / "config" / "agent_profile.json"
            active_path.parent.mkdir(parents=True, exist_ok=True)
            active_path.write_text(json.dumps(_profile(), ensure_ascii=False), encoding="utf-8")
            resolved = resolve_project_active_profile(project)
            self.assertEqual(resolved["resolution_state"], "ready")
            self.assertEqual(resolved["support_level"], "supported")
            adapter = resolve_project_runtime_adapter(project)
            self.assertEqual(adapter["enabled_lanes"], ["Claude", "Codex", "Gemini"])

    def test_classify_setup_entry_detects_first_run(self) -> None:
        state = classify_setup_entry({})
        self.assertEqual(state["entry_state"], "first_run")

    def test_classify_setup_entry_prefers_broken_active_profile(self) -> None:
        state = classify_setup_entry({"active_exists": True, "active_payload": None})
        self.assertEqual(state["entry_state"], "broken_active_profile")

    def test_classify_setup_entry_detects_needs_migration_before_resume(self) -> None:
        state = classify_setup_entry(
            {
                "legacy_profile_exists": True,
                "draft_exists": True,
            }
        )
        self.assertEqual(state["entry_state"], "needs_migration")

    def test_classify_setup_entry_detects_resume_setup(self) -> None:
        state = classify_setup_entry({"draft_exists": True})
        self.assertEqual(state["entry_state"], "resume_setup")

    def test_classify_setup_entry_prefers_resume_setup_over_ready_normal(self) -> None:
        state = classify_setup_entry(
            {
                "active_exists": True,
                "active_payload": _profile(),
                "draft_exists": True,
            }
        )
        self.assertEqual(state["entry_state"], "resume_setup")

    def test_classify_setup_entry_detects_ready_normal(self) -> None:
        state = classify_setup_entry(
            {
                "active_exists": True,
                "active_payload": _profile(),
            }
        )
        self.assertEqual(state["entry_state"], "ready_normal")

    def test_resolve_active_profile_returns_broken_on_malformed_nested_payload(self) -> None:
        resolved = resolve_active_profile(
            {
                "schema_version": 1,
                "selected_agents": 1,
                "role_bindings": 1,
                "role_options": 1,
                "mode_flags": 1,
            }
        )
        self.assertEqual(resolved["resolution_state"], "broken")
        self.assertEqual(resolved["support_level"], "blocked")
        self.assertIsNone(resolved["effective_runtime_plan"])
        self.assertTrue(any("must be" in message for message in resolved["messages"]))

    def test_resolve_active_profile_rejects_unknown_selected_agent(self) -> None:
        resolved = resolve_active_profile(
            _profile(selected_agents=["Claude", "Unknown"], verify="Claude", self_verify_allowed=True)
        )
        self.assertEqual(resolved["resolution_state"], "broken")
        self.assertEqual(resolved["support_level"], "blocked")
        self.assertTrue(any("unsupported agent: Unknown" in message for message in resolved["messages"]))

    def test_active_profile_fingerprint_ignores_executor_override(self) -> None:
        left = _profile()
        right = _profile()
        right["executor_override"] = "Codex"
        self.assertEqual(active_profile_fingerprint(left), active_profile_fingerprint(right))
        self.assertNotEqual(
            fingerprint_payload(canonical_setup_payload_for_fingerprint(left)),
            fingerprint_payload(canonical_setup_payload_for_fingerprint(right)),
        )

    def test_build_last_applied_record_uses_active_profile_fingerprint(self) -> None:
        record = build_last_applied_record(
            setup_id="setup-1",
            approved_preview_fingerprint="sha256:preview-1",
            active_payload=_profile(),
            restart_required=True,
            executor="Codex",
            applied_at="2026-04-09T00:00:00+00:00",
        )
        self.assertEqual(record["setup_id"], "setup-1")
        self.assertEqual(record["approved_preview_fingerprint"], "sha256:preview-1")
        self.assertEqual(record["active_profile_fingerprint"], active_profile_fingerprint(_profile()))
        self.assertTrue(record["restart_required"])
        self.assertEqual(record["executor"], "Codex")
        self.assertEqual(record["applied_at"], "2026-04-09T00:00:00+00:00")

    def test_reconcile_last_applied_reports_ok_and_mismatch(self) -> None:
        active = _profile()
        record = build_last_applied_record(
            setup_id="setup-1",
            approved_preview_fingerprint="sha256:preview-1",
            active_payload=active,
            restart_required=True,
            executor="Codex",
            applied_at="2026-04-09T00:00:00+00:00",
        )
        matched = reconcile_last_applied(active_payload=active, last_applied_payload=record)
        self.assertEqual(matched["status"], "ok")

        mismatched = reconcile_last_applied(
            active_payload=_profile(selected_agents=["Claude", "Codex"], advisory="", advisory_enabled=False),
            last_applied_payload=record,
        )
        self.assertEqual(mismatched["status"], "mismatch")

    def test_reconcile_last_applied_distinguishes_missing_and_broken_records(self) -> None:
        missing = reconcile_last_applied(
            active_payload=_profile(),
            last_applied_payload=None,
            last_applied_exists=False,
        )
        self.assertEqual(missing["status"], "missing")

        broken = reconcile_last_applied(
            active_payload=_profile(),
            last_applied_payload=None,
            last_applied_exists=True,
        )
        self.assertEqual(broken["status"], "broken")

        broken_shape = reconcile_last_applied(
            active_payload=_profile(),
            last_applied_payload={"setup_id": "setup-1"},
        )
        self.assertEqual(broken_shape["status"], "broken")

    def test_reconcile_last_applied_treats_missing_active_profile_as_mismatch(self) -> None:
        record = build_last_applied_record(
            setup_id="setup-1",
            approved_preview_fingerprint="sha256:preview-1",
            active_payload=_profile(),
            restart_required=True,
            executor="Codex",
            applied_at="2026-04-09T00:00:00+00:00",
        )
        reconciled = reconcile_last_applied(
            active_payload=None,
            last_applied_payload=record,
            active_exists=False,
            last_applied_exists=True,
        )
        self.assertEqual(reconciled["status"], "mismatch")
        self.assertEqual(reconciled["current_active_profile_fingerprint"], "")
        self.assertTrue(any("Active profile is missing" in message for message in reconciled["messages"]))

    def test_cleanup_stale_setup_artifacts_removes_unprotected_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            setup_dir = Path(td)
            keep_path = setup_dir / "result.json"
            remove_path = setup_dir / "request.json"
            keep_path.write_text('{"setup_id":"setup-keep"}', encoding="utf-8")
            remove_path.write_text('{"setup_id":"setup-old"}', encoding="utf-8")

            removed = cleanup_stale_setup_artifacts(
                setup_dir=setup_dir,
                protected_setup_ids={"setup-keep"},
            )

            self.assertEqual(removed, [remove_path])
            self.assertTrue(keep_path.exists())
            self.assertFalse(remove_path.exists())

    def test_cleanup_stale_setup_artifacts_removes_unreadable_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            setup_dir = Path(td)
            broken_path = setup_dir / "preview.json"
            broken_path.write_text("{", encoding="utf-8")

            removed = cleanup_stale_setup_artifacts(
                setup_dir=setup_dir,
                protected_setup_ids=set(),
            )

            self.assertEqual(removed, [broken_path])
            self.assertFalse(broken_path.exists())


if __name__ == "__main__":
    unittest.main()
