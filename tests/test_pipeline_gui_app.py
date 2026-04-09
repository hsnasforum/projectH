from __future__ import annotations

import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

from pipeline_gui.app import PipelineGUI
from pipeline_gui.setup_executor import FaultInjectingSetupExecutorAdapter, LocalSetupExecutorAdapter
from pipeline_gui.token_queries import CollectorStatus, TodayTotals, TokenDashboard
from storage.json_store_base import read_json


class _Var:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def set(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        return self.value


class _Widget:
    def __init__(self) -> None:
        self.state = None
        self._fg = None
        self._bg = None

    def configure(self, **kwargs: object) -> None:
        if "state" in kwargs:
            self.state = kwargs["state"]
        if "fg" in kwargs:
            self._fg = kwargs["fg"]
        if "bg" in kwargs:
            self._bg = kwargs["bg"]


def _make_setup_gui(project: Path, *, adapter=None) -> PipelineGUI:
    gui = PipelineGUI.__new__(PipelineGUI)
    gui.project = project
    gui._project_valid = True
    gui._action_in_progress = False
    gui._setup_form_updating = False
    gui._setup_mode_state = "DraftOnly"
    gui._setup_current_setup_id = ""
    gui._setup_current_draft_fingerprint = ""
    gui._setup_current_preview_fingerprint = ""
    gui._setup_current_preview_payload = None
    gui._setup_current_apply_payload = None
    gui._setup_current_result_payload = None
    gui._setup_draft_saved = False
    gui._setup_dirty = False
    gui._setup_has_error = False
    gui._setup_has_warning = False
    gui._setup_executor_adapter = adapter or LocalSetupExecutorAdapter(
        preview_delay_sec=0.01,
        result_delay_sec=0.01,
    )
    gui._setup_errors = []
    gui._setup_warnings = []
    gui._setup_infos = []
    gui._setup_restart_required = False
    gui._setup_agent_vars = {name: _Var(True) for name in ("Claude", "Codex", "Gemini")}
    gui._setup_implement_var = _Var("Claude")
    gui._setup_verify_var = _Var("Codex")
    gui._setup_advisory_var = _Var("Gemini")
    gui._setup_advisory_enabled_var = _Var(True)
    gui._setup_operator_stop_enabled_var = _Var(True)
    gui._setup_session_arbitration_var = _Var(True)
    gui._setup_self_verify_var = _Var(False)
    gui._setup_self_advisory_var = _Var(False)
    gui._setup_executor_var = _Var("auto")
    gui._setup_agent_error_var = _Var("")
    gui._setup_implement_error_var = _Var("")
    gui._setup_verify_error_var = _Var("")
    gui._setup_advisory_error_var = _Var("")
    gui._setup_mode_state_var = _Var("")
    gui._setup_support_level_var = _Var("")
    gui._setup_validation_var = _Var("")
    gui._setup_preview_summary_var = _Var("")
    gui._setup_current_setup_id_var = _Var("—")
    gui._setup_current_preview_fingerprint_var = _Var("—")
    gui._setup_apply_readiness_var = _Var("")
    gui._setup_restart_notice_var = _Var("")
    gui._setup_cleanup_summary_var = _Var("아직 정리 기록이 없습니다.")
    gui._setup_cleanup_history = []
    gui.btn_setup_save_draft = _Widget()
    gui.btn_setup_generate_preview = _Widget()
    gui.btn_setup_apply = _Widget()
    gui.btn_setup_clean_staged = _Widget()
    gui.btn_setup_restart_now = _Widget()
    gui._set_toast_style = mock.Mock()
    gui.msg_var = _Var("")
    gui._clear_msg_later = mock.Mock()
    gui._ask_yn = mock.Mock(return_value=True)
    gui._on_restart = mock.Mock()
    for name in (
        "_setup_paths",
        "_setup_default_profile",
        "_setup_selected_agents",
        "_setup_recommended_executor",
        "_setup_collect_form_payload",
        "_setup_draft_payload",
        "_setup_active_payload",
        "_setup_payload_for_fingerprint",
        "_setup_fingerprint",
        "_setup_preview_fingerprint",
        "_setup_support_level",
        "_setup_validate",
        "_setup_effective_executor",
        "_setup_write_json",
        "_setup_apply_inline_errors",
        "_setup_summary_text",
        "_setup_restart_required_for_payload",
        "_setup_cleanup_staged_files_once_on_startup",
        "_setup_cleanup_staged_files",
        "_setup_reset_cleanup_history",
        "_setup_record_cleanup_result",
        "_setup_build_preview_payload",
        "_setup_execute_preview_roundtrip",
        "_setup_execute_apply_roundtrip",
        "_refresh_setup_mode_state",
        "_setup_apply_readiness_text",
        "_update_setup_action_buttons",
        "_setup_promote_active_profile",
        "_setup_generate_setup_id",
        "_update_setup_widget_options",
        "_on_setup_clean_staged",
        "_on_setup_save_draft",
        "_on_setup_generate_preview",
        "_on_setup_apply",
        "_on_setup_confirm_restart",
    ):
        setattr(gui, name, getattr(PipelineGUI, name).__get__(gui, PipelineGUI))
    gui._setup_preview_matches_current = PipelineGUI._setup_preview_matches_current
    gui._setup_result_can_promote_active = PipelineGUI._setup_result_can_promote_active
    return gui


def _wait_until(predicate, *, timeout: float = 0.5) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class PipelineGuiAppTest(unittest.TestCase):
    def test_setup_preview_match_uses_draft_fingerprint(self) -> None:
        preview = {
            "setup_id": "setup-1",
            "draft_fingerprint": "sha256:draft-123",
            "preview_fingerprint": "sha256:preview-999",
        }

        self.assertTrue(
            PipelineGUI._setup_preview_matches_current(
                preview,
                "setup-1",
                "sha256:draft-123",
            )
        )
        self.assertFalse(
            PipelineGUI._setup_preview_matches_current(
                preview,
                "setup-1",
                "sha256:draft-mismatch",
            )
        )

    def test_setup_result_promotion_guard_requires_matching_setup_id_and_preview_fingerprint(self) -> None:
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
        draft = {
            "schema_version": 1,
            "selected_agents": ["Claude", "Codex", "Gemini"],
            "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
            "role_options": {"advisory_enabled": True, "operator_stop_enabled": True, "session_arbitration_enabled": True},
            "mode_flags": {"single_agent_mode": False, "self_verify_allowed": False, "self_advisory_allowed": False},
            "executor_override": "auto",
        }
        fp_fn = lambda payload: PipelineGUI._setup_fingerprint(PipelineGUI.__new__(PipelineGUI), payload)
        draft_fp = fp_fn(draft)
        preview = {
            "setup_id": "setup-1",
            "draft_fingerprint": draft_fp,
            "preview_fingerprint": "sha256:preview-123",
        }

        ok, _message = PipelineGUI._setup_result_can_promote_active(
            result,
            apply_payload,
            preview,
            "setup-1",
            draft,
            draft_fp,
            fp_fn,
        )
        self.assertTrue(ok)
        ok, _message = PipelineGUI._setup_result_can_promote_active(
            mismatch,
            apply_payload,
            preview,
            "setup-1",
            draft,
            draft_fp,
            fp_fn,
        )
        self.assertFalse(ok)
        ok, _message = PipelineGUI._setup_result_can_promote_active(
            result,
            apply_payload,
            preview,
            "setup-2",
            draft,
            draft_fp,
            fp_fn,
        )
        self.assertFalse(ok)

    def test_setup_result_promotion_guard_holds_when_draft_missing_or_mismatched(self) -> None:
        apply_payload = {
            "setup_id": "setup-1",
            "approved_preview_fingerprint": "sha256:preview-123",
        }
        result = {
            "status": "applied",
            "setup_id": "setup-1",
            "approved_preview_fingerprint": "sha256:preview-123",
        }
        draft = {
            "schema_version": 1,
            "selected_agents": ["Claude", "Codex", "Gemini"],
            "role_bindings": {"implement": "Claude", "verify": "Codex", "advisory": "Gemini"},
            "role_options": {"advisory_enabled": True, "operator_stop_enabled": True, "session_arbitration_enabled": True},
            "mode_flags": {"single_agent_mode": False, "self_verify_allowed": False, "self_advisory_allowed": False},
            "executor_override": "auto",
        }
        fp_fn = lambda payload: PipelineGUI._setup_fingerprint(PipelineGUI.__new__(PipelineGUI), payload)
        draft_fp = fp_fn(draft)
        preview = {
            "setup_id": "setup-1",
            "draft_fingerprint": draft_fp,
            "preview_fingerprint": "sha256:preview-123",
        }

        ok, message = PipelineGUI._setup_result_can_promote_active(
            result,
            apply_payload,
            preview,
            "setup-1",
            None,
            draft_fp,
            fp_fn,
        )
        self.assertFalse(ok)
        self.assertIn("draft 파일이 없어", message)

        changed = dict(draft)
        changed["executor_override"] = "Codex"
        ok, message = PipelineGUI._setup_result_can_promote_active(
            result,
            apply_payload,
            preview,
            "setup-1",
            changed,
            draft_fp,
            fp_fn,
        )
        self.assertFalse(ok)
        self.assertIn("draft 파일이 바뀌어", message)

    def test_setup_roundtrip_writes_preview_and_result_and_updates_meta_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)

            self.assertEqual(gui._setup_mode_state, "PreviewWaiting")

            paths = gui._setup_paths()
            self.assertTrue(_wait_until(lambda: read_json(paths["preview"]) is not None))
            gui._refresh_setup_mode_state()
            preview_payload = read_json(paths["preview"])
            self.assertIsNotNone(read_json(paths["request"]))
            self.assertTrue(
                PipelineGUI._setup_preview_matches_current(
                    preview_payload,
                    gui._setup_current_setup_id,
                    gui._setup_current_draft_fingerprint,
                )
            )
            self.assertEqual(gui._setup_mode_state, "PreviewReady")
            self.assertNotEqual(gui._setup_current_setup_id_var.get(), "—")
            self.assertTrue(gui._setup_current_preview_fingerprint_var.get().startswith("sha256:"))

            PipelineGUI._on_setup_apply(gui)
            self.assertEqual(gui._setup_mode_state, "ApplyPending")

            self.assertTrue(_wait_until(lambda: read_json(paths["result"]) is not None))
            gui._refresh_setup_mode_state()
            result_payload = read_json(paths["result"])
            active_payload = read_json(paths["active"])
            self.assertEqual(result_payload["status"], "applied")
            self.assertEqual(gui._setup_mode_state, "Applied")
            self.assertIsNotNone(active_payload)
            self.assertEqual(gui.btn_setup_restart_now.state, "normal")

    def test_local_setup_executor_suppresses_stale_preview_canonical_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(preview_delay_sec=0.02, result_delay_sec=0.01)

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            first_setup_id = gui._setup_current_setup_id

            gui._setup_executor_var.set("Codex")
            gui._setup_dirty = True
            gui._refresh_setup_mode_state()
            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            second_setup_id = gui._setup_current_setup_id

            self.assertNotEqual(first_setup_id, second_setup_id)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None, timeout=0.6))
            time.sleep(0.05)
            preview_payload = read_json(gui._setup_paths()["preview"])
            self.assertEqual(preview_payload["setup_id"], second_setup_id)
            self.assertIsNotNone(read_json(gui._setup_paths()["preview"].with_name(f"preview.{first_setup_id}.staged.json")))

    def test_setup_refresh_cleans_old_noncurrent_staged_files_but_keeps_current_setup_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(
                preview_delay_sec=0.20,
                result_delay_sec=0.01,
                staged_retention_sec=0.01,
            )

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            current_setup_id = gui._setup_current_setup_id
            paths = gui._setup_paths()
            keep_path = paths["preview"].with_name(f"preview.{current_setup_id}.staged.json")
            stale_path = paths["result"].with_name("result.setup-stale.staged.json")
            gui._setup_write_json(keep_path, {"setup_id": current_setup_id})
            gui._setup_write_json(stale_path, {"setup_id": "setup-stale"})

            time.sleep(0.02)
            gui._refresh_setup_mode_state()

            self.assertTrue(keep_path.exists())
            self.assertFalse(stale_path.exists())
            self.assertEqual(gui._setup_cleanup_summary_var.get(), "자동 정리: 오래된 staged 파일 1개 정리")

    def test_setup_startup_cleanup_uses_disk_request_apply_context_to_protect_current_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(
                preview_delay_sec=0.01,
                result_delay_sec=0.01,
                staged_retention_sec=0.01,
            )
            paths = gui._setup_paths()
            gui._setup_write_json(paths["request"], {"setup_id": "setup-current"})
            gui._setup_write_json(paths["apply"], {"setup_id": "setup-apply"})
            keep_request = paths["preview"].with_name("preview.setup-current.staged.json")
            keep_apply = paths["result"].with_name("result.setup-apply.staged.json")
            stale_path = paths["preview"].with_name("preview.setup-old.staged.json")
            gui._setup_write_json(keep_request, {"setup_id": "setup-current"})
            gui._setup_write_json(keep_apply, {"setup_id": "setup-apply"})
            gui._setup_write_json(stale_path, {"setup_id": "setup-old"})

            time.sleep(0.02)
            PipelineGUI._setup_cleanup_staged_files_once_on_startup(gui)

            self.assertTrue(keep_request.exists())
            self.assertTrue(keep_apply.exists())
            self.assertFalse(stale_path.exists())
            self.assertEqual(gui._setup_cleanup_summary_var.get(), "초기 정리: 오래된 staged 파일 1개 정리")

    def test_setup_manual_clean_removes_old_staged_files_and_toasts_count(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(
                preview_delay_sec=0.01,
                result_delay_sec=0.01,
                staged_retention_sec=0.01,
            )
            paths = gui._setup_paths()
            stale_path = paths["preview"].with_name("preview.setup-old.staged.json")
            gui._setup_write_json(stale_path, {"setup_id": "setup-old"})
            time.sleep(0.02)

            PipelineGUI._on_setup_clean_staged(gui)

            self.assertFalse(stale_path.exists())
            self.assertEqual(gui.msg_var.get(), "오래된 staged 파일 1개를 정리했습니다")
            self.assertEqual(gui._setup_cleanup_summary_var.get(), "수동 정리: 오래된 staged 파일 1개 정리")

            PipelineGUI._on_setup_clean_staged(gui)

            self.assertEqual(
                gui._setup_cleanup_summary_var.get(),
                "수동 정리: 정리할 오래된 staged 파일이 없습니다\n수동 정리: 오래된 staged 파일 1개 정리",
            )

    def test_setup_manual_clean_keeps_inflight_setup_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))
            gui._setup_executor_adapter = LocalSetupExecutorAdapter(
                preview_delay_sec=0.01,
                result_delay_sec=0.01,
                staged_retention_sec=0.01,
            )
            gui._setup_mode_state = "PreviewWaiting"
            gui._setup_current_setup_id = "setup-current"
            paths = gui._setup_paths()
            keep_path = paths["preview"].with_name("preview.setup-current.staged.json")
            stale_path = paths["preview"].with_name("preview.setup-old.staged.json")
            gui._setup_write_json(paths["request"], {"setup_id": "setup-current"})
            gui._setup_write_json(keep_path, {"setup_id": "setup-current"})
            gui._setup_write_json(stale_path, {"setup_id": "setup-old"})
            time.sleep(0.02)

            PipelineGUI._on_setup_clean_staged(gui)

            self.assertTrue(keep_path.exists())
            self.assertFalse(stale_path.exists())

    def test_stale_preview_overwrite_never_downgrades_current_preview_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()

            current_setup_id = gui._setup_current_setup_id
            current_preview_fingerprint = gui._setup_current_preview_fingerprint
            gui._setup_write_json(
                gui._setup_paths()["preview"],
                {
                    "status": "preview_ready",
                    "setup_id": "setup-stale",
                    "draft_fingerprint": "sha256:stale",
                    "preview_fingerprint": "sha256:stale-preview",
                },
            )
            gui._refresh_setup_mode_state()

            self.assertEqual(gui._setup_mode_state, "PreviewReady")
            self.assertEqual(gui._setup_current_setup_id, current_setup_id)
            self.assertEqual(gui._setup_current_preview_fingerprint, current_preview_fingerprint)

    def test_stale_result_overwrite_never_downgrades_applied_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()
            PipelineGUI._on_setup_apply(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["result"]) is not None))
            gui._refresh_setup_mode_state()

            current_setup_id = gui._setup_current_setup_id
            current_preview_fingerprint = gui._setup_current_preview_fingerprint
            self.assertEqual(gui._setup_mode_state, "Applied")

            gui._setup_write_json(
                gui._setup_paths()["result"],
                {
                    "status": "apply_failed",
                    "setup_id": "setup-stale",
                    "approved_preview_fingerprint": "sha256:stale",
                    "message": "stale result should not win",
                },
            )
            gui._refresh_setup_mode_state()

            self.assertEqual(gui._setup_mode_state, "Applied")
            self.assertEqual(gui._setup_current_setup_id, current_setup_id)
            self.assertEqual(gui._setup_current_preview_fingerprint, current_preview_fingerprint)

    def test_setup_apply_holds_active_promotion_when_draft_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()
            gui._setup_paths()["draft"].unlink()

            PipelineGUI._on_setup_apply(gui)
            self.assertEqual(gui._setup_mode_state, "ApplyPending")
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["result"]) is not None))
            gui._refresh_setup_mode_state()

            self.assertEqual(gui._setup_mode_state, "ApplyFailed")
            self.assertIn("draft 파일이 없어", gui._setup_validation_var.get())
            self.assertIsNone(read_json(gui._setup_paths()["active"]))

    def test_setup_apply_failed_result_surfaces_errors_warnings_and_message_first(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gui = _make_setup_gui(Path(td))

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()

            apply_payload = {
                "status": "apply_requested",
                "setup_id": gui._setup_current_setup_id,
                "schema_version": 1,
                "approved_at": "2026-04-08T00:00:00Z",
                "approved_preview_fingerprint": gui._setup_current_preview_fingerprint,
                "executor": "Codex",
            }
            gui._setup_write_json(gui._setup_paths()["apply"], apply_payload)
            gui._setup_write_json(
                gui._setup_paths()["result"],
                {
                    "status": "apply_failed",
                    "setup_id": gui._setup_current_setup_id,
                    "approved_preview_fingerprint": gui._setup_current_preview_fingerprint,
                    "errors": ["preview materialization failed"],
                    "warnings": ["manual review recommended"],
                    "message": "executor apply failed",
                },
            )
            gui._refresh_setup_mode_state()

            lines = gui._setup_validation_var.get().splitlines()
            self.assertGreaterEqual(len(lines), 3)
            self.assertEqual(lines[0], "오류: preview materialization failed")
            self.assertEqual(lines[1], "오류: executor apply failed")
            self.assertEqual(lines[2], "경고: manual review recommended")

    def test_fault_injecting_setup_executor_exercises_apply_failed_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            adapter = FaultInjectingSetupExecutorAdapter(
                preview_delay_sec=0.01,
                result_delay_sec=0.01,
                result_patch={
                    "status": "apply_failed",
                    "errors": ["simulated apply failure"],
                    "warnings": ["operator review recommended"],
                    "message": "fault injection apply failed",
                },
            )
            gui = _make_setup_gui(Path(td), adapter=adapter)

            PipelineGUI._on_setup_save_draft(gui)
            PipelineGUI._on_setup_generate_preview(gui)
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["preview"]) is not None))
            gui._refresh_setup_mode_state()

            PipelineGUI._on_setup_apply(gui)
            self.assertEqual(gui._setup_mode_state, "ApplyPending")
            self.assertTrue(_wait_until(lambda: read_json(gui._setup_paths()["result"]) is not None))
            gui._refresh_setup_mode_state()

            self.assertEqual(gui._setup_mode_state, "ApplyFailed")
            lines = gui._setup_validation_var.get().splitlines()
            self.assertGreaterEqual(len(lines), 3)
            self.assertEqual(lines[0], "오류: simulated apply failure")
            self.assertEqual(lines[1], "오류: fault injection apply failed")
            self.assertEqual(lines[2], "경고: operator review recommended")

    def test_setup_restart_confirmation_calls_restart_only_when_accepted(self) -> None:
        gui = _make_setup_gui(Path("/tmp/projecth-setup-test"))
        gui._setup_mode_state = "Applied"
        gui._setup_restart_required = True
        gui._ask_yn.return_value = False

        PipelineGUI._on_setup_confirm_restart(gui)
        gui._on_restart.assert_not_called()

        gui._ask_yn.return_value = True
        PipelineGUI._on_setup_confirm_restart(gui)
        gui._on_restart.assert_called_once_with()

    def test_ask_yn_calls_messagebox_directly_on_main_thread(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.root = mock.Mock()
        with mock.patch("pipeline_gui.app.messagebox.askyesno", return_value=True) as ask_mock:
            result = PipelineGUI._ask_yn(gui, "Title", "Body", icon="question")
        self.assertTrue(result)
        ask_mock.assert_called_once_with("Title", "Body", icon="question")
        gui.root.after.assert_not_called()

    def test_apply_token_dashboard_shows_loading_during_token_action_without_db(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.selected_agent = "Claude"
        gui._action_in_progress = True
        gui._token_action_var = _Var("작업: 전체 히스토리 · 0% · 준비 중 · 0.0초 · 스캔 0/0")
        gui._token_status_var = _Var()
        gui._token_totals_var = _Var()
        gui._token_agents_var = _Var()
        gui._token_selected_var = _Var()
        gui._token_jobs_var = _Var()
        gui._last_snapshot = {"token_usage": {}}
        gui._fmt_count = PipelineGUI._fmt_count.__get__(gui, PipelineGUI)

        dashboard = TokenDashboard(
            display_day="",
            collector_status=CollectorStatus(),
            today_totals=TodayTotals(),
            agent_totals=[],
            top_jobs=[],
        )

        PipelineGUI._apply_token_dashboard(gui, dashboard)

        self.assertEqual(gui._token_status_var.get(), "수집기: 불러오는 중...")
        self.assertEqual(gui._token_totals_var.get(), "오늘: 불러오는 중...")
        self.assertEqual(gui._token_agents_var.get(), "에이전트: 불러오는 중...")
        self.assertEqual(gui._token_selected_var.get(), "선택 에이전트 CLAUDE: 불러오는 중...")
        self.assertEqual(gui._token_jobs_var.get(), "주요 작업: 불러오는 중...")

    def test_apply_token_dashboard_shows_selected_agent_detail(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.selected_agent = "Codex"
        gui._action_in_progress = False
        gui._token_action_var = _Var("작업: —")
        gui._token_status_var = _Var()
        gui._token_totals_var = _Var()
        gui._token_agents_var = _Var()
        gui._token_selected_var = _Var()
        gui._token_jobs_var = _Var()
        gui._last_snapshot = {
            "token_usage": {
                "Codex": {
                    "available": True,
                    "used_percent": 14.2,
                    "session_tokens": 42100,
                    "today_tokens": 108200,
                    "reset_at": "03:00",
                }
            }
        }
        gui._fmt_count = PipelineGUI._fmt_count.__get__(gui, PipelineGUI)

        agent_row = type(
            "AgentRow",
            (),
            {
                "source": "codex",
                "events": 12,
                "linked_events": 4,
                "input_tokens": 1200,
                "output_tokens": 340,
                "total_cost_usd": 0.0,
            },
        )()
        dashboard = TokenDashboard(
            display_day="2026-04-05",
            collector_status=CollectorStatus(available=True, phase="idle"),
            today_totals=TodayTotals(input_tokens=1200, output_tokens=340),
            agent_totals=[agent_row],
            top_jobs=[],
        )

        PipelineGUI._apply_token_dashboard(gui, dashboard)

        self.assertIn("선택 에이전트 CODEX:", gui._token_selected_var.get())
        self.assertIn("usage 14% 사용", gui._token_selected_var.get())
        self.assertIn("최근 2026-04-05 1.2k/340", gui._token_selected_var.get())
        self.assertIn("연결 4/12", gui._token_selected_var.get())

    def test_start_token_maintenance_action_uses_shared_setup_flow(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._action_in_progress = False
        gui._ask_yn = mock.Mock(return_value=True)
        gui._lock_buttons = mock.Mock()
        gui._update_token_action_progress = mock.Mock()
        gui._start_token_ui_pump = mock.Mock()
        gui._token_action_initial_payload = mock.Mock(return_value={"phase": "preparing"})
        worker = mock.Mock()

        with mock.patch("pipeline_gui.app.threading.Thread") as thread_cls:
            thread = thread_cls.return_value
            PipelineGUI._start_token_maintenance_action(
                gui,
                action_label="전체 히스토리",
                dialog_title="Title",
                dialog_message="Body",
                icon="question",
                lock_message="LOCK",
                worker_target=worker,
            )

        gui._ask_yn.assert_called_once_with("Title", "Body", icon="question")
        gui._lock_buttons.assert_called_once_with("LOCK")
        gui._update_token_action_progress.assert_called_once_with("전체 히스토리", {"phase": "preparing"})
        gui._start_token_ui_pump.assert_called_once_with()
        thread_cls.assert_called_once_with(target=worker, daemon=True)
        thread.start.assert_called_once_with()

    def test_run_token_maintenance_action_enqueues_shared_success_flow(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        queued: list[object] = []
        gui._enqueue_token_ui = lambda callback: queued.append(callback)
        gui._format_token_action_done = mock.Mock(return_value="작업: 완료")
        gui._set_token_action_text = mock.Mock()
        gui._refresh_token_dashboard_async = mock.Mock()
        gui._start_token_usage_refresh = mock.Mock()
        gui._unlock_buttons = mock.Mock()
        gui._clear_msg_later = mock.Mock()

        PipelineGUI._run_token_maintenance_action(
            gui,
            action_label="DB 재구성",
            action_runner=lambda: {
                "summary": {"elapsed_sec": 3.2, "usage_inserted": 12},
                "backup_path": "/tmp/usage.backup-1.db",
            },
            unlock_message_builder=lambda summary, backup_path: (
                f"done {summary['elapsed_sec']:.1f} {backup_path}"
            ),
            error_message="should not be used",
        )

        for callback in queued:
            callback()

        gui._format_token_action_done.assert_called_once()
        gui._set_token_action_text.assert_called_once_with("작업: 완료")
        gui._refresh_token_dashboard_async.assert_called_once_with()
        gui._start_token_usage_refresh.assert_called_once_with(force=True)
        gui._unlock_buttons.assert_called_once_with("done 3.2 /tmp/usage.backup-1.db")
        gui._clear_msg_later.assert_called_once_with(10000)

    def test_format_token_job_segment_shortens_link_method(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        job = type(
            "JobRow",
            (),
            {
                "job_id": "20260406-verify-long-job-name",
                "total_cost_usd": 1.25,
                "primary_link_method": "dispatch_slot_verify_window",
                "max_confidence": 0.9,
                "low_confidence_events": 0,
                "events": 3,
            },
        )()

        text = PipelineGUI._format_token_job_segment(gui, job)

        self.assertIn("verify-long-job-name", text)
        self.assertIn("$1.25", text)
        self.assertIn("dispatch", text)
        self.assertIn("c=0.90", text)
        self.assertIn("low=0/3", text)

    def test_set_main_button_states_handles_disabled_and_ready_modes(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui.btn_setup = _Widget()
        gui.btn_start = _Widget()
        gui.btn_stop = _Widget()
        gui.btn_restart = _Widget()
        gui.btn_attach = _Widget()
        gui.btn_token_backfill = _Widget()
        gui.btn_token_rebuild = _Widget()

        PipelineGUI._set_main_button_states(gui, all_disabled=True)
        self.assertEqual(gui.btn_setup.state, "disabled")
        self.assertEqual(gui.btn_start.state, "disabled")
        self.assertEqual(gui.btn_token_rebuild.state, "disabled")

        PipelineGUI._set_main_button_states(gui, all_disabled=False, can_start=True, session_ok=True)
        self.assertEqual(gui.btn_setup.state, "normal")
        self.assertEqual(gui.btn_start.state, "normal")
        self.assertEqual(gui.btn_stop.state, "normal")
        self.assertEqual(gui.btn_restart.state, "normal")
        self.assertEqual(gui.btn_attach.state, "normal")
        self.assertEqual(gui.btn_token_backfill.state, "normal")
        self.assertEqual(gui.btn_token_rebuild.state, "normal")

    def test_poll_status_text_marks_live_snapshot_fresh_and_stale(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._last_poll_at = 100.0

        text, color = PipelineGUI._poll_status_text(gui, is_live=True, now=101.0)
        self.assertEqual(text, "폴링: 최신 1초")
        self.assertEqual(color, "#34d399")

        text, color = PipelineGUI._poll_status_text(gui, is_live=True, now=105.0)
        self.assertEqual(text, "폴링: 지연 5초")
        self.assertEqual(color, "#e0a040")

    def test_poll_status_text_marks_last_run_when_not_live(self) -> None:
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._last_poll_at = 100.0

        text, color = PipelineGUI._poll_status_text(gui, is_live=False, now=104.0)
        self.assertEqual(text, "폴링: 마지막 실행 4초 전")
        self.assertEqual(color, "#666666")

    def test_apply_snapshot_control_slot_normal_active(self) -> None:
        """_apply_snapshot sets control vars and blue color for normal active slot."""
        gui = self._make_snapshot_gui()
        snapshot = self._base_snapshot()
        snapshot["control_slots"] = {
            "active": {"file": "claude_handoff.md", "status": "implement", "label": "Claude 실행", "mtime": 1.0},
            "stale": [{"file": "operator_request.md", "status": "needs_operator", "label": "operator 대기", "mtime": 0.5}],
        }
        PipelineGUI._apply_snapshot(gui, snapshot)
        self.assertIn("Claude 실행", gui.active_control_var.get())
        self.assertIn("operator_request.md", gui.stale_control_var.get())
        self.assertIn("비활성", gui.stale_control_var.get())
        self.assertEqual(gui.active_control_label._fg, "#60a5fa")

    def test_apply_snapshot_control_slot_needs_operator_red(self) -> None:
        """_apply_snapshot uses red color when active control is needs_operator."""
        gui = self._make_snapshot_gui()
        snapshot = self._base_snapshot()
        snapshot["control_slots"] = {
            "active": {"file": "operator_request.md", "status": "needs_operator", "label": "operator 대기", "mtime": 1.0},
            "stale": [],
        }
        PipelineGUI._apply_snapshot(gui, snapshot)
        self.assertIn("operator 대기", gui.active_control_var.get())
        self.assertEqual(gui.active_control_label._fg, "#f87171")

    def test_apply_snapshot_control_slot_no_active_gray(self) -> None:
        """_apply_snapshot uses gray color when no active control slot."""
        gui = self._make_snapshot_gui()
        snapshot = self._base_snapshot()
        snapshot["control_slots"] = {"active": None, "stale": []}
        PipelineGUI._apply_snapshot(gui, snapshot)
        self.assertEqual(gui.active_control_var.get(), "활성 제어: 없음")
        self.assertEqual(gui.stale_control_var.get(), "")
        self.assertEqual(gui.active_control_label._fg, "#6b7280")

    @staticmethod
    def _make_snapshot_gui():
        """Build a minimal PipelineGUI stub sufficient for _apply_snapshot."""
        gui = PipelineGUI.__new__(PipelineGUI)
        gui._last_snapshot = {}
        gui._last_poll_at = 0.0
        gui.selected_agent = "Claude"
        gui._auto_focus_agent = False
        gui._working_since = {}
        gui._action_in_progress = False
        gui._setup_state = "ready"
        # System card vars
        gui.pipeline_var = _Var()
        gui.status_var = _Var()
        gui.status_label = _Widget()
        gui.pipeline_state_label = _Widget()
        gui.watcher_var = _Var()
        gui.watcher_state_label = _Widget()
        gui.poll_var = _Var()
        gui.poll_state_label = _Widget()
        gui.active_control_var = _Var()
        gui.active_control_label = _Widget()
        gui.stale_control_var = _Var()
        gui.stale_control_label = _Widget()
        # Artifact vars
        gui.work_var = _Var()
        gui._work_label = _Widget()
        gui.verify_var = _Var()
        gui._verify_label = _Widget()
        gui._run_context_var = _Var()
        gui._run_context_label = _Widget()
        gui._artifacts_title_var = _Var()
        # Focus / log
        gui.focus_title_var = _Var()
        gui.focus_text = type("FakeText", (), {
            "get": lambda self, *a: "",
            "configure": lambda self, **kw: None,
            "delete": lambda self, *a: None,
            "insert": lambda self, *a: None,
            "see": lambda self, *a: None,
        })()
        gui._log_title_var = _Var()
        gui.log_text = type("FakeText", (), {
            "get": lambda self, *a: "",
            "configure": lambda self, **kw: None,
            "delete": lambda self, *a: None,
            "insert": lambda self, *a: None,
            "see": lambda self, *a: None,
        })()
        gui.agent_labels = []
        # Token vars
        gui._token_status_var = _Var()
        gui._token_totals_var = _Var()
        gui._token_agents_var = _Var()
        gui._token_selected_var = _Var()
        gui._token_jobs_var = _Var()
        gui._token_action_var = _Var()
        gui._fmt_count = PipelineGUI._fmt_count.__get__(gui, PipelineGUI)
        # Stubs for methods called during _apply_snapshot
        gui._update_poll_freshness = lambda: None
        gui._apply_token_dashboard = lambda dashboard: None
        gui._update_text_if_changed = lambda widget, text: None
        gui._set_main_button_states = lambda **kw: None
        return gui

    @staticmethod
    def _base_snapshot():
        """Return a minimal valid snapshot dict."""
        return {
            "session_ok": False,
            "watcher_alive": False,
            "watcher_pid": None,
            "agents": [],
            "pane_map": {},
            "token_usage": {},
            "token_dashboard": None,
            "work_name": "—",
            "work_mtime": 0.0,
            "verify_name": "—",
            "verify_mtime": 0.0,
            "log_lines": [],
            "run_summary": {},
            "control_slots": {"active": None, "stale": []},
            "polled_at": time.time(),
        }


if __name__ == "__main__":
    unittest.main()
