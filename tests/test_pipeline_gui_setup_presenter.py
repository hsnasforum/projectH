from __future__ import annotations

import unittest

from pipeline_gui.setup_models import SetupActionState
from pipeline_gui.setup_presenter import (
    build_setup_action_buttons,
    build_setup_detail_presentation,
    build_setup_fast_presentation,
    build_setup_inline_errors,
    format_setup_state_label,
    format_setup_support_label,
)


class PipelineGuiSetupPresenterTest(unittest.TestCase):
    def test_build_setup_inline_errors_maps_role_specific_messages(self) -> None:
        presentation = build_setup_inline_errors(
            [
                "최소 1개의 agent를 선택해야 합니다.",
                "구현 역할은 반드시 지정해야 합니다.",
                "현재 설정에서는 구현 역할과 검증 역할을 같은 agent에 둘 수 없습니다.",
                "현재 설정에서는 자문 역할을 구현/검증과 같은 agent에 둘 수 없습니다.",
            ]
        )

        self.assertIn("최소 1개의 agent", presentation.agent_error)
        self.assertIn("구현 역할", presentation.implement_error)
        self.assertIn("구현 역할과 검증 역할", presentation.verify_error)
        self.assertIn("자문 역할", presentation.advisory_error)

    def test_build_setup_action_buttons_stays_fail_closed_before_detail_ready(self) -> None:
        state = SetupActionState(
            mode_state="PreviewReady",
            detail_ready=False,
            current_preview_payload={"controls": {"apply_allowed": True}},
            current_support_resolution={"controls": {"preview_allowed": True}},
            dirty=False,
            draft_saved=True,
        )

        buttons = build_setup_action_buttons(
            project_valid=True,
            action_in_progress=False,
            state=state,
            preview_allowed=True,
            apply_allowed=True,
            active_matches_current=False,
        )
        self.assertFalse(buttons.apply_enabled)

        state.detail_ready = True
        buttons = build_setup_action_buttons(
            project_valid=True,
            action_in_progress=False,
            state=state,
            preview_allowed=True,
            apply_allowed=True,
            active_matches_current=False,
        )
        self.assertTrue(buttons.apply_enabled)

    def test_build_setup_fast_presentation_uses_pending_text_and_disables_apply(self) -> None:
        snapshot = {
            "state_text": "상태 확인 중...",
            "support_resolution": {"support_level": "experimental", "controls": {"preview_allowed": True}},
            "errors": ["구현 역할은 반드시 지정해야 합니다."],
            "active_matches_current": False,
            "current_setup_id_text": "setup-1",
            "current_preview_fingerprint_text": "sha256:preview-1",
        }
        state = SetupActionState(
            mode_state="PreviewWaiting",
            dirty=True,
            draft_saved=True,
        )

        presentation = build_setup_fast_presentation(
            snapshot,
            state,
            project_valid=True,
            action_in_progress=False,
            detail_pending_text="갱신 중...",
        )

        self.assertEqual(presentation.support_level_text, "실험적")
        self.assertEqual(presentation.validation_text, "갱신 중...")
        self.assertFalse(presentation.buttons.apply_enabled)
        self.assertIn("구현 역할", presentation.inline_errors.implement_error)

    def test_build_setup_detail_presentation_enables_apply_for_ready_preview(self) -> None:
        snapshot = {
            "errors": [],
            "display_support_level": "experimental",
            "validation_text": "안내: 실험적 프로필입니다",
            "preview_summary_text": "미리보기 있음",
            "restart_notice_text": "",
            "apply_readiness_text": "적용 가능",
        }
        state = SetupActionState(
            mode_state="PreviewReady",
            detail_ready=True,
            current_setup_id="setup-2",
            current_preview_fingerprint="sha256:preview-2",
            current_preview_payload={"controls": {"apply_allowed": True}},
            current_support_resolution={"controls": {"preview_allowed": True}},
            dirty=False,
            draft_saved=True,
        )

        presentation = build_setup_detail_presentation(
            snapshot,
            state,
            project_valid=True,
            action_in_progress=False,
        )

        self.assertEqual(presentation.mode_state_text, "미리보기 준비됨")
        self.assertEqual(presentation.support_level_text, "실험적")
        self.assertTrue(presentation.buttons.apply_enabled)
        self.assertEqual(presentation.current_setup_id_text, "setup-2")

    def test_format_helpers_cover_state_and_support_labels(self) -> None:
        self.assertEqual(format_setup_state_label("Applied"), "적용 완료")
        self.assertEqual(format_setup_support_label("blocked"), "차단")

