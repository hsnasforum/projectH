from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline_gui.setup_controller import SetupController
from pipeline_gui.setup_models import SetupActionState
from pipeline_gui.setup_profile import build_last_applied_record
from storage.json_store_base import read_json


class PipelineGuiSetupControllerTest(unittest.TestCase):
    def test_preview_matches_current_uses_setup_id_and_draft_fingerprint(self) -> None:
        preview = {
            "setup_id": "setup-1",
            "draft_fingerprint": "sha256:draft-123",
            "preview_fingerprint": "sha256:preview-999",
        }

        self.assertTrue(
            SetupController.preview_matches_current(
                preview,
                "setup-1",
                "sha256:draft-123",
            )
        )
        self.assertFalse(
            SetupController.preview_matches_current(
                preview,
                "setup-1",
                "sha256:draft-mismatch",
            )
        )

    def test_result_can_promote_active_requires_matching_setup_and_preview_truth(self) -> None:
        controller = SetupController(Path("/tmp/projectH"))
        apply_payload = {
            "setup_id": "setup-1",
            "approved_preview_fingerprint": "sha256:preview-123",
        }
        result = {
            "status": "applied",
            "setup_id": "setup-1",
            "approved_preview_fingerprint": "sha256:preview-123",
        }
        mismatch = {
            "status": "applied",
            "setup_id": "setup-1",
            "approved_preview_fingerprint": "sha256:other",
        }
        draft = controller.default_profile()
        draft_fp = controller.fingerprint(draft)
        preview = {
            "setup_id": "setup-1",
            "draft_fingerprint": draft_fp,
            "preview_fingerprint": "sha256:preview-123",
        }

        ok, _message = SetupController.result_can_promote_active(
            result,
            apply_payload,
            preview,
            "setup-1",
            draft,
            draft_fp,
            controller.fingerprint,
        )
        self.assertTrue(ok)

        ok, _message = SetupController.result_can_promote_active(
            mismatch,
            apply_payload,
            preview,
            "setup-1",
            draft,
            draft_fp,
            controller.fingerprint,
        )
        self.assertFalse(ok)

        ok, _message = SetupController.result_can_promote_active(
            result,
            apply_payload,
            preview,
            "setup-2",
            draft,
            draft_fp,
            controller.fingerprint,
        )
        self.assertFalse(ok)

    def test_result_can_promote_active_holds_when_draft_missing_or_changed(self) -> None:
        controller = SetupController(Path("/tmp/projectH"))
        apply_payload = {
            "setup_id": "setup-1",
            "approved_preview_fingerprint": "sha256:preview-123",
        }
        result = {
            "status": "applied",
            "setup_id": "setup-1",
            "approved_preview_fingerprint": "sha256:preview-123",
        }
        draft = controller.default_profile()
        draft_fp = controller.fingerprint(draft)
        preview = {
            "setup_id": "setup-1",
            "draft_fingerprint": draft_fp,
            "preview_fingerprint": "sha256:preview-123",
        }

        ok, message = SetupController.result_can_promote_active(
            result,
            apply_payload,
            preview,
            "setup-1",
            None,
            draft_fp,
            controller.fingerprint,
        )
        self.assertFalse(ok)
        self.assertIn("draft 파일이 없어", message)

        changed = dict(draft)
        changed["executor_override"] = "Codex"
        ok, message = SetupController.result_can_promote_active(
            result,
            apply_payload,
            preview,
            "setup-1",
            changed,
            draft_fp,
            controller.fingerprint,
        )
        self.assertFalse(ok)
        self.assertIn("draft 파일이 바뀌어", message)

    def test_read_disk_state_reuses_recent_cached_reads(self) -> None:
        controller = SetupController(Path("/tmp/projectH"))

        with (
            mock.patch("pipeline_gui.setup_controller.read_json_path", return_value=None) as read_json_path,
            mock.patch("pipeline_gui.setup_controller.path_exists", return_value=False) as path_exists,
        ):
            first = controller.read_disk_state()
            second = controller.read_disk_state()

        self.assertEqual(first, second)
        self.assertEqual(read_json_path.call_count, 7)
        self.assertEqual(path_exists.call_count, 6)

    def test_resolve_runtime_active_profile_reuses_recent_cached_resolution(self) -> None:
        controller = SetupController(Path("/tmp/projectH"))

        with mock.patch(
            "pipeline_gui.setup_controller.resolve_project_active_profile",
            return_value={"support_level": "supported", "controls": {"launch_allowed": True}},
        ) as resolve_active:
            first = controller.resolve_runtime_active_profile()
            second = controller.resolve_runtime_active_profile()

        self.assertEqual(first, second)
        resolve_active.assert_called_once_with(controller.project)

    def test_runtime_and_setup_presentations_are_built_in_controller(self) -> None:
        controller = SetupController(Path("/tmp/projectH"))
        resolved = {
            "support_level": "experimental",
            "controls": {"launch_allowed": True},
            "messages": ["extra operator attention"],
        }

        launch = controller.build_runtime_launch_presentation("ready_warn", resolved)
        setup = controller.build_setup_state_presentation("ready_warn", "Gemini", resolved)

        self.assertTrue(launch.launch_allowed)
        self.assertIn("실행 프로필: 실험적", launch.text)
        self.assertIn("extra operator attention", launch.text)
        self.assertEqual(launch.color, "#fbbf24")
        self.assertIn("설정: ● 준비됨 (Gemini) / 실험적", setup.text)
        self.assertEqual(setup.color, "#f59e0b")

    def test_build_detail_snapshot_promotes_active_profile_and_last_applied(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            controller = SetupController(project)
            paths = controller.paths()
            paths["config_dir"].mkdir(parents=True, exist_ok=True)
            paths["setup_dir"].mkdir(parents=True, exist_ok=True)

            form_payload = controller.default_profile()
            draft_payload = controller.draft_payload(form_payload)
            controller.write_json(paths["draft"], draft_payload)

            setup_id = "setup-1"
            draft_fingerprint = controller.fingerprint(draft_payload)
            request_payload = {
                "setup_id": setup_id,
                "draft_fingerprint": draft_fingerprint,
            }
            preview_payload = controller.build_preview_payload(
                form_payload,
                setup_id=setup_id,
                draft_fingerprint=draft_fingerprint,
            )
            apply_payload = {
                "setup_id": setup_id,
                "approved_preview_fingerprint": preview_payload["preview_fingerprint"],
            }
            result_payload = {
                "status": "applied",
                "setup_id": setup_id,
                "finished_at": "2026-04-10T00:00:00+00:00",
                "approved_preview_fingerprint": preview_payload["preview_fingerprint"],
                "effective_executor": "Codex",
                "restart_required": True,
                "message": "설정 적용 결과가 도착했습니다.",
            }

            controller.write_json(paths["request"], request_payload)
            controller.write_json(paths["preview"], preview_payload)
            controller.write_json(paths["apply"], apply_payload)
            controller.write_json(paths["result"], result_payload)

            state = SetupActionState(current_setup_id=setup_id)
            detail = controller.build_detail_snapshot(form_payload, state)

            active_payload = read_json(paths["active"])
            last_applied_payload = read_json(paths["last_applied"])
            self.assertEqual(detail.state, "Applied")
            self.assertIsNotNone(active_payload)
            self.assertIsNotNone(last_applied_payload)
            self.assertEqual(active_payload["metadata"]["source_setup_id"], setup_id)
            self.assertEqual(last_applied_payload["setup_id"], setup_id)
            self.assertEqual(
                last_applied_payload["approved_preview_fingerprint"],
                preview_payload["preview_fingerprint"],
            )


if __name__ == "__main__":
    unittest.main()
